"""Index curated internal knowledge notes into JSON Lines cards."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from ai_workspace.knowledge.import_knowledge import detect_sensitive_content
from ai_workspace.knowledge.parse_documents import normalize_whitespace
from ai_workspace.utils.io import ensure_parent_dir, write_jsonl


EXCERPT_CHARS = 2000
SKIP_DIRS = {"archive", "imports"}
LIST_KEYS = {"applies_to", "related_objects", "related_config_objects", "related_processes", "keywords"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Index local internal knowledge notes.")
    parser.add_argument("--knowledge-root", default=".ai/knowledge")
    parser.add_argument("--out", default=".ai/context/index/knowledge-cards.jsonl")
    parser.add_argument("--summary-out", default=".ai/context/index/knowledge-index-summary.json")
    parser.add_argument("--include-draft", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-excerpt-chars", type=int, default=EXCERPT_CHARS)
    args = parser.parse_args(argv)

    knowledge_root = Path(args.knowledge_root)
    out_path = Path(args.out)
    records = build_knowledge_index(
        knowledge_root,
        include_draft=args.include_draft,
        max_excerpt_chars=args.max_excerpt_chars,
    )
    write_jsonl(out_path, records)
    summary_path = Path(args.summary_out)
    ensure_parent_dir(summary_path)
    total_files = len(_knowledge_markdown_files(knowledge_root)) if knowledge_root.exists() else 0
    summary_path.write_text(
        json.dumps(
            _summary(records, knowledge_root, out_path, total_files=total_files),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(records)} knowledge card(s) to {out_path}")
    print(f"Wrote summary to {summary_path}")
    return 0


def build_knowledge_index(
    knowledge_root: Path,
    include_draft: bool = True,
    max_excerpt_chars: int = EXCERPT_CHARS,
) -> list[dict[str, Any]]:
    """Build knowledge cards from markdown notes under knowledge_root."""

    if not knowledge_root.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in _knowledge_markdown_files(knowledge_root):
        record = parse_knowledge_note(path, knowledge_root, max_excerpt_chars=max_excerpt_chars)
        if not include_draft and str(record.get("status") or "").lower() == "draft":
            continue
        records.append(record)
    records.sort(key=lambda item: (str(item.get("domain")), str(item.get("path")), str(item.get("title"))))
    return records


def parse_knowledge_note(path: Path, knowledge_root: Path, max_excerpt_chars: int = EXCERPT_CHARS) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    metadata, body, has_front_matter = _parse_front_matter(text)
    headings = _headings(body)
    summary = _summary_from_body(body)
    relative_path = _card_path(path, knowledge_root)
    return {
        "card_type": "knowledge_note",
        "title": str(metadata.get("title") or path.stem),
        "domain": str(metadata.get("domain") or _domain_from_path(path, knowledge_root)),
        "path": relative_path,
        "source_type": str(metadata.get("source_type") or ""),
        "source_file": str(metadata.get("source_file") or ""),
        "owner": str(metadata.get("owner") or ""),
        "status": str(metadata.get("status") or ""),
        "confidence": str(metadata.get("confidence") or ""),
        "last_reviewed": str(metadata.get("last_reviewed") or ""),
        "applies_to": _list_value(metadata.get("applies_to")),
        "keywords": _list_value(metadata.get("keywords")),
        "related_objects": _list_value(metadata.get("related_objects")),
        "related_config_objects": _list_value(metadata.get("related_config_objects")),
        "related_processes": _list_value(metadata.get("related_processes")),
        "headings": headings,
        "summary": summary,
        "content_excerpt": normalize_whitespace(body)[:max_excerpt_chars],
        "checksum": hashlib.sha256(normalize_whitespace(text).encode("utf-8")).hexdigest(),
        "risk_flags": _risk_flags(metadata, body, has_front_matter),
    }


def _parse_front_matter(text: str) -> tuple[dict[str, Any], str, bool]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, False
    metadata: dict[str, Any] = {}
    current_list_key: str | None = None
    end_index = 0
    for index, raw in enumerate(lines[1:], start=1):
        line = raw.rstrip()
        if line.strip() == "---":
            end_index = index
            break
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and current_list_key:
            metadata.setdefault(current_list_key, []).append(_parse_scalar(stripped[2:].strip()))
            continue
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "" and key in LIST_KEYS:
                metadata[key] = []
                current_list_key = key
            else:
                metadata[key] = _parse_scalar(value)
                current_list_key = None
    body = "\n".join(lines[end_index + 1 :]) if end_index else text
    return metadata, body, bool(end_index)


def _risk_flags(metadata: dict[str, Any], body: str, has_front_matter: bool) -> list[str]:
    flags: set[str] = set()
    if not has_front_matter:
        flags.add("missing_front_matter")
    status = str(metadata.get("status") or "").lower()
    confidence = str(metadata.get("confidence") or "").lower()
    if status == "draft":
        flags.add("draft_status")
    if confidence == "low":
        flags.add("low_confidence")
    if not str(metadata.get("owner") or "").strip():
        flags.add("missing_owner")
    if _stale_review(str(metadata.get("last_reviewed") or "")):
        flags.add("stale_review")
    if detect_sensitive_content(body):
        flags.add("possible_secret")
    return sorted(flags)


def _knowledge_markdown_files(knowledge_root: Path) -> list[Path]:
    return [
        path
        for path in sorted(knowledge_root.rglob("*.md"), key=lambda item: item.as_posix())
        if not _should_skip(path, knowledge_root)
    ]


def _stale_review(value: str) -> bool:
    if not value or value == "YYYY-MM-DD":
        return True
    try:
        reviewed = date.fromisoformat(value[:10])
    except ValueError:
        return True
    return (datetime.now(timezone.utc).date() - reviewed).days > 365


def _should_skip(path: Path, knowledge_root: Path) -> bool:
    if path.name == "README.md":
        return True
    try:
        relative = path.relative_to(knowledge_root)
    except ValueError:
        return True
    return any(part in SKIP_DIRS for part in relative.parts)


def _headings(body: str) -> list[str]:
    return [line.lstrip("#").strip() for line in body.splitlines() if line.startswith("#") and line.lstrip("#").strip()]


def _summary_from_body(body: str) -> str:
    normalized = normalize_whitespace(re.sub(r"^---.*?---", "", body, flags=re.DOTALL))
    paragraphs = [part.strip() for part in normalized.split("\n\n") if part.strip()]
    for paragraph in paragraphs:
        if not paragraph.startswith("#"):
            return paragraph[:500]
    return normalized[:500]


def _domain_from_path(path: Path, knowledge_root: Path) -> str:
    try:
        relative = path.relative_to(knowledge_root)
    except ValueError:
        return "general"
    if len(relative.parts) >= 3 and relative.parts[0] == "domains":
        return relative.parts[1]
    return "general"


def _card_path(path: Path, knowledge_root: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except (FileNotFoundError, ValueError):
        pass
    try:
        return (Path(".ai/knowledge") / path.relative_to(knowledge_root)).as_posix()
    except ValueError:
        return path.as_posix()


def _list_value(value: Any) -> list[str]:
    if isinstance(value, list):
        return sorted(str(item) for item in value if str(item).strip())
    if value:
        return [str(value)]
    return []


def _parse_scalar(value: str) -> Any:
    if value == "[]":
        return []
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _summary(records: list[dict[str, Any]], knowledge_root: Path, out_path: Path, total_files: int) -> dict[str, Any]:
    by_domain: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_confidence: dict[str, int] = {}
    risk_counts: dict[str, int] = {}
    warnings: list[str] = []
    for record in records:
        domain = str(record.get("domain") or "general")
        status = str(record.get("status") or "missing")
        confidence = str(record.get("confidence") or "missing")
        by_domain[domain] = by_domain.get(domain, 0) + 1
        by_status[status] = by_status.get(status, 0) + 1
        by_confidence[confidence] = by_confidence.get(confidence, 0) + 1
        for flag in record.get("risk_flags", []):
            risk_counts[str(flag)] = risk_counts.get(str(flag), 0) + 1
        if record.get("risk_flags"):
            warnings.append(f"{record.get('path')}: {', '.join(record.get('risk_flags', []))}")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "knowledge_root": knowledge_root.as_posix(),
        "out": out_path.as_posix(),
        "total_files": total_files,
        "indexed_cards": len(records),
        "by_domain": by_domain,
        "by_status": by_status,
        "by_confidence": by_confidence,
        "risk_counts": risk_counts,
        "warnings": warnings,
    }


if __name__ == "__main__":
    raise SystemExit(main())
