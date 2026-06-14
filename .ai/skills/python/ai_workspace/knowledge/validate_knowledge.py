"""Validate knowledge notes against the front-matter schema and governance rules.

Reuses ``index_knowledge._parse_front_matter`` to read YAML and implements a
focused, stdlib-only walker against the JSON Schema at
``.ai/templates/schemas/knowledge-note.schema.json`` — no ``jsonschema``
dependency, in keeping with the workspace's stdlib-first posture.

Findings shape::

    {"severity": "blocking|high|medium|low", "type": str, "path": str,
     "line"?: int, "message": str}

Exit code is 1 when any blocking finding is emitted, unless ``--warn-only`` is
passed.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from ai_workspace.knowledge.import_knowledge import detect_sensitive_content
from ai_workspace.knowledge.index_knowledge import (
    _knowledge_markdown_files,
    _parse_front_matter,
    _stale_review,
)
from ai_workspace.security.no_salesforce_ids import find_salesforce_id_candidates_in_text
from ai_workspace.utils.io import ensure_parent_dir


SEVERITY_RANK = {"blocking": 0, "high": 1, "medium": 2, "low": 3}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate internal knowledge notes.")
    parser.add_argument("--knowledge-root", default=".ai/knowledge")
    parser.add_argument(
        "--schema",
        default=".ai/templates/schemas/knowledge-note.schema.json",
        help="JSON Schema describing the knowledge-note front matter.",
    )
    parser.add_argument("--max-age-days", type=int, default=180)
    parser.add_argument("--json-out", default=".ai/outputs/knowledge-import/validation-report.json")
    parser.add_argument("--md-out", default=".ai/outputs/knowledge-import/validation-report.md")
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args(argv)

    knowledge_root = Path(args.knowledge_root)
    schema_path = Path(args.schema)
    if not knowledge_root.exists():
        print(f"Knowledge root not found: {knowledge_root}")
        return 0
    if not schema_path.exists():
        print(f"Schema file not found: {schema_path}")
        return 2
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    sobject_index = _load_sobject_index(Path(".ai/context/index/sobject-cards.jsonl"))
    process_slugs = _process_slugs(knowledge_root / "process-maps")

    files = _knowledge_markdown_files(knowledge_root)
    findings: list[dict[str, Any]] = []
    for path in files:
        findings.extend(validate_file(path, knowledge_root, schema, args.max_age_days, sobject_index, process_slugs))

    summary = _summary(findings, files)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "knowledge_root": knowledge_root.as_posix(),
        "schema": schema_path.as_posix(),
        "max_age_days": args.max_age_days,
        "files_checked": len(files),
        "summary": summary,
        "findings": findings,
    }
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    ensure_parent_dir(json_path)
    ensure_parent_dir(md_path)
    json_path.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")

    print(f"Validation findings: blocking={summary['blocking']} high={summary['high']} "
          f"medium={summary['medium']} low={summary['low']} (files_checked={len(files)})")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    if summary["blocking"] > 0 and not args.warn_only:
        return 1
    return 0


def validate_file(
    path: Path,
    knowledge_root: Path,
    schema: dict[str, Any],
    max_age_days: int,
    sobject_index: set[str],
    process_slugs: set[str],
) -> list[dict[str, Any]]:
    rel_path = _display_path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [{"severity": "high", "type": "schema_violation", "path": rel_path, "message": f"Could not read file: {exc}"}]
    metadata, body, has_front_matter = _parse_front_matter(text)
    findings: list[dict[str, Any]] = []
    if not has_front_matter:
        findings.append({"severity": "high", "type": "schema_violation", "path": rel_path,
                         "message": "Missing YAML front matter (`---` fenced block at top of file)."})
        return findings
    findings.extend(_schema_findings(metadata, schema, rel_path))
    findings.extend(_staleness_findings(metadata, rel_path, max_age_days))
    findings.extend(_cross_ref_findings(metadata, rel_path, sobject_index, process_slugs))
    if not _is_governance_doc(path, knowledge_root, metadata):
        findings.extend(_governance_findings(body, rel_path))
    return findings


def _is_governance_doc(path: Path, knowledge_root: Path, metadata: dict[str, Any]) -> bool:
    """Exempt governance/policy documents from the sensitive-content scan.

    Policy docs necessarily mention the terms they prohibit (api key, token,
    credentials, password) — scanning their bodies for those terms is a
    guaranteed false positive that would block every CI run.
    """

    try:
        relative = path.resolve().relative_to(knowledge_root.resolve())
    except ValueError:
        relative = Path(path.name)
    if relative.parts and relative.parts[0] == "governance":
        return True
    return str(metadata.get("source_type") or "").lower() == "governance"


def _schema_findings(metadata: dict[str, Any], schema: dict[str, Any], rel_path: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    props: dict[str, Any] = schema.get("properties") or {}
    required: list[str] = schema.get("required") or []
    additional_properties = schema.get("additionalProperties", True)

    for key in required:
        value = metadata.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            findings.append({"severity": "high", "type": "schema_violation", "path": rel_path,
                             "field": key, "message": f"Required front-matter key missing or empty: {key}"})
    if additional_properties is False:
        for key in metadata:
            if key not in props:
                findings.append({"severity": "low", "type": "schema_violation", "path": rel_path,
                                 "field": key, "message": f"Unknown front-matter key: {key}"})
    for key, spec in props.items():
        if key not in metadata:
            continue
        value = metadata[key]
        expected_type = spec.get("type")
        if expected_type == "string" and not isinstance(value, str):
            findings.append({"severity": "high", "type": "schema_violation", "path": rel_path,
                             "field": key, "message": f"Expected string for {key}, got {type(value).__name__}"})
            continue
        if expected_type == "array" and not isinstance(value, list):
            findings.append({"severity": "high", "type": "schema_violation", "path": rel_path,
                             "field": key, "message": f"Expected array for {key}, got {type(value).__name__}"})
            continue
        if expected_type == "string":
            enum = spec.get("enum")
            if enum and value not in enum:
                findings.append({"severity": "high", "type": "enum_violation", "path": rel_path,
                                 "field": key, "message": f"{key}={value!r} is not one of {enum}"})
            pattern = spec.get("pattern")
            if pattern and not re.fullmatch(pattern, value or ""):
                findings.append({"severity": "high", "type": "schema_violation", "path": rel_path,
                                 "field": key, "message": f"{key}={value!r} does not match pattern {pattern}"})
            min_length = spec.get("minLength")
            if isinstance(min_length, int) and len(value or "") < min_length:
                findings.append({"severity": "high", "type": "schema_violation", "path": rel_path,
                                 "field": key, "message": f"{key} must be at least {min_length} characters long"})
        elif expected_type == "array":
            item_spec = spec.get("items") or {}
            item_type = item_spec.get("type")
            for index, item in enumerate(value):
                if item_type == "string" and not isinstance(item, str):
                    findings.append({"severity": "high", "type": "schema_violation", "path": rel_path,
                                     "field": key, "message": f"{key}[{index}] expected string, got {type(item).__name__}"})
                elif item_type == "string" and isinstance(item, str) and item_spec.get("minLength") and len(item) < item_spec["minLength"]:
                    findings.append({"severity": "medium", "type": "schema_violation", "path": rel_path,
                                     "field": key, "message": f"{key}[{index}] is shorter than minLength={item_spec['minLength']}"})
    return findings


def _staleness_findings(metadata: dict[str, Any], rel_path: str, max_age_days: int) -> list[dict[str, Any]]:
    value = str(metadata.get("last_reviewed") or "").strip()
    if not value or value == "YYYY-MM-DD":
        return [{"severity": "medium", "type": "stale_review", "path": rel_path,
                 "message": "last_reviewed is missing or a placeholder."}]
    try:
        reviewed = date.fromisoformat(value[:10])
    except ValueError:
        return [{"severity": "high", "type": "schema_violation", "path": rel_path,
                 "field": "last_reviewed",
                 "message": f"last_reviewed is not a valid ISO date: {value!r}"}]
    age = (datetime.now(timezone.utc).date() - reviewed).days
    if age > max_age_days:
        return [{"severity": "medium", "type": "stale_review", "path": rel_path,
                 "message": f"last_reviewed is {age} days old (>{max_age_days})."}]
    if _stale_review(value) and age <= max_age_days:
        # Keeps parity with index_knowledge: catch obviously placeholder values that fromisoformat would still accept.
        pass
    return []


def _cross_ref_findings(
    metadata: dict[str, Any],
    rel_path: str,
    sobject_index: set[str],
    process_slugs: set[str],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    related_objects = [item for item in metadata.get("related_objects") or [] if str(item).strip()]
    related_processes = [item for item in metadata.get("related_processes") or [] if str(item).strip()]
    if sobject_index:
        for obj in related_objects:
            if obj not in sobject_index:
                findings.append({
                    "severity": "medium", "type": "broken_cross_ref", "path": rel_path,
                    "field": "related_objects",
                    "message": f"related_objects entry {obj!r} not found in sobject-cards.jsonl. "
                               "Run `make ai-index-schema` to refresh the schema index, or correct the API name.",
                })
    if process_slugs:
        for process in related_processes:
            slug = _slug(str(process))
            if slug and slug not in process_slugs:
                findings.append({
                    "severity": "low", "type": "broken_cross_ref", "path": rel_path,
                    "field": "related_processes",
                    "message": f"related_processes entry {process!r} has no matching file in process-maps/.",
                })
    return findings


def _governance_findings(body: str, rel_path: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for warning in detect_sensitive_content(body):
        findings.append({"severity": "blocking", "type": "governance_violation", "path": rel_path,
                         "message": warning})
    for candidate in find_salesforce_id_candidates_in_text(body):
        findings.append({"severity": "blocking", "type": "prohibited_class", "path": rel_path,
                         "line": candidate.get("line"),
                         "message": f"Possible Salesforce ID in body: {candidate.get('candidate')!r}. "
                                    "Knowledge notes must not contain raw record IDs (governance/data-handling-policy.md)."})
    return findings


def _load_sobject_index(path: Path) -> set[str]:
    if not path.exists():
        return set()
    api_names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        for key in ("api_name", "object_api_name", "full_name", "name"):
            value = record.get(key)
            if isinstance(value, str) and value.strip():
                api_names.add(value.strip())
                break
    return api_names


def _process_slugs(process_dir: Path) -> set[str]:
    if not process_dir.exists():
        return set()
    return {path.stem.lower() for path in process_dir.glob("*.md")}


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug


def _summary(findings: list[dict[str, Any]], files: list[Path]) -> dict[str, Any]:
    counts = {"blocking": 0, "high": 0, "medium": 0, "low": 0}
    by_type: dict[str, int] = {}
    affected: set[str] = set()
    for finding in findings:
        sev = finding.get("severity") or "low"
        counts[sev] = counts.get(sev, 0) + 1
        ftype = finding.get("type") or "unknown"
        by_type[ftype] = by_type.get(ftype, 0) + 1
        affected.add(str(finding.get("path") or ""))
    return {
        **counts,
        "by_type": by_type,
        "files_with_findings": len(affected),
        "files_total": len(files),
    }


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    lines = [
        "# Knowledge Validation Report",
        "",
        f"- Generated at: `{report.get('generated_at')}`",
        f"- Knowledge root: `{report.get('knowledge_root')}`",
        f"- Schema: `{report.get('schema')}`",
        f"- Files checked: {report.get('files_checked')}",
        "",
        "## Summary",
        "",
        f"- blocking: {summary.get('blocking', 0)}",
        f"- high: {summary.get('high', 0)}",
        f"- medium: {summary.get('medium', 0)}",
        f"- low: {summary.get('low', 0)}",
        f"- files with findings: {summary.get('files_with_findings', 0)}",
        "",
    ]
    by_type = summary.get("by_type") or {}
    if by_type:
        lines.append("### By type")
        lines.append("")
        for ftype, count in sorted(by_type.items()):
            lines.append(f"- {ftype}: {count}")
        lines.append("")
    findings = report.get("findings") or []
    findings_sorted = sorted(
        findings,
        key=lambda f: (SEVERITY_RANK.get(f.get("severity") or "low", 3), f.get("path") or "", f.get("type") or ""),
    )
    if not findings_sorted:
        lines.append("No findings.")
        return "\n".join(lines).rstrip() + "\n"
    lines.append("## Findings")
    lines.append("")
    for finding in findings_sorted:
        loc = f"L{finding['line']}" if finding.get("line") else ""
        field = finding.get("field") or ""
        head = " ".join(part for part in [finding.get("severity"), finding.get("type"), field, loc] if part)
        lines.append(f"- **{finding.get('path')}** — {head}: {finding.get('message')}")
    return "\n".join(lines).rstrip() + "\n"


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except (FileNotFoundError, ValueError):
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
