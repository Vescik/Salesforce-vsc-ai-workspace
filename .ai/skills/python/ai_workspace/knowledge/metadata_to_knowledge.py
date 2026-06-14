"""Emit knowledge cards derived from local Salesforce metadata under ``force-app/``.

For Phase 1 of Knowledge 2.0 we emit **one card per metadata component** (Apex
class, Apex trigger, Flow, custom object) using the existing parsers in
``ai_workspace.parsers``. Per-method / per-Flow-node breakdown is deferred to a
follow-up once consumers exist (graph builder, AC coverage check).

Output is local-only and never synced upstream::

    .ai/context/index/metadata-knowledge-cards.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_workspace.parsers.parse_apex import parse_apex_file
from ai_workspace.parsers.parse_flow import parse_flow_file
from ai_workspace.utils.io import ensure_parent_dir, read_utf8, write_jsonl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit knowledge cards derived from Salesforce metadata.")
    parser.add_argument("--force-app-root", default="force-app")
    parser.add_argument("--out", default=".ai/context/index/metadata-knowledge-cards.jsonl")
    parser.add_argument("--summary-out", default=".ai/context/index/metadata-knowledge-summary.json")
    args = parser.parse_args(argv)

    root = Path(args.force_app_root)
    out_path = Path(args.out)
    summary_path = Path(args.summary_out)

    records: list[dict[str, Any]] = []
    if root.exists():
        records.extend(_apex_cards(root))
        records.extend(_flow_cards(root))
        records.extend(_object_cards(root))

    records.sort(key=lambda card: (card.get("metadata_type", ""), card.get("api_name", ""), card.get("path", "")))
    write_jsonl(out_path, records)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "force_app_root": root.as_posix(),
        "out": out_path.as_posix(),
        "card_count": len(records),
        "by_type": _count(records, "metadata_type"),
    }
    ensure_parent_dir(summary_path)
    summary_path.write_text(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Wrote {len(records)} metadata-knowledge card(s) to {out_path}")
    print(f"Wrote summary to {summary_path}")
    return 0


def _apex_cards(root: Path) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for path in sorted(list(root.rglob("*.cls")) + list(root.rglob("*.trigger"))):
        parsed = parse_apex_file(path)
        details = parsed.get("details") or {}
        kind = str(details.get("kind") or "apex")
        cards.append(_make_card(
            metadata_type=f"apex_{kind}",
            api_name=str(parsed.get("full_name") or path.stem),
            path=path,
            summary=str(parsed.get("summary") or ""),
            references=parsed.get("references") or {},
            risk_flags=parsed.get("risk_flags") or [],
            parse_status=str(parsed.get("parse_status") or "ok"),
            extra={
                "sharing": details.get("sharing"),
                "trigger_object": details.get("trigger_object"),
            },
        ))
    return cards


def _flow_cards(root: Path) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.flow-meta.xml")):
        parsed = parse_flow_file(path)
        details = parsed.get("details") or {}
        cards.append(_make_card(
            metadata_type="flow",
            api_name=str(parsed.get("full_name") or path.stem),
            path=path,
            summary=str(parsed.get("summary") or ""),
            references=parsed.get("references") or {},
            risk_flags=parsed.get("risk_flags") or [],
            parse_status=str(parsed.get("parse_status") or "ok"),
            extra={
                "process_type": details.get("process_type"),
                "start_object": details.get("start_object"),
                "record_operations": len(details.get("record_operations") or []),
            },
        ))
    return cards


def _object_cards(root: Path) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for object_xml in sorted(root.rglob("*.object-meta.xml")):
        object_name = object_xml.name.removesuffix(".object-meta.xml")
        object_dir = object_xml.parent
        fields = sorted((object_dir / "fields").glob("*.field-meta.xml")) if (object_dir / "fields").exists() else []
        validation_rules = sorted((object_dir / "validationRules").glob("*.validationRule-meta.xml")) if (object_dir / "validationRules").exists() else []
        formula_fields, total_fields = _scan_fields(fields)
        rule_summaries = _scan_validation_rules(validation_rules)
        cards.append(_make_card(
            metadata_type="custom_object",
            api_name=object_name,
            path=object_xml,
            summary=(f"Custom object {object_name}: {total_fields} field(s), "
                     f"{len(formula_fields)} formula(s), {len(rule_summaries)} validation rule(s)."),
            references={"objects": [object_name], "fields": [f"{object_name}.{name}" for name in formula_fields]},
            risk_flags=[],
            parse_status="ok",
            extra={
                "field_count": total_fields,
                "formula_fields": formula_fields,
                "validation_rules": rule_summaries,
            },
        ))
    return cards


def _scan_fields(field_paths: list[Path]) -> tuple[list[str], int]:
    formula: list[str] = []
    for field_xml in field_paths:
        try:
            text, _ = read_utf8(field_xml)
            root = ET.fromstring(text)
        except (OSError, ET.ParseError):
            continue
        full_name = _first_text(root, "fullName") or field_xml.stem
        if _first_text(root, "formula"):
            formula.append(full_name)
    return sorted(formula), len(field_paths)


def _scan_validation_rules(rule_paths: list[Path]) -> list[dict[str, str]]:
    rules: list[dict[str, str]] = []
    for rule_xml in rule_paths:
        try:
            text, _ = read_utf8(rule_xml)
            root = ET.fromstring(text)
        except (OSError, ET.ParseError):
            continue
        rules.append({
            "full_name": _first_text(root, "fullName") or rule_xml.stem,
            "active": _first_text(root, "active") or "",
            "error_message": _clip(_first_text(root, "errorMessage") or "", 200),
        })
    return rules


def _first_text(root: ET.Element, tag: str) -> str:
    for element in root.iter():
        local = element.tag.rsplit("}", 1)[-1]
        if local == tag and element.text:
            return element.text.strip()
    return ""


def _clip(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[:limit] + "..."


def _make_card(
    *,
    metadata_type: str,
    api_name: str,
    path: Path,
    summary: str,
    references: dict[str, Any],
    risk_flags: list[str],
    parse_status: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "card_type": "metadata_component",
        "metadata_type": metadata_type,
        "api_name": api_name,
        "path": _display_path(path),
        "summary": summary,
        "references": _normalize_references(references),
        "risk_flags": list(risk_flags or []),
        "parse_status": parse_status,
        "details": {k: v for k, v in (extra or {}).items() if v not in (None, "", [], {})},
    }


def _normalize_references(references: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for key, value in references.items():
        if isinstance(value, list):
            result[key] = sorted({str(item) for item in value if str(item).strip()})
    return result


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except (FileNotFoundError, ValueError):
        return path.as_posix()


def _count(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = str(record.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


if __name__ == "__main__":
    raise SystemExit(main())
