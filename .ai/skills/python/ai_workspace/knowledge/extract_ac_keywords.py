"""Extract a short, IDF-weighted keyword list from a Work Item's AC + description.

Reads ``.ai/context/work-items/<WI>/acceptance-criteria.md`` (preferred) and the
``description`` field of ``ado-work-item.json`` (fallback / supplement). Tokens
are lower-cased, stop-words removed, synonyms expanded, and the top-N ranked by
IDF from the cached corpus stats at ``.ai/context/index/_search-stats.json``.

The resulting keyword list seeds ``build_context_pack`` so step (b) of the
solution-design workflow becomes implicit::

    make ai-context WORK_ITEM=KIM-1234 QUERY="$(python -m ai_workspace.knowledge.extract_ac_keywords --work-item KIM-1234 --print)"
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from ai_workspace.knowledge.index_knowledge import _parse_front_matter as _parse_yaml_fm
from ai_workspace.search.simple_search import (
    DEFAULT_CORPUS_STATS_PATH,
    load_or_build_corpus_stats,
    tokenize,
)
from ai_workspace.search.synonyms import expand_terms


DEFAULT_KNOWLEDGE_INDEX = Path(".ai/context/index/knowledge-cards.jsonl")
DEFAULT_STOPWORDS = Path(".ai/skills/python/ai_workspace/search/stopwords.txt")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract IDF-ranked AC keywords for a Work Item.")
    parser.add_argument("--work-item", required=True)
    parser.add_argument("--work-item-dir")
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--knowledge-index", default=str(DEFAULT_KNOWLEDGE_INDEX))
    parser.add_argument("--stopwords", default=str(DEFAULT_STOPWORDS))
    parser.add_argument("--out", help="Write JSON output to this path.")
    parser.add_argument("--print", action="store_true", help="Print keywords as a space-separated query string and exit.")
    args = parser.parse_args(argv)

    work_item_dir = Path(args.work_item_dir or f".ai/context/work-items/{args.work_item}")
    text_blob = _gather_text(work_item_dir)
    if not text_blob.strip():
        print(f"WARNING: no AC text found in {work_item_dir}")
    stopwords = _load_stopwords(Path(args.stopwords))
    keywords = rank_keywords(
        text_blob,
        knowledge_index=Path(args.knowledge_index),
        stopwords=stopwords,
        top=args.top,
    )

    if args.print:
        print(" ".join(keywords))
        return 0

    payload = {
        "work_item": args.work_item,
        "sources": _source_list(work_item_dir),
        "top": args.top,
        "keywords": keywords,
    }
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Wrote {out_path}")
    print(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


def rank_keywords(
    text: str,
    *,
    knowledge_index: Path,
    stopwords: set[str],
    top: int,
) -> list[str]:
    """Return up to ``top`` IDF-ranked keywords with synonyms folded in."""

    if not text.strip():
        return []
    raw_tokens = [token for token in tokenize(text) if len(token) > 1 and token not in stopwords]
    expanded = expand_terms(raw_tokens)
    expanded = [token for token in expanded if token not in stopwords]
    if not expanded:
        return []
    stats = load_or_build_corpus_stats(knowledge_index)
    idf: dict[str, float] = (stats.get("idf") or {}) if isinstance(stats, dict) else {}
    default_idf = max((value for value in idf.values()), default=1.0) if idf else 1.0

    scored: dict[str, float] = {}
    for token in expanded:
        if token in scored:
            continue
        scored[token] = idf.get(token, default_idf)

    sorted_tokens = sorted(scored.items(), key=lambda kv: (-kv[1], kv[0]))
    return [token for token, _score in sorted_tokens[: max(top, 1)]]


def _gather_text(work_item_dir: Path) -> str:
    parts: list[str] = []
    ac_path = work_item_dir / "acceptance-criteria.md"
    if ac_path.exists():
        parts.append(ac_path.read_text(encoding="utf-8", errors="replace"))
    summary_path = work_item_dir / "work-item-summary.md"
    if summary_path.exists():
        parts.append(_extract_ac_section(summary_path.read_text(encoding="utf-8", errors="replace")))
    ado_path = work_item_dir / "ado-work-item.json"
    if ado_path.exists():
        try:
            ado_payload = json.loads(ado_path.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            ado_payload = {}
        if isinstance(ado_payload, dict):
            for key in ("title", "description", "acceptance_criteria", "summary"):
                value = ado_payload.get(key)
                if isinstance(value, str):
                    parts.append(value)
                elif isinstance(value, list):
                    parts.extend(str(item) for item in value if str(item).strip())
    return "\n\n".join(part for part in parts if part.strip())


def _extract_ac_section(text: str) -> str:
    """Return the Acceptance Criteria section of a work-item-summary.md, if present."""

    sections = re.split(r"(?m)^## +", text)
    for section in sections:
        head, _, body = section.partition("\n")
        if "acceptance" in head.lower() and "criter" in head.lower():
            return body
    return ""


def _load_stopwords(path: Path) -> set[str]:
    if not path.exists():
        return set()
    words: set[str] = set()
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        words.add(line.lower())
    return words


def _source_list(work_item_dir: Path) -> list[str]:
    sources: list[str] = []
    for name in ("acceptance-criteria.md", "work-item-summary.md", "ado-work-item.json"):
        path = work_item_dir / name
        if path.exists():
            sources.append(path.as_posix())
    return sources


if __name__ == "__main__":
    raise SystemExit(main())
