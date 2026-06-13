"""Standard-library search helpers for local AI context indexes."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
IMPORTANT_KEYS = {
    "name",
    "full_name",
    "path",
    "component_type",
    "api_name",
    "object_api_name",
    "field_api_name",
    "record_key",
    "category",
}


def tokenize(text: str) -> list[str]:
    """Tokenize text case-insensitively into stable terms."""

    return TOKEN_RE.findall(text.lower())


def score_record(record: dict[str, Any], query_terms: list[str]) -> float:
    """Score a record by token overlap and important field matches."""

    if not query_terms:
        return 0.0

    query_set = set(term.lower() for term in query_terms if term)
    search_text = record_to_search_text(record)
    search_text_lower = search_text.lower()
    record_terms = set(tokenize(search_text))
    overlap = query_set.intersection(record_terms)
    score = float(len(overlap))

    important_text = _important_text(record).lower()
    important_terms = set(tokenize(important_text))
    important_overlap = query_set.intersection(important_terms)
    score += 3.0 * len(important_overlap)

    query_phrase = " ".join(query_terms).lower().strip()
    if query_phrase and query_phrase in search_text_lower:
        score += 5.0
    if query_phrase and query_phrase in important_text:
        score += 5.0

    parse_status = str(record.get("parse_status") or "").lower()
    if parse_status == "failed":
        score *= 0.25

    return round(score, 4)


def search_jsonl(path: str, query: str, limit: int) -> list[dict[str, Any]]:
    """Search a JSONL file and return top matching records."""

    query_terms = tokenize(query)
    if limit < 1:
        return []

    records: list[dict[str, Any]] = []
    source = Path(path)
    if not source.exists():
        return []

    with source.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                loaded = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"WARNING: could not parse JSONL line {path}:{line_number}: {exc}", file=sys.stderr)
                continue
            if not isinstance(loaded, dict):
                continue
            score = score_record(loaded, query_terms)
            if score <= 0:
                continue
            result = dict(loaded)
            result["_search_score"] = score
            records.append(result)

    records.sort(key=lambda record: (-float(record.get("_search_score", 0)), _stable_sort_key(record)))
    return records[:limit]


def record_to_search_text(record: dict[str, Any]) -> str:
    """Flatten a record into searchable text."""

    values: list[str] = []
    _append_values(record, values)
    return " ".join(values)


def _append_values(value: Any, values: list[str]) -> None:
    if value is None:
        return
    if isinstance(value, (str, int, float, bool)):
        values.append(str(value))
        return
    if isinstance(value, dict):
        for key in sorted(value, key=str):
            values.append(str(key))
            _append_values(value[key], values)
        return
    if isinstance(value, list):
        for item in value:
            _append_values(item, values)


def _important_text(record: dict[str, Any]) -> str:
    values: list[str] = []
    for key in sorted(IMPORTANT_KEYS):
        value = record.get(key)
        if value is not None:
            values.append(str(value))
    return " ".join(values)


def _stable_sort_key(record: dict[str, Any]) -> str:
    for key in ("full_name", "api_name", "object_api_name", "field_api_name", "record_key", "path"):
        value = record.get(key)
        if value:
            return str(value)
    return json.dumps(record, ensure_ascii=True, sort_keys=True)
