"""Search local internal knowledge cards."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ai_workspace.search.simple_search import search_jsonl


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


def search_knowledge(query: str, index_path: str | Path, top_k: int = 10) -> list[dict[str, Any]]:
    return search_jsonl(str(index_path), query, max(1, top_k))


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
        "related_objects": record.get("related_objects") or [],
        "related_config_objects": record.get("related_config_objects") or [],
        "related_processes": record.get("related_processes") or [],
        "risk_flags": record.get("risk_flags") or [],
        "score": record.get("_search_score"),
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
        lines.append(f"  - Related objects: {_list_text(record.get('related_objects'))}")
        lines.append(f"  - Related config objects: {_list_text(record.get('related_config_objects'))}")
        lines.append(f"  - Related processes: {_list_text(record.get('related_processes'))}")
        lines.append(f"  - Risk flags: {_list_text(record.get('risk_flags'))}")
        lines.append(f"  - Score: {_value(record, 'score')}")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search internal knowledge cards.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--index", default=".ai/context/index/knowledge-cards.jsonl")
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args(argv)
    results = [record_to_knowledge_context(record) for record in search_knowledge(args.query, args.index, args.top_k)]
    print(results_to_markdown(args.query, results), end="")
    return 0


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
