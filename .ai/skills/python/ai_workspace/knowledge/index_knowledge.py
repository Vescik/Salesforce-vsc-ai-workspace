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
LIST_KEYS = {
    "applies_to",
    "usage_context",
    "tags",
    "aliases",
    "key_concepts",
    "related_objects",
    "related_fields",
    "related_config_objects",
    "related_metadata",
    "related_processes",
    "integration_points",
    "dependencies",
    "business_rules",
    "keywords",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Index local internal knowledge notes.")
    parser.add_argument("--knowledge-root", default=".ai/knowledge")
    parser.add_argument("--out", default=".ai/context/index/knowledge-cards.jsonl")
    parser.add_argument("--summary-out", default=".ai/context/index/knowledge-index-summary.json")
    parser.add_argument("--include-draft", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-excerpt-chars", type=int, default=EXCERPT_CHARS)
    parser.add_argument(
        "--emit-index-yaml",
        nargs="?",
        const=".ai/context/index/knowledge-index-files.yaml",
        default=None,
        help="Also emit a machine-maintained YAML index of per-file rows. "
             "When the flag is given without a value, writes to "
             ".ai/context/index/knowledge-index-files.yaml. "
             "Pass an explicit path to write elsewhere (e.g. .ai/knowledge/index.yaml when "
             "regenerating the upstream Vescik/Salesforce-knowledge-base file).",
    )
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

    if args.emit_index_yaml:
        index_yaml_path = Path(args.emit_index_yaml)
        ensure_parent_dir(index_yaml_path)
        index_yaml_path.write_text(
            _render_index_yaml(records, knowledge_root, args.knowledge_root),
            encoding="utf-8",
        )
        print(f"Wrote index YAML to {index_yaml_path}")
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
        "source_format": str(metadata.get("source_format") or ""),
        "source_checksum": str(metadata.get("source_checksum") or ""),
        "purpose": str(metadata.get("purpose") or ""),
        "owner": str(metadata.get("owner") or ""),
        "status": str(metadata.get("status") or ""),
        "confidence": str(metadata.get("confidence") or ""),
        "last_reviewed": str(metadata.get("last_reviewed") or ""),
        "applies_to": _list_value(metadata.get("applies_to")),
        "usage_context": _list_value(metadata.get("usage_context")),
        "tags": _list_value(metadata.get("tags")),
        "aliases": _list_value(metadata.get("aliases")),
        "key_concepts": _list_value(metadata.get("key_concepts")),
        "keywords": _list_value(metadata.get("keywords")),
        "related_objects": _list_value(metadata.get("related_objects")),
        "related_fields": _list_value(metadata.get("related_fields")),
        "related_config_objects": _list_value(metadata.get("related_config_objects")),
        "related_metadata": _list_value(metadata.get("related_metadata")),
        "related_processes": _list_value(metadata.get("related_processes")),
        "integration_points": _list_value(metadata.get("integration_points")),
        "dependencies": _list_value(metadata.get("dependencies")),
        "business_rules": _list_value(metadata.get("business_rules")),
        "headings": headings,
        "summary": summary,
        "weighted_terms": _weighted_terms(metadata, body),
        "content_excerpt": _section_aware_excerpt(body, max_excerpt_chars),
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
    if _looks_v2(metadata):
        if not str(metadata.get("purpose") or "").strip():
            flags.add("missing_purpose")
        if not _list_value(metadata.get("keywords")):
            flags.add("missing_keywords")
        if not str(metadata.get("source_file") or "").strip():
            flags.add("missing_source_file")
        semantic_values = []
        for key in ("key_concepts", "related_objects", "related_fields", "related_metadata", "business_rules"):
            semantic_values.extend(_list_value(metadata.get(key)))
        if not semantic_values:
            flags.add("missing_semantic_fields")
    return sorted(flags)


def _looks_v2(metadata: dict[str, Any]) -> bool:
    return any(
        key in metadata
        for key in (
            "purpose",
            "source_checksum",
            "source_format",
            "usage_context",
            "aliases",
            "key_concepts",
            "related_fields",
            "related_metadata",
            "business_rules",
        )
    )


def _weighted_terms(metadata: dict[str, Any], body: str) -> list[str]:
    terms: list[str] = []
    for key in (
        "title",
        "purpose",
        "domain",
        "usage_context",
        "tags",
        "aliases",
        "key_concepts",
        "keywords",
        "related_objects",
        "related_fields",
        "related_config_objects",
        "related_metadata",
        "related_processes",
        "integration_points",
        "dependencies",
        "business_rules",
    ):
        value = metadata.get(key)
        if isinstance(value, list):
            terms.extend(str(item) for item in value if str(item).strip())
        elif value:
            terms.append(str(value))
    for heading in _headings(body):
        terms.append(heading)
    seen: set[str] = set()
    out: list[str] = []
    for term in terms:
        clean = normalize_whitespace(term)
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            out.append(clean)
    return out


def _section_aware_excerpt(body: str, max_chars: int) -> str:
    """Return up to max_chars covering the preamble + first N chars of each heading section."""
    normalized = normalize_whitespace(body)
    if len(normalized) <= max_chars:
        return normalized
    section_re = re.compile(r"(?m)^(#{1,2} .+)$")
    parts = section_re.split(normalized)
    result: list[str] = []
    budget = max_chars
    preamble = parts[0].strip()
    if preamble:
        chunk = preamble[:budget]
        result.append(chunk)
        budget -= len(chunk)
    section_preview = 400
    for i in range(1, len(parts) - 1, 2):
        if budget <= 0:
            break
        heading = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        section_text = f"\n{heading}\n{content[:section_preview]}"
        chunk = section_text[:budget]
        result.append(chunk)
        budget -= len(chunk)
    return "\n".join(result).strip()


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
    return (datetime.now(timezone.utc).date() - reviewed).days > 180


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


def _render_index_yaml(records: list[dict[str, Any]], knowledge_root: Path, knowledge_root_str: str) -> str:
    """Render per-file rows grouped by domain into a YAML index.

    The file is machine-maintained — header marks it and the rendered shape is
    stable so callers can detect drift by diff. Source repo (per ADR-002) keeps
    hand-curated top-level fields; this output augments domain entries with a
    ``files:`` list.
    """

    by_domain: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        domain = str(record.get("domain") or "general") or "general"
        by_domain.setdefault(domain, []).append(record)

    lines: list[str] = []
    lines.append("# Generated by ai_workspace.knowledge.index_knowledge --emit-index-yaml — do not edit by hand.")
    lines.append("# Per-file rows reflect what knowledge_search and the MCP knowledge_get tool will resolve.")
    lines.append(f"# Source knowledge root: {knowledge_root_str}")
    lines.append("generated_at: " + json.dumps(datetime.now(timezone.utc).isoformat()))
    lines.append(f"file_count: {sum(len(v) for v in by_domain.values())}")
    lines.append("domains:")
    for domain in sorted(by_domain):
        domain_records = sorted(by_domain[domain], key=lambda r: (str(r.get("path") or ""), str(r.get("title") or "")))
        lines.append(f"  {_yaml_key(domain)}:")
        lines.append(f"    file_count: {len(domain_records)}")
        lines.append("    files:")
        for record in domain_records:
            slug = _slug_from_path(record)
            lines.append(f"      - slug: {_yaml_string(slug)}")
            lines.append(f"        path: {_yaml_string(record.get('path'))}")
            lines.append(f"        title: {_yaml_string(record.get('title'))}")
            lines.append(f"        status: {_yaml_string(record.get('status'))}")
            lines.append(f"        confidence: {_yaml_string(record.get('confidence'))}")
            lines.append(f"        last_reviewed: {_yaml_string(record.get('last_reviewed'))}")
            lines.append(f"        source_type: {_yaml_string(record.get('source_type'))}")
            lines.append(f"        related_objects: {_yaml_flow_list(record.get('related_objects'))}")
            lines.append(f"        related_fields: {_yaml_flow_list(record.get('related_fields'))}")
            lines.append(f"        related_config_objects: {_yaml_flow_list(record.get('related_config_objects'))}")
            lines.append(f"        related_metadata: {_yaml_flow_list(record.get('related_metadata'))}")
            lines.append(f"        related_processes: {_yaml_flow_list(record.get('related_processes'))}")
            lines.append(f"        usage_context: {_yaml_flow_list(record.get('usage_context'))}")
            lines.append(f"        keywords: {_yaml_flow_list(record.get('keywords'))}")
            risk_flags = record.get("risk_flags") if isinstance(record.get("risk_flags"), list) else []
            if risk_flags:
                lines.append(f"        risk_flags: {_yaml_flow_list(risk_flags)}")
    return "\n".join(lines) + "\n"


def _yaml_key(value: str) -> str:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", value):
        return value
    return json.dumps(value, ensure_ascii=True)


def _yaml_string(value: Any) -> str:
    return json.dumps(str(value or ""), ensure_ascii=True)


def _yaml_flow_list(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "[]"
    return "[" + ", ".join(json.dumps(str(item), ensure_ascii=True) for item in value) + "]"


def _slug_from_path(record: dict[str, Any]) -> str:
    path = str(record.get("path") or "")
    if not path:
        title = str(record.get("title") or "")
        return re.sub(r"[^A-Za-z0-9_-]+", "-", title.strip().lower()).strip("-")
    return Path(path).stem


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
