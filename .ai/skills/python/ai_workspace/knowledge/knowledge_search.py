"""Search local internal knowledge cards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ai_workspace.search.simple_search import record_to_search_text, search_jsonl, tokenize


def load_knowledge_cards(index_path: str | Path) -> list[dict[str, Any]]:
    path = Path(index_path)
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            loaded = json.loads(line)
            if isinstance(loaded, dict):
                records.append(loaded)
    return records


def search_knowledge(
    query: str,
    index_path: str | Path,
    top_k: int = 10,
    *,
    domain: str | None = None,
    usage_context: str | None = None,
    object_api_name: str | None = None,
    field_api_name: str | None = None,
    metadata_type: str | None = None,
    status: str | None = None,
    confidence: str | None = None,
    expand_synonyms: bool = False,
) -> list[dict[str, Any]]:
    raw = search_jsonl(
        str(index_path),
        query,
        max(1, top_k) * 5,
        mode="bm25",
        synonyms=None if expand_synonyms else False,
    )
    filtered: list[dict[str, Any]] = []
    for record in raw:
        if not _matches_filters(
            record,
            domain=domain,
            usage_context=usage_context,
            object_api_name=object_api_name,
            field_api_name=field_api_name,
            metadata_type=metadata_type,
            status=status,
            confidence=confidence,
        ):
            continue
        record = dict(record)
        record["_search_explanation"] = _explain_match(query, record)
        filtered.append(record)
        if len(filtered) >= top_k:
            break
    return filtered


def record_to_knowledge_context(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": record.get("title"),
        "domain": record.get("domain"),
        "path": record.get("path"),
        "source_file": record.get("source_file"),
        "confidence": record.get("confidence"),
        "status": record.get("status"),
        "last_reviewed": record.get("last_reviewed"),
        "summary": record.get("summary"),
        "purpose": record.get("purpose"),
        "usage_context": record.get("usage_context") or [],
        "tags": record.get("tags") or [],
        "aliases": record.get("aliases") or [],
        "key_concepts": record.get("key_concepts") or [],
        "related_objects": record.get("related_objects") or [],
        "related_fields": record.get("related_fields") or [],
        "related_config_objects": record.get("related_config_objects") or [],
        "related_metadata": record.get("related_metadata") or [],
        "related_processes": record.get("related_processes") or [],
        "integration_points": record.get("integration_points") or [],
        "dependencies": record.get("dependencies") or [],
        "business_rules": record.get("business_rules") or [],
        "risk_flags": record.get("risk_flags") or [],
        "score": record.get("_search_score"),
        "search_explanation": record.get("_search_explanation") or {},
    }


def results_to_markdown(query: str, results: list[dict[str, Any]]) -> str:
    lines = ["# Knowledge Search Results", "", f"Query: `{query}`", ""]
    if not results:
        lines.append("No matching knowledge cards were found.")
        return "\n".join(lines).rstrip() + "\n"
    for record in results:
        lines.append(f"- **{_value(record, 'title')}**")
        lines.append(f"  - Domain: {_value(record, 'domain')}")
        lines.append(f"  - Path: `{_value(record, 'path')}`")
        lines.append(f"  - Source file: `{_value(record, 'source_file')}`")
        lines.append(f"  - Status: {_value(record, 'status')}")
        lines.append(f"  - Confidence: {_value(record, 'confidence')}")
        lines.append(f"  - Last reviewed: {_value(record, 'last_reviewed')}")
        lines.append(f"  - Summary: {_clip(_value(record, 'summary'), 360)}")
        lines.append(f"  - Usage context: {_list_text(record.get('usage_context'))}")
        lines.append(f"  - Key concepts: {_list_text(record.get('key_concepts'))}")
        lines.append(f"  - Related objects: {_list_text(record.get('related_objects'))}")
        lines.append(f"  - Related fields: {_list_text(record.get('related_fields'))}")
        lines.append(f"  - Related metadata: {_list_text(record.get('related_metadata'))}")
        lines.append(f"  - Related config objects: {_list_text(record.get('related_config_objects'))}")
        lines.append(f"  - Related processes: {_list_text(record.get('related_processes'))}")
        lines.append(f"  - Risk flags: {_list_text(record.get('risk_flags'))}")
        lines.append(f"  - Score: {_value(record, 'score')}")
        explanation = record.get("search_explanation") if isinstance(record.get("search_explanation"), dict) else {}
        if explanation:
            lines.append(f"  - Matched terms: {_list_text(explanation.get('matched_terms'))}")
            lines.append(f"  - Matched fields: {_list_text(explanation.get('matched_fields'))}")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search internal knowledge cards.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--index", default=".ai/context/index/knowledge-cards.jsonl")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--domain")
    parser.add_argument("--usage-context")
    parser.add_argument("--object")
    parser.add_argument("--field")
    parser.add_argument("--metadata-type")
    parser.add_argument("--status")
    parser.add_argument("--confidence")
    parser.add_argument("--expand-synonyms", action="store_true")
    args = parser.parse_args(argv)
    results = [
        record_to_knowledge_context(record)
        for record in search_knowledge(
            args.query,
            args.index,
            args.top_k,
            domain=args.domain,
            usage_context=args.usage_context,
            object_api_name=args.object,
            field_api_name=args.field,
            metadata_type=args.metadata_type,
            status=args.status,
            confidence=args.confidence,
            expand_synonyms=args.expand_synonyms,
        )
    ]
    print(results_to_markdown(args.query, results), end="")
    return 0


def _matches_filters(
    record: dict[str, Any],
    *,
    domain: str | None,
    usage_context: str | None,
    object_api_name: str | None,
    field_api_name: str | None,
    metadata_type: str | None,
    status: str | None,
    confidence: str | None,
) -> bool:
    if domain and str(record.get("domain") or "").lower() != domain.lower():
        return False
    if status and str(record.get("status") or "").lower() != status.lower():
        return False
    if confidence and str(record.get("confidence") or "").lower() != confidence.lower():
        return False
    if usage_context and usage_context.lower() not in [str(item).lower() for item in record.get("usage_context") or []]:
        return False
    if object_api_name and object_api_name not in [str(item) for item in record.get("related_objects") or []]:
        return False
    if field_api_name:
        fields = [str(item) for item in record.get("related_fields") or []]
        if field_api_name not in fields and not any(value.endswith(f".{field_api_name}") for value in fields):
            return False
    if metadata_type:
        needle = metadata_type.lower()
        metadata = " ".join(str(item) for item in record.get("related_metadata") or []).lower()
        if needle not in metadata:
            return False
    return True


def _explain_match(query: str, record: dict[str, Any]) -> dict[str, Any]:
    query_terms = set(tokenize(query))
    matched_terms = sorted(term for term in query_terms if term in set(tokenize(record_to_search_text(record))))
    matched_fields: list[str] = []
    for field in (
        "title",
        "purpose",
        "summary",
        "keywords",
        "aliases",
        "key_concepts",
        "related_objects",
        "related_fields",
        "related_metadata",
        "business_rules",
        "content_excerpt",
    ):
        value = record.get(field)
        if not value:
            continue
        text = " ".join(str(item) for item in value) if isinstance(value, list) else str(value)
        if query_terms.intersection(tokenize(text)):
            matched_fields.append(field)
    return {"matched_terms": matched_terms, "matched_fields": matched_fields}


def _value(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if value is None or value == "":
        return "unknown"
    return str(value)


def _list_text(value: Any) -> str:
    if isinstance(value, list):
        items = [str(item) for item in value if str(item).strip()]
        return ", ".join(items) if items else "none"
    if value:
        return str(value)
    return "none"


def _clip(value: str, limit: int) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text or "unknown"
    return text[: limit - 3].rstrip() + "..."


if __name__ == "__main__":
    raise SystemExit(main())
