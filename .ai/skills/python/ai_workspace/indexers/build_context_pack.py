"""Build a concise Work Item context pack from local AI index files."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_workspace.search.ranking import (
    CONFIDENCE_RANK as _CONFIDENCE_RANK,
    RISK_PENALTY as _RISK_PENALTY,
    STATUS_RANK as _STATUS_RANK,
    knowledge_quality_rank as _knowledge_quality_rank,
)
from ai_workspace.search.simple_search import score_record, search_jsonl, tokenize


INDEX_FILES = {
    "metadata": "metadata-components.jsonl",
    "sobjects": "sobject-cards.jsonl",
    "fields": "field-cards.jsonl",
    "relationships": "relationship-cards.jsonl",
    "config_records": "config-record-cards.jsonl",
    "knowledge": "knowledge-cards.jsonl",
}

METADATA_GROUP_ORDER = [
    "ApexClass",
    "ApexTrigger",
    "Flow",
    "LWC",
    "FlexiPage",
    "Layout",
    "PermissionSet",
    "Profile",
    "CustomMetadata",
    "Other",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a local Work Item context pack from AI index files."
    )
    parser.add_argument("--work-item", required=True, help="Work Item ID.")
    parser.add_argument("--query", required=True, help="Search query for relevant context.")
    parser.add_argument("--index-dir", default=".ai/context/index", help="Local index directory.")
    parser.add_argument("--work-item-dir", help="Work Item artifact directory.")
    parser.add_argument("--out", help="Context pack markdown output path.")
    parser.add_argument("--metadata-limit", type=int, default=20)
    parser.add_argument("--schema-limit", type=int, default=20)
    parser.add_argument("--field-limit", type=int, default=30)
    parser.add_argument("--config-limit", type=int, default=20)
    parser.add_argument("--knowledge-limit", type=int, default=10)
    args = parser.parse_args(argv)

    work_item_dir = Path(args.work_item_dir or f".ai/context/work-items/{args.work_item}")
    out_path = Path(args.out or work_item_dir / "context-pack.md")
    index_dir = Path(args.index_dir)
    generated_at = datetime.now(timezone.utc).isoformat()
    warnings: list[str] = []

    work_item_summary = _read_optional(work_item_dir / "work-item-summary.md")
    acceptance_criteria = _read_optional(work_item_dir / "acceptance-criteria.md")
    ado_work_item = _read_json_optional(work_item_dir / "ado-work-item.json", warnings)

    input_files = _input_file_info(index_dir, warnings)
    metadata = _search_index(index_dir / INDEX_FILES["metadata"], args.query, args.metadata_limit)
    sobjects = _search_index(index_dir / INDEX_FILES["sobjects"], args.query, args.schema_limit)
    fields = _search_index(index_dir / INDEX_FILES["fields"], args.query, args.field_limit)
    relationships = _search_index(index_dir / INDEX_FILES["relationships"], args.query, args.schema_limit)
    config_records = _search_index(index_dir / INDEX_FILES["config_records"], args.query, args.config_limit)
    knowledge_raw = _search_index(index_dir / INDEX_FILES["knowledge"], args.query, args.knowledge_limit * 3)
    knowledge = sorted(
        knowledge_raw,
        key=lambda r: (-float(r.get("_search_score", 0)), _knowledge_quality_rank(r)),
    )[:args.knowledge_limit]

    selected_counts = {
        "metadata": len(metadata),
        "sobjects": len(sobjects),
        "fields": len(fields),
        "relationships": len(relationships),
        "config_records": len(config_records),
        "knowledge": len(knowledge),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    _write_text(out_path, _context_markdown(
        work_item=args.work_item,
        query=args.query,
        generated_at=generated_at,
        input_files=input_files,
        warnings=warnings,
        selected_counts=selected_counts,
        work_item_summary=work_item_summary,
        acceptance_criteria=acceptance_criteria,
        ado_work_item=ado_work_item,
        metadata=metadata,
        sobjects=sobjects,
        fields=fields,
        relationships=relationships,
        config_records=config_records,
        knowledge=knowledge,
    ))
    _write_text(work_item_dir / "relevant-metadata.yaml", _metadata_yaml(metadata, args.query))
    _write_text(work_item_dir / "relevant-schema.yaml", _schema_yaml(sobjects, fields, relationships, args.query))
    _write_text(work_item_dir / "relevant-config-records.yaml", _config_yaml(config_records, args.query))
    _write_text(work_item_dir / "relevant-knowledge.yaml", _knowledge_yaml(knowledge, args.query))

    context_sources = {
        "work_item": args.work_item,
        "query": args.query,
        "generated_at": generated_at,
        "input_files": input_files,
        "selected_counts": selected_counts,
        "warnings": warnings,
    }
    _write_text(
        work_item_dir / "context-sources.json",
        json.dumps(context_sources, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
    )

    print(f"Wrote context pack to {out_path}")
    return 0


def _search_index(path: Path, query: str, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return search_jsonl(str(path), query, limit)


def _input_file_info(index_dir: Path, warnings: list[str]) -> dict[str, dict[str, Any]]:
    info: dict[str, dict[str, Any]] = {}
    for key, filename in INDEX_FILES.items():
        path = index_dir / filename
        exists = path.exists()
        record_count = _count_jsonl_records(path) if exists else 0
        if not exists:
            warnings.append(f"Missing index file: {path.as_posix()}")
        info[key] = {
            "path": path.as_posix(),
            "exists": exists,
            "record_count": record_count,
        }
    return info


def _count_jsonl_records(path: Path) -> int:
    count = 0
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    count += 1
    except OSError:
        return 0
    return count


def _context_markdown(
    work_item: str,
    query: str,
    generated_at: str,
    input_files: dict[str, dict[str, Any]],
    warnings: list[str],
    selected_counts: dict[str, int],
    work_item_summary: str | None,
    acceptance_criteria: str | None,
    ado_work_item: dict[str, Any] | None,
    metadata: list[dict[str, Any]],
    sobjects: list[dict[str, Any]],
    fields: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    config_records: list[dict[str, Any]],
    knowledge: list[dict[str, Any]],
) -> str:
    lines: list[str] = []
    lines.append(f"# Context Pack — {work_item}")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append(
        "This is a curated AI context artifact for Copilot-assisted solution design. "
        "It is not the source of truth. Validate all conclusions against ADO, Salesforce schema, "
        "repository metadata, anonymized configuration records, and human architect review."
    )
    lines.append("")
    lines.append("## Work Item Summary")
    lines.append("")
    if work_item_summary:
        lines.append(_clip(work_item_summary, 2500))
    elif ado_work_item:
        lines.extend(_ado_summary_lines(ado_work_item))
    else:
        lines.append(f"Placeholder: no local Work Item summary was found for `{work_item}`.")
    if acceptance_criteria:
        lines.append("")
        lines.append("### Acceptance Criteria")
        lines.append("")
        lines.append(_clip(acceptance_criteria, 1800))
    lines.append("")
    lines.append("## Query")
    lines.append("")
    lines.append(f"`{query}`")
    lines.append("")
    lines.append("## Context Build Summary")
    lines.append("")
    lines.append(f"- Generated at: `{generated_at}`")
    lines.append("- Index files used:")
    for key in sorted(input_files):
        item = input_files[key]
        lines.append(
            f"  - {key}: `{item['path']}` exists={str(item['exists']).lower()} records={item['record_count']}"
        )
    lines.append("- Selected counts:")
    for key in sorted(selected_counts):
        lines.append(f"  - {key}: {selected_counts[key]}")
    if warnings:
        lines.append("- Warnings:")
        for warning in warnings:
            lines.append(f"  - {warning}")
    else:
        lines.append("- Warnings: none")
    lines.append("")

    lines.extend(_metadata_section(metadata, query))
    lines.extend(_sobject_section(sobjects, query))
    lines.extend(_field_section(fields, query))
    lines.extend(_relationship_section(relationships, query))
    lines.extend(_config_section(config_records, query))
    lines.extend(_knowledge_section(knowledge, query))
    lines.extend(_dependency_observations(metadata, fields, relationships, config_records))
    lines.extend(_current_state_clues(metadata, sobjects, fields, config_records, knowledge))
    lines.extend(_context_gaps(input_files, warnings, selected_counts))
    lines.extend(_next_steps())
    return "\n".join(lines).rstrip() + "\n"


def _metadata_section(records: list[dict[str, Any]], query: str) -> list[str]:
    lines = ["## Relevant Metadata", ""]
    grouped: dict[str, list[dict[str, Any]]] = {key: [] for key in METADATA_GROUP_ORDER}
    for record in records:
        component_type = str(record.get("component_type") or "Other")
        group = component_type if component_type in grouped else "Other"
        grouped[group].append(record)
    if not records:
        lines.append("No relevant metadata records were selected from the local index.")
        lines.append("")
        return lines
    for group in METADATA_GROUP_ORDER:
        if not grouped[group]:
            continue
        lines.append(f"### {group}")
        lines.append("")
        for record in grouped[group]:
            lines.append(f"- **{_record_name(record)}**")
            lines.append(f"  - Path: `{_value(record, 'path')}`")
            lines.append(f"  - Summary: {_clip(_value(record, 'summary'), 280)}")
            lines.append(f"  - References: {_compact_json(record.get('references') or {})}")
            lines.append(f"  - Risk flags: {_list_text(record.get('risk_flags'))}")
            lines.append(f"  - Confidence: {_confidence(record, query)}")
        lines.append("")
    return lines


def _sobject_section(records: list[dict[str, Any]], query: str) -> list[str]:
    lines = ["## Relevant Salesforce Objects", ""]
    if not records:
        lines.append("No relevant Salesforce object cards were selected from the local index.")
        lines.append("")
        return lines
    for record in records:
        lines.append(f"- **{_value(record, 'api_name')}**")
        lines.append(f"  - Label: {_value(record, 'label')}")
        lines.append(f"  - Namespace: {_value(record, 'namespace')}")
        lines.append(f"  - Source: {_value(record, 'source')}")
        lines.append(f"  - Field count: {_value(record, 'field_count')}")
        lines.append(f"  - Relationship count: {_value(record, 'relationship_count')}")
        lines.append(f"  - Summary: {_clip(_value(record, 'summary'), 280)}")
        lines.append(f"  - Confidence: {_confidence(record, query)}")
    lines.append("")
    return lines


def _field_section(records: list[dict[str, Any]], query: str) -> list[str]:
    lines = ["## Relevant Fields", ""]
    if not records:
        lines.append("No relevant field cards were selected from the local index.")
        lines.append("")
        return lines
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[_value(record, "object_api_name")].append(record)
    for object_api_name in sorted(grouped):
        lines.append(f"### {object_api_name or 'Unknown Object'}")
        lines.append("")
        for record in grouped[object_api_name]:
            flags = [
                f"required={_value(record, 'is_required')}",
                f"calculated={_value(record, 'is_calculated')}",
                f"indexed={_value(record, 'is_indexed')}",
            ]
            lines.append(f"- **{_value(record, 'field_api_name')}**")
            lines.append(f"  - Label: {_value(record, 'label')}")
            lines.append(f"  - Data type: {_value(record, 'data_type')}")
            lines.append(f"  - Flags: {', '.join(flags)}")
            lines.append(f"  - Reference to: {_list_text(record.get('reference_to'))}")
            lines.append(f"  - Summary: {_clip(_value(record, 'summary'), 280)}")
            lines.append(f"  - Confidence: {_confidence(record, query)}")
        lines.append("")
    return lines


def _relationship_section(records: list[dict[str, Any]], query: str) -> list[str]:
    lines = ["## Relevant Relationships", ""]
    if not records:
        lines.append("No relevant relationship cards were selected from the local index.")
        lines.append("")
        return lines
    for record in records:
        lines.append(f"- **{_value(record, 'from_object')}.{_value(record, 'field_api_name')}**")
        lines.append(f"  - To objects: {_list_text(record.get('to_objects'))}")
        lines.append(f"  - Relationship name: {_value(record, 'relationship_name')}")
        lines.append(f"  - Summary: {_clip(_value(record, 'summary'), 280)}")
        lines.append(f"  - Confidence: {_confidence(record, query)}")
    lines.append("")
    return lines


def _config_section(records: list[dict[str, Any]], query: str) -> list[str]:
    lines = ["## Relevant KimbleOne/Kantata Config Records", ""]
    if not records:
        lines.append("No relevant anonymized config record cards were selected from the local index.")
        lines.append("")
        return lines
    for record in records:
        fields = record.get("fields") if isinstance(record.get("fields"), dict) else {}
        fields_summary = ", ".join(sorted(str(key) for key in fields)[:8])
        lines.append(f"- **{_value(record, 'record_key')}**")
        lines.append(f"  - Object: {_value(record, 'object_api_name')}")
        lines.append(f"  - Category: {_value(record, 'category')}")
        lines.append(f"  - AI visibility: {_value(record, 'ai_visibility')}")
        lines.append(f"  - Summary: {_clip(_value(record, 'summary'), 280)}")
        lines.append(f"  - Fields summary: {fields_summary or 'none'}")
        lines.append(f"  - References: {_compact_json(record.get('references') or [])}")
        lines.append(f"  - Checksum: `{_value(record, 'checksum')}`")
        lines.append(f"  - Confidence: {_confidence(record, query)}")
    lines.append("")
    return lines


def _knowledge_section(records: list[dict[str, Any]], query: str) -> list[str]:
    lines = ["## Relevant Internal Knowledge", ""]
    if not records:
        lines.append("No relevant internal knowledge cards were selected from the local index.")
        lines.append("")
        return lines
    lines.append(
        "Internal knowledge notes are supporting evidence only. Draft, low-confidence, or stale notes require human validation."
    )
    lines.append("")
    for record in records:
        validation_notes = []
        risk_flags = record.get("risk_flags") if isinstance(record.get("risk_flags"), list) else []
        if str(record.get("status") or "").lower() == "draft" or "draft_status" in risk_flags:
            validation_notes.append("Needs human validation")
        if str(record.get("confidence") or "").lower() == "low" or "low_confidence" in risk_flags:
            validation_notes.append("Low confidence")
        if "stale_review" in risk_flags:
            validation_notes.append("Review date stale or missing")
        lines.append(f"- **{_value(record, 'title')}**")
        lines.append(f"  - Domain: {_value(record, 'domain')}")
        lines.append(f"  - Path: `{_value(record, 'path')}`")
        lines.append(f"  - Source file: `{_value(record, 'source_file')}`")
        lines.append(f"  - Confidence: {_value(record, 'confidence')}")
        lines.append(f"  - Status: {_value(record, 'status')}")
        lines.append(f"  - Last reviewed: {_value(record, 'last_reviewed')}")
        lines.append(f"  - Summary: {_clip(_value(record, 'summary') or _value(record, 'content_excerpt'), 320)}")
        lines.append(f"  - Related objects: {_list_text(record.get('related_objects'))}")
        lines.append(f"  - Related config objects: {_list_text(record.get('related_config_objects'))}")
        lines.append(f"  - Related processes: {_list_text(record.get('related_processes'))}")
        lines.append(f"  - Risk flags: {_list_text(risk_flags)}")
        lines.append(f"  - Validation notes: {', '.join(validation_notes) if validation_notes else 'none'}")
        lines.append(f"  - Search confidence: {_confidence(record, query)}")
    lines.append("")
    return lines


def _dependency_observations(
    metadata: list[dict[str, Any]],
    fields: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    config_records: list[dict[str, Any]],
) -> list[str]:
    lines = ["## Dependency / Relationship Observations", ""]
    observations: list[str] = []
    object_refs: set[str] = set()
    field_refs: set[str] = set()
    for record in metadata:
        references = record.get("references") if isinstance(record.get("references"), dict) else {}
        object_refs.update(str(item) for item in references.get("objects", []) if item)
        field_refs.update(str(item) for item in references.get("fields", []) if item)
    if object_refs:
        observations.append(f"The index indicates metadata references object candidates: {', '.join(sorted(object_refs)[:12])}.")
    if field_refs:
        observations.append(f"The index indicates metadata references field candidates: {', '.join(sorted(field_refs)[:12])}.")
    relationship_names = [
        f"{_value(record, 'from_object')}.{_value(record, 'field_api_name')}"
        for record in relationships
        if _value(record, "from_object") or _value(record, "field_api_name")
    ]
    if relationship_names:
        observations.append(f"Relationship cards selected: {', '.join(sorted(relationship_names)[:12])}.")
    config_refs = []
    for record in config_records:
        refs = record.get("references")
        if isinstance(refs, list):
            config_refs.extend(str(item.get("field")) for item in refs if isinstance(item, dict) and item.get("field"))
    if config_refs:
        observations.append(f"Config record reference hints appear in fields: {', '.join(sorted(set(config_refs))[:12])}.")
    if not observations:
        observations.append("No dependency observations were strong enough to summarize from the selected records.")
    for observation in observations:
        lines.append(f"- {observation}")
    lines.append("")
    return lines


def _current_state_clues(
    metadata: list[dict[str, Any]],
    sobjects: list[dict[str, Any]],
    fields: list[dict[str, Any]],
    config_records: list[dict[str, Any]],
    knowledge: list[dict[str, Any]],
) -> list[str]:
    lines = ["## Current-State Functional Clues", ""]
    if metadata:
        lines.append(f"- The index indicates {len(metadata)} local metadata component(s) may be relevant.")
    if sobjects:
        lines.append(f"- The index indicates {len(sobjects)} Salesforce object card(s) may be relevant.")
    if fields:
        lines.append(f"- The index indicates {len(fields)} field card(s) may be relevant.")
    if config_records:
        lines.append(f"- The index indicates {len(config_records)} anonymized configuration record card(s) may be relevant.")
    if knowledge:
        lines.append(f"- The index indicates {len(knowledge)} internal knowledge note(s) may be relevant.")
    if not any((metadata, sobjects, fields, config_records, knowledge)):
        lines.append("- The local indexes did not produce relevant current-state clues for the query.")
    lines.append("- This may suggest areas for solution design analysis, but requires human validation.")
    lines.append("")
    return lines


def _context_gaps(
    input_files: dict[str, dict[str, Any]],
    warnings: list[str],
    selected_counts: dict[str, int],
) -> list[str]:
    lines = ["## Context Gaps", ""]
    gaps: list[str] = []
    for key, item in input_files.items():
        if not item.get("exists"):
            gaps.append(f"Missing {key} index file: `{item.get('path')}`.")
        elif item.get("record_count") == 0:
            gaps.append(f"{key} index file exists but has zero records.")
    for key, count in selected_counts.items():
        if count == 0:
            gaps.append(f"No selected {key} records matched the query.")
    gaps.extend(warnings)
    if not gaps:
        gaps.append("No major context gaps were detected from local files.")
    for gap in sorted(set(gaps)):
        lines.append(f"- {gap}")
    lines.append("")
    return lines


def _next_steps() -> list[str]:
    return [
        "## Recommended Next Steps",
        "",
        "- Review this context pack with a human architect.",
        "- Run `/solution-design` after confirming the Work Item and acceptance criteria.",
        "- Check missing schema or config indexes if the selected context is weak.",
        "- Validate assumptions before creating implementation work packets.",
        "",
    ]


def _metadata_yaml(records: list[dict[str, Any]], query: str) -> str:
    if not records:
        return "metadata: []\n"
    lines = ["metadata:"]
    for record in records:
        lines.extend([
            f"  - component_type: {_yaml_scalar(_value(record, 'component_type'))}",
            f"    full_name: {_yaml_scalar(_record_name(record))}",
            f"    path: {_yaml_scalar(_value(record, 'path'))}",
            f"    confidence: {_yaml_scalar(_confidence(record, query))}",
            f"    risk_flags: {_yaml_list(record.get('risk_flags'))}",
        ])
    return "\n".join(lines) + "\n"


def _schema_yaml(
    sobjects: list[dict[str, Any]],
    fields: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    query: str,
) -> str:
    if not sobjects and not fields and not relationships:
        return "sobjects: []\nfields: []\nrelationships: []\n"
    lines = ["sobjects:"]
    if sobjects:
        for record in sobjects:
            lines.extend([
                f"  - api_name: {_yaml_scalar(_value(record, 'api_name'))}",
                f"    label: {_yaml_scalar(_value(record, 'label'))}",
                f"    namespace: {_yaml_scalar(_value(record, 'namespace'))}",
                f"    confidence: {_yaml_scalar(_confidence(record, query))}",
            ])
    else:
        lines.append("  []")
    lines.append("fields:")
    if fields:
        for record in fields:
            lines.extend([
                f"  - object_api_name: {_yaml_scalar(_value(record, 'object_api_name'))}",
                f"    field_api_name: {_yaml_scalar(_value(record, 'field_api_name'))}",
                f"    data_type: {_yaml_scalar(_value(record, 'data_type'))}",
                f"    confidence: {_yaml_scalar(_confidence(record, query))}",
            ])
    else:
        lines.append("  []")
    lines.append("relationships:")
    if relationships:
        for record in relationships:
            lines.extend([
                f"  - from_object: {_yaml_scalar(_value(record, 'from_object'))}",
                f"    field_api_name: {_yaml_scalar(_value(record, 'field_api_name'))}",
                f"    relationship_name: {_yaml_scalar(_value(record, 'relationship_name'))}",
                f"    confidence: {_yaml_scalar(_confidence(record, query))}",
            ])
    else:
        lines.append("  []")
    return "\n".join(lines) + "\n"


def _config_yaml(records: list[dict[str, Any]], query: str) -> str:
    if not records:
        return "config_records: []\n"
    lines = ["config_records:"]
    if records:
        for record in records:
            lines.extend([
                f"  - object_api_name: {_yaml_scalar(_value(record, 'object_api_name'))}",
                f"    record_key: {_yaml_scalar(_value(record, 'record_key'))}",
                f"    category: {_yaml_scalar(_value(record, 'category'))}",
                f"    ai_visibility: {_yaml_scalar(_value(record, 'ai_visibility'))}",
                f"    checksum: {_yaml_scalar(_value(record, 'checksum'))}",
                f"    confidence: {_yaml_scalar(_confidence(record, query))}",
            ])
    return "\n".join(lines) + "\n"


def _knowledge_yaml(records: list[dict[str, Any]], query: str) -> str:
    if not records:
        return "knowledge: []\n"
    lines = ["knowledge:"]
    for record in records:
        lines.extend([
            f"  - title: {_yaml_scalar(_value(record, 'title'))}",
            f"    domain: {_yaml_scalar(_value(record, 'domain'))}",
            f"    path: {_yaml_scalar(_value(record, 'path'))}",
            f"    source_file: {_yaml_scalar(_value(record, 'source_file'))}",
            f"    status: {_yaml_scalar(_value(record, 'status'))}",
            f"    confidence: {_yaml_scalar(_value(record, 'confidence'))}",
            f"    last_reviewed: {_yaml_scalar(_value(record, 'last_reviewed'))}",
            f"    keywords: {_yaml_list(record.get('keywords'))}",
            f"    related_objects: {_yaml_list(record.get('related_objects'))}",
            f"    risk_flags: {_yaml_list(record.get('risk_flags'))}",
            f"    search_confidence: {_yaml_scalar(_confidence(record, query))}",
        ])
    return "\n".join(lines) + "\n"


def _confidence(record: dict[str, Any], query: str) -> str:
    terms = tokenize(query)
    score = float(record.get("_search_score") or score_record(record, terms))
    important = " ".join(
        str(record.get(key) or "")
        for key in ("full_name", "api_name", "object_api_name", "field_api_name", "record_key", "title", "path")
    ).lower()
    query_lower = query.lower().strip()
    if query_lower and query_lower in important:
        return "high"
    if score >= 8:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def _ado_summary_lines(ado_work_item: dict[str, Any]) -> list[str]:
    lines = []
    for key in ("title", "description", "business_summary", "summary"):
        value = ado_work_item.get(key)
        if value:
            lines.append(f"- {key}: {_clip(str(value), 800)}")
    return lines or ["Placeholder: local ADO Work Item JSON did not contain summary text."]


def _read_optional(path: Path) -> str | None:
    try:
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return None


def _read_json_optional(path: Path, warnings: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"Could not read Work Item JSON `{path.as_posix()}`: {exc}")
        return None
    return loaded if isinstance(loaded, dict) else None


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _record_name(record: dict[str, Any]) -> str:
    for key in ("full_name", "api_name", "record_key", "name"):
        if record.get(key):
            return str(record[key])
    return "Unnamed"


def _value(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if value is None:
        return ""
    return str(value)


def _list_text(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "none"
    if value:
        return str(value)
    return "none"


def _compact_json(value: Any) -> str:
    return _clip(json.dumps(value, ensure_ascii=True, sort_keys=True), 360)


def _clip(text: str, max_length: int) -> str:
    normalized = text.strip()
    if len(normalized) <= max_length:
        return normalized
    return normalized[:max_length] + "...[TRUNCATED]"


def _yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def _yaml_list(value: Any) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(json.dumps(str(item), ensure_ascii=True) for item in value) + "]"
    return "[]"


if __name__ == "__main__":
    raise SystemExit(main())
