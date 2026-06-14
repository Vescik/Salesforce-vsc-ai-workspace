"""Lint a proposed solution design for Knowledge 2.0 compliance.

Checks (each emits findings with severity blocking/high/medium/low):
- Every AC has a row in the design's Coverage Table.
- Every ``related_object`` of a cited knowledge card is mentioned in the design body.
- Every cited ``status: draft`` or ``confidence: low`` knowledge card is wrapped
  in ``[unverified]`` in the design body.
- Every metadata component named in the "Impacted metadata" section resolves
  against ``metadata-components.jsonl`` (when present).

Exit code 1 when blocking findings exist.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_workspace.deployment.ac_coverage_check import (
    _extract_coverage_table,
    _extract_knowledge_references,
    _extract_metadata_components,
    _normalize_ac_id,
    _read_acceptance_criteria,
)
from ai_workspace.knowledge.index_knowledge import _parse_front_matter


SEVERITIES = ("blocking", "high", "medium", "low")
SEVERITY_RANK = {sev: rank for rank, sev in enumerate(SEVERITIES)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint a proposed/approved solution design.")
    parser.add_argument("--work-item", required=True)
    parser.add_argument("--work-item-dir")
    parser.add_argument("--design")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--metadata-index", default=".ai/context/index/metadata-components.jsonl")
    parser.add_argument("--out", default=".ai/outputs/precheck/{work_item}.design-lint.md")
    parser.add_argument("--out-json", default=".ai/outputs/precheck/{work_item}.design-lint.json")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    work_item_dir = Path(args.work_item_dir or f".ai/context/work-items/{args.work_item}")
    design_path = _resolve_design(args.design, args.work_item, repo_root)
    if design_path is None or not design_path.exists():
        return _write_outputs(
            args,
            [{"severity": "blocking", "type": "design_missing", "path": "", "message": f"No proposed/approved design found for {args.work_item}."}],
            design_path,
        )

    design_text = design_path.read_text(encoding="utf-8", errors="replace")
    ac_rows = _read_acceptance_criteria(work_item_dir)
    coverage_table = _extract_coverage_table(design_text)
    knowledge_refs = _extract_knowledge_references(design_text)
    impacted_metadata = _extract_metadata_components(design_text)

    findings: list[dict[str, Any]] = []
    findings.extend(_findings_ac_in_coverage(ac_rows, coverage_table, design_path))
    findings.extend(_findings_related_objects(knowledge_refs, design_text, design_path, repo_root))
    findings.extend(_findings_unverified_wrap(knowledge_refs, design_text, design_path, repo_root))
    findings.extend(_findings_metadata_resolves(impacted_metadata, Path(args.metadata_index), design_path))

    return _write_outputs(args, findings, design_path)


def _resolve_design(explicit: str | None, work_item: str, repo_root: Path) -> Path | None:
    if explicit:
        return Path(explicit)
    for candidate in (
        repo_root / "specs" / "approved" / f"{work_item}.solution-design.md",
        repo_root / "specs" / "proposed" / f"{work_item}.solution-design.md",
    ):
        if candidate.exists():
            return candidate
    return None


def _findings_ac_in_coverage(
    ac_rows: list[tuple[str, str]],
    coverage_table: dict[str, dict[str, list[str]]],
    design_path: Path,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for ac_id, _ac_text in ac_rows:
        key = _normalize_ac_id(ac_id).upper().replace(" ", "")
        if key not in coverage_table:
            findings.append({
                "severity": "blocking",
                "type": "ac_missing_from_coverage_table",
                "path": _display(design_path),
                "ac_id": ac_id,
                "message": f"{ac_id} is not present in the design's Coverage Table or Acceptance Criteria Mapping.",
            })
    return findings


def _findings_related_objects(
    knowledge_refs: list[dict[str, str]],
    design_text: str,
    design_path: Path,
    repo_root: Path,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    body_lower = design_text.lower()
    for ref in knowledge_refs:
        note_path = (repo_root / ref.get("path", "")).resolve() if ref.get("path") else None
        if note_path is None or not note_path.exists():
            continue
        try:
            note_text = note_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        metadata, _, _ = _parse_front_matter(note_text)
        related_objects = metadata.get("related_objects") if isinstance(metadata.get("related_objects"), list) else []
        for obj in related_objects:
            obj_str = str(obj).strip()
            if not obj_str:
                continue
            if obj_str.lower() not in body_lower:
                findings.append({
                    "severity": "high",
                    "type": "related_object_not_mentioned",
                    "path": _display(design_path),
                    "knowledge": ref.get("path"),
                    "related_object": obj_str,
                    "message": (
                        f"Cited knowledge `{ref.get('path')}` lists related_object `{obj_str}`, "
                        "but the design body does not mention it."
                    ),
                })
    return findings


def _findings_unverified_wrap(
    knowledge_refs: list[dict[str, str]],
    design_text: str,
    design_path: Path,
    repo_root: Path,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for ref in knowledge_refs:
        note_path_str = ref.get("path", "")
        note_path = (repo_root / note_path_str).resolve() if note_path_str else None
        if note_path is None or not note_path.exists():
            continue
        try:
            note_text = note_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        metadata, _, _ = _parse_front_matter(note_text)
        status = str(metadata.get("status") or "").lower()
        confidence = str(metadata.get("confidence") or "").lower()
        if status not in {"draft"} and confidence not in {"low"}:
            continue
        # Look for `[label](path)` and check the next 20 characters for [unverified].
        for match in re.finditer(rf"\[([^\]]+)\]\({re.escape(note_path_str)}\)", design_text):
            tail = design_text[match.end():match.end() + 40]
            head = design_text[max(0, match.start() - 20):match.start()]
            if "[unverified]" in tail.lower() or "[unverified]" in head.lower():
                continue
            reasons = []
            if status == "draft":
                reasons.append("status=draft")
            if confidence == "low":
                reasons.append("confidence=low")
            findings.append({
                "severity": "high",
                "type": "draft_low_confidence_unwrapped",
                "path": _display(design_path),
                "knowledge": note_path_str,
                "reasons": reasons,
                "message": (
                    f"Cited knowledge `{note_path_str}` is {'/'.join(reasons)}; "
                    "wrap the citation with `[unverified]` in the design body."
                ),
            })
    return findings


def _findings_metadata_resolves(
    impacted_metadata: set[str],
    metadata_index_path: Path,
    design_path: Path,
) -> list[dict[str, Any]]:
    if not impacted_metadata:
        return []
    if not metadata_index_path.exists():
        # No index built yet — defer to a soft finding so the lint stays useful.
        return [{
            "severity": "low",
            "type": "metadata_index_missing",
            "path": _display(design_path),
            "message": f"Cannot resolve impacted metadata: {metadata_index_path.as_posix()} not found.",
        }]
    known: set[str] = set()
    for line in metadata_index_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        for key in ("full_name", "api_name", "name"):
            value = record.get(key)
            if isinstance(value, str) and value.strip():
                known.add(value.strip())
                break
    findings: list[dict[str, Any]] = []
    for component in sorted(impacted_metadata):
        # Strip object qualifier (kmbi__Invoice__c.kmbi__Foo__c → kmbi__Foo__c)
        candidate = component.split(".")[-1]
        if component not in known and candidate not in known:
            findings.append({
                "severity": "medium",
                "type": "metadata_component_unresolved",
                "path": _display(design_path),
                "component": component,
                "message": (
                    f"Impacted metadata component `{component}` does not resolve to a row in "
                    f"{metadata_index_path.as_posix()}. Confirm the API name or run `make ai-index-repo`."
                ),
            })
    return findings


def _write_outputs(args: argparse.Namespace, findings: list[dict[str, Any]], design_path: Path | None) -> int:
    md_path = Path(args.out.format(work_item=args.work_item))
    json_path = Path(args.out_json.format(work_item=args.work_item))
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {sev: 0 for sev in SEVERITIES}
    for finding in findings:
        severity = str(finding.get("severity") or "low")
        if severity in summary:
            summary[severity] += 1
    payload = {
        "work_item": args.work_item,
        "design_path": design_path.as_posix() if design_path else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "findings": sorted(findings, key=lambda f: (SEVERITY_RANK.get(f.get("severity") or "low", 99), f.get("type") or "")),
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_render_md(payload), encoding="utf-8")
    print(f"Wrote {md_path}")
    print(f"Wrote {json_path}")
    print(f"Design lint: blocking={summary['blocking']} high={summary['high']} medium={summary['medium']} low={summary['low']}")
    return 1 if summary["blocking"] > 0 else 0


def _render_md(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        f"# Design Lint — {payload['work_item']}",
        "",
        f"- Generated at: `{payload.get('generated_at')}`",
        f"- Design: `{payload.get('design_path') or 'missing'}`",
        f"- Summary: blocking={summary.get('blocking', 0)} high={summary.get('high', 0)} medium={summary.get('medium', 0)} low={summary.get('low', 0)}",
        "",
        "## Findings",
        "",
    ]
    findings = payload.get("findings") or []
    if not findings:
        lines.append("No findings.")
        return "\n".join(lines).rstrip() + "\n"
    for finding in findings:
        lines.append(f"- **{finding.get('severity')}** {finding.get('type')}: {finding.get('message')}")
    return "\n".join(lines).rstrip() + "\n"


def _display(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except (FileNotFoundError, ValueError):
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
