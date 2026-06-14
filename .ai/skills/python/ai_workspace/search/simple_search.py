"""Standard-library search helpers for local AI context indexes.

Phase 2 adds:
- BM25 scoring (``score_record_bm25``) with corpus stats cached at
  ``.ai/context/index/_search-stats.json``.
- A ``mode`` kwarg on ``score_record`` and ``search_jsonl`` (default
  ``"legacy"``) so every current caller works unchanged. Callers can opt in
  with ``mode="bm25"`` once the corpus stats are built.
- Tie-break by knowledge quality (status → confidence → recency) when scores
  are within 0.001 of each other.

Synonym expansion is opt-in via the ``synonyms`` flag on ``search_jsonl`` —
loaded from ``.ai/config/search-synonyms.yaml`` (see ``search.synonyms``).
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Any

from ai_workspace.search.ranking import (
    confidence_rank,
    recency_negative_days,
    status_rank,
)


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
    # knowledge card fields
    "title",
    "keywords",
    "domain",
    "related_objects",
    "related_config_objects",
    "related_processes",
    "summary",
}

DEFAULT_CORPUS_STATS_PATH = Path(".ai/context/index/_search-stats.json")
_BM25_K1 = 1.5
_BM25_B = 0.75
_TIE_BREAK_EPSILON = 0.001


def tokenize(text: str) -> list[str]:
    """Tokenize text case-insensitively into stable terms."""

    return TOKEN_RE.findall(text.lower())


def score_record(
    record: dict[str, Any],
    query_terms: list[str],
    *,
    mode: str = "legacy",
    corpus_stats: dict[str, Any] | None = None,
) -> float:
    """Score a record by token overlap (legacy) or BM25.

    ``mode`` defaults to ``"legacy"`` so every existing caller keeps its current
    behavior. Pass ``mode="bm25"`` with ``corpus_stats`` to get BM25 scoring.
    """

    if mode == "bm25":
        return score_record_bm25(record, query_terms, corpus_stats or {})
    return _score_record_legacy(record, query_terms)


def _score_record_legacy(record: dict[str, Any], query_terms: list[str]) -> float:
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


def score_record_bm25(
    record: dict[str, Any],
    query_terms: list[str],
    corpus_stats: dict[str, Any],
) -> float:
    """Classical BM25 (k1=1.5, b=0.75) using cached corpus IDF."""

    if not query_terms or not corpus_stats:
        return 0.0
    idf: dict[str, float] = corpus_stats.get("idf") or {}
    avg_dl: float = float(corpus_stats.get("avg_dl") or 1.0)
    body_tokens = tokenize(record_to_search_text(record))
    important_tokens = tokenize(_important_text(record))
    weighted = body_tokens + important_tokens * 2  # cheap field boost
    if not weighted:
        return 0.0
    dl = len(weighted)
    tf: dict[str, int] = {}
    for token in weighted:
        tf[token] = tf.get(token, 0) + 1
    score = 0.0
    for term in query_terms:
        t = term.lower()
        term_idf = idf.get(t)
        if term_idf is None:
            continue
        f = tf.get(t, 0)
        if f == 0:
            continue
        norm = 1.0 - _BM25_B + _BM25_B * (dl / avg_dl if avg_dl else 1.0)
        score += term_idf * ((f * (_BM25_K1 + 1)) / (f + _BM25_K1 * norm))
    parse_status = str(record.get("parse_status") or "").lower()
    if parse_status == "failed":
        score *= 0.25
    return round(score, 4)


def search_jsonl(
    path: str,
    query: str,
    limit: int,
    *,
    mode: str = "legacy",
    synonyms: dict[str, tuple[str, ...]] | None = None,
    corpus_stats: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Search a JSONL file and return top matching records.

    Pass ``mode="bm25"`` for BM25 ranking (will lazy-build corpus stats from
    ``path`` if ``corpus_stats`` is None). Pass ``synonyms`` (or rely on the
    default ``.ai/config/search-synonyms.yaml``) to expand the query.
    """

    if limit < 1:
        return []
    source = Path(path)
    if not source.exists():
        return []

    expanded_query = _expand_query_lazy(query, synonyms)
    query_terms = tokenize(expanded_query)
    stats = corpus_stats if corpus_stats is not None else (load_or_build_corpus_stats(source) if mode == "bm25" else None)

    records: list[dict[str, Any]] = []
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
            score = score_record(loaded, query_terms, mode=mode, corpus_stats=stats)
            if score <= 0:
                continue
            result = dict(loaded)
            result["_search_score"] = score
            records.append(result)

    records.sort(key=_result_sort_key)
    return records[:limit]


