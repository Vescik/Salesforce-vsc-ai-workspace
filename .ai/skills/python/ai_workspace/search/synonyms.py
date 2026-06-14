"""Query expansion against a hand-curated synonym map.

The synonym map lives at ``.ai/config/search-synonyms.yaml`` (upstreamed to the
KB repo per ADR-002). It maps a canonical term to one or more alternates::

    invoice:
      - kmbi__Invoice__c
      - billing

Expansion is additive: the original query terms are preserved and matched
synonyms are appended. Lookup is case-insensitive but synonyms are emitted with
the casing they appear in the YAML (so API names like ``kmbi__Invoice__c``
survive intact for downstream BM25 tokenization).
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from ai_workspace.security.redactor import load_simple_yaml


DEFAULT_SYNONYMS_PATH = Path(".ai/config/search-synonyms.yaml")
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


@lru_cache(maxsize=8)
def load_synonyms(path: str | None = None) -> dict[str, tuple[str, ...]]:
    """Load and cache the synonym map. Returns lowercase keys → tuple of synonyms."""

    target = Path(path) if path else DEFAULT_SYNONYMS_PATH
    if not target.exists():
        return {}
    try:
        loaded = load_simple_yaml(str(target))
    except Exception:  # noqa: BLE001 - search should keep working with an empty map
        return {}
    if not isinstance(loaded, dict):
        return {}
    result: dict[str, tuple[str, ...]] = {}
    for key, value in loaded.items():
        if not isinstance(key, str):
            continue
        if isinstance(value, list):
            values = tuple(str(item) for item in value if str(item).strip())
        elif isinstance(value, str):
            values = (value,)
        else:
            continue
        if values:
            result[_unquote(key).strip().lower()] = values
    return result


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def expand_query(query: str, synonyms: dict[str, tuple[str, ...]] | None = None) -> str:
    """Append synonyms for any matching tokens or quoted phrases to the query."""

    if not query.strip():
        return query
    table = synonyms if synonyms is not None else load_synonyms()
    if not table:
        return query
    tokens = _TOKEN_RE.findall(query.lower())
    additions: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        for replacement in table.get(token, ()):
            if replacement.lower() in seen:
                continue
            seen.add(replacement.lower())
            additions.append(replacement)
    # Phrase-level lookup ("invoice approval" → process names)
    for phrase, values in table.items():
        if " " in phrase and phrase in query.lower():
            for replacement in values:
                if replacement.lower() in seen:
                    continue
                seen.add(replacement.lower())
                additions.append(replacement)
    if not additions:
        return query
    return query + " " + " ".join(additions)


def expand_terms(terms: Iterable[str], synonyms: dict[str, tuple[str, ...]] | None = None) -> list[str]:
    """Return tokens plus expanded synonyms (deduplicated, lowercased for matching)."""

    table = synonyms if synonyms is not None else load_synonyms()
    out: list[str] = []
    seen: set[str] = set()
    for term in terms:
        lowered = term.lower()
        if lowered and lowered not in seen:
            seen.add(lowered)
            out.append(lowered)
        for replacement in table.get(lowered, ()):
            r_lower = replacement.lower()
            if r_lower not in seen:
                seen.add(r_lower)
                out.append(r_lower)
    return out


__all__ = ["load_synonyms", "expand_query", "expand_terms"]
