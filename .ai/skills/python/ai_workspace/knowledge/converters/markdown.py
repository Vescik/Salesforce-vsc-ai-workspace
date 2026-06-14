"""Markdown converter.

Uses ``markdown-it-py`` when available for accurate AST-based parsing of
headings, tables, and fenced code blocks. Falls back to a stdlib heuristic
parser when the extra is missing so the workspace still functions without
``salesforce-ai-workspace-tools[knowledge]`` installed.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ai_workspace.knowledge.converters import make_doc


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_FENCE_RE = re.compile(r"^([`~]{3,})\s*([A-Za-z0-9_+\-]*)\s*$")
_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")


def convert(path: Path | str) -> dict[str, Any]:
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = source.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return make_doc("md", source, warnings=[f"Could not read markdown: {exc}"], parse_status="failed")

    try:
        from markdown_it import MarkdownIt  # type: ignore
    except ImportError:
        return _heuristic_convert(source, text, degraded=True)

    return _markdown_it_convert(source, text, MarkdownIt)


def _markdown_it_convert(source: Path, text: str, MarkdownIt: Any) -> dict[str, Any]:
    md = MarkdownIt("commonmark", {"html": False}).enable("table").enable("strikethrough")
    tokens = md.parse(text)
    sections: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    code_blocks: list[dict[str, Any]] = []
    current_heading = source.stem
    current_level = 1
    current_body: list[str] = []
    anchors: list[str] = []

    def flush() -> None:
        body = "\n".join(current_body).strip()
        if body or current_heading:
            sections.append({
                "heading": current_heading,
                "level": current_level,
                "body": body,
                "anchors": list(anchors),
            })

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == "heading_open":
            flush()
            current_body = []
            anchors = []
            current_level = int(tok.tag[1:]) if tok.tag.startswith("h") else 1
            inline = tokens[i + 1] if i + 1 < len(tokens) else None
            current_heading = (inline.content if inline and inline.type == "inline" else "").strip() or source.stem
            i += 3  # skip heading_open, inline, heading_close
            continue
        if tok.type == "fence":
            code_blocks.append({"lang": tok.info.strip() or "", "text": tok.content})
            current_body.append(tok.content.strip())
            i += 1
            continue
        if tok.type == "table_open":
            rows, consumed = _consume_table(tokens, i)
            if rows:
                tables.append({"caption": current_heading, "rows": rows})
                current_body.append("\n".join(" | ".join(r) for r in rows))
            i = consumed
            continue
        if tok.type == "inline":
            current_body.append(tok.content)
        i += 1
    flush()

    return make_doc(
        "md",
        source,
        sections=sections,
        tables=tables,
        code_blocks=code_blocks,
        metadata={"library": "markdown-it-py"},
        parse_status="ok",
        degraded=False,
    )


def _consume_table(tokens: list[Any], start: int) -> tuple[list[list[str]], int]:
    rows: list[list[str]] = []
    current_row: list[str] = []
    i = start
    while i < len(tokens):
        t = tokens[i]
        if t.type == "table_close":
            return rows, i + 1
        if t.type in {"tr_open"}:
            current_row = []
        elif t.type in {"th_open", "td_open"}:
            inline = tokens[i + 1] if i + 1 < len(tokens) else None
            current_row.append((inline.content if inline and inline.type == "inline" else "").strip())
        elif t.type in {"tr_close"}:
            if current_row:
                rows.append(current_row)
        i += 1
    return rows, i


def _heuristic_convert(source: Path, text: str, *, degraded: bool) -> dict[str, Any]:
    """Stdlib-only fallback parser: regex-based headings/tables/fences."""

    warnings: list[str] = []
    if degraded:
        warnings.append("markdown-it-py not installed; using heuristic Markdown parser.")
    sections: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    code_blocks: list[dict[str, Any]] = []
    current_heading = source.stem
    current_level = 1
    current_body: list[str] = []
    in_fence = False
    fence_marker = ""
    fence_lang = ""
    fence_buf: list[str] = []
    pending_table_header: list[str] | None = None
    pending_table_rows: list[list[str]] = []

    def flush_section() -> None:
        body = "\n".join(current_body).strip()
        if body or current_heading:
            sections.append({
                "heading": current_heading,
                "level": current_level,
                "body": body,
                "anchors": [],
            })

    def flush_table() -> None:
        nonlocal pending_table_header, pending_table_rows
        if pending_table_header is not None:
            rows = [pending_table_header] + pending_table_rows
            tables.append({"caption": current_heading, "rows": rows})
            current_body.append("\n".join(" | ".join(r) for r in rows))
        pending_table_header = None
        pending_table_rows = []

    lines = text.splitlines()
    n = len(lines)
    for idx in range(n):
        line = lines[idx]
        if in_fence:
            if line.startswith(fence_marker) and line.strip() == fence_marker:
                code_blocks.append({"lang": fence_lang, "text": "\n".join(fence_buf)})
                current_body.append("\n".join(fence_buf))
                fence_buf = []
                fence_lang = ""
                fence_marker = ""
                in_fence = False
                continue
            fence_buf.append(line)
            continue
        fence_match = _FENCE_RE.match(line)
        if fence_match:
            flush_table()
            in_fence = True
            fence_marker = fence_match.group(1)
            fence_lang = (fence_match.group(2) or "").strip()
            fence_buf = []
            continue
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            flush_table()
            flush_section()
            current_heading = heading_match.group(2).strip() or source.stem
            current_level = len(heading_match.group(1))
            current_body = []
            continue
        if "|" in line and idx + 1 < n and _TABLE_SEPARATOR_RE.match(lines[idx + 1]):
            pending_table_header = _split_table_row(line)
            pending_table_rows = []
            continue
        if pending_table_header is not None:
            if _TABLE_SEPARATOR_RE.match(line):
                continue
            if "|" in line and line.strip():
                pending_table_rows.append(_split_table_row(line))
                continue
            flush_table()
        current_body.append(line)
    flush_table()
    flush_section()

    return make_doc(
        "md",
        source,
        sections=sections,
        tables=tables,
        code_blocks=code_blocks,
        metadata={"library": "stdlib-heuristic"},
        warnings=warnings,
        parse_status="partial" if degraded else "ok",
        degraded=degraded,
    )


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]