def _result_sort_key(record: dict[str, Any]) -> tuple[float, int, int, float, str]:
    """Composite sort key: score desc, then quality, then recency, then stable id.

    BM25 + legacy scores have continuous spread; we bucket by ``round(score, 3)``
    so near-ties (within ``_TIE_BREAK_EPSILON``) collapse and the quality / recency
    tie-breakers actually kick in.
    """

    score = float(record.get("_search_score", 0))
    bucketed = -round(score / _TIE_BREAK_EPSILON) * _TIE_BREAK_EPSILON
    return (
        bucketed,
        status_rank(record),
        confidence_rank(record),
        recency_negative_days(record),
        _stable_sort_key(record),
    )


def build_corpus_stats(jsonl_path: Path) -> dict[str, Any]:
    """Walk a JSONL once and compute IDF + average document length for BM25."""

    if not jsonl_path.exists():
        return {"n_docs": 0, "avg_dl": 0.0, "idf": {}}
    n_docs = 0
    total_tokens = 0
    df: dict[str, int] = {}
    with jsonl_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                loaded = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(loaded, dict):
                continue
            n_docs += 1
            tokens = tokenize(record_to_search_text(loaded))
            tokens += tokenize(_important_text(loaded))
            total_tokens += len(tokens)
            for term in set(tokens):
                df[term] = df.get(term, 0) + 1
    avg_dl = total_tokens / n_docs if n_docs else 0.0
    idf: dict[str, float] = {}
    for term, frequency in df.items():
        # BM25+ style smoothed IDF: log(1 + (N - n + 0.5) / (n + 0.5)).
        idf[term] = math.log(1 + (n_docs - frequency + 0.5) / (frequency + 0.5))
    return {"n_docs": n_docs, "avg_dl": avg_dl, "idf": idf}


def load_or_build_corpus_stats(
    jsonl_path: Path,
    cache_path: Path | None = None,
) -> dict[str, Any]:
    """Return cached corpus stats for ``jsonl_path``, building+caching on miss."""

    cache = cache_path or DEFAULT_CORPUS_STATS_PATH
    cache_key = jsonl_path.as_posix()
    try:
        if cache.exists():
            payload = json.loads(cache.read_text(encoding="utf-8"))
            entry = (payload.get("by_index") or {}).get(cache_key)
            if entry and _stats_fresh(entry, jsonl_path):
                return entry["stats"]
    except (OSError, json.JSONDecodeError):
        pass

    stats = build_corpus_stats(jsonl_path)
    try:
        payload = {}
        if cache.exists():
            try:
                payload = json.loads(cache.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payload = {}
        by_index = payload.get("by_index") or {}
        by_index[cache_key] = {
            "mtime_ns": _safe_mtime(jsonl_path),
            "stats": stats,
        }
        payload["by_index"] = by_index
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(payload, ensure_ascii=True, sort_keys=True), encoding="utf-8")
    except OSError:
        pass
    return stats


def _stats_fresh(entry: dict[str, Any], jsonl_path: Path) -> bool:
    return int(entry.get("mtime_ns") or 0) == _safe_mtime(jsonl_path)


def _safe_mtime(path: Path) -> int:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return 0


def _expand_query_lazy(query: str, synonyms: dict[str, tuple[str, ...]] | None) -> str:
    if synonyms is False:  # type: ignore[comparison-overlap]
        return query
    from ai_workspace.search.synonyms import expand_query

    return expand_query(query, synonyms)


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
        if value is None:
            continue
        if isinstance(value, list):
            values.extend(str(item) for item in value if str(item).strip())
        else:
            values.append(str(value))
    return " ".join(values)


def _stable_sort_key(record: dict[str, Any]) -> str:
    for key in ("full_name", "api_name", "object_api_name", "field_api_name", "record_key", "path"):
        value = record.get(key)
        if value:
            return str(value)
    return json.dumps(record, ensure_ascii=True, sort_keys=True)
