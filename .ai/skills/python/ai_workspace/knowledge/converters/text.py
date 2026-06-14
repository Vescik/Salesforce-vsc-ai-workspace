"""Plain text converter for Knowledge Base Creator 2.0."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ai_workspace.knowledge.converters import make_doc
from ai_workspace.knowledge.parse_documents import normalize_whitespace


HEADING_RE = re.compile(r"^\s*(?:#{1,6}\s*)?([A-Z][A-Za-z0-9][A-Za-z0-9 /&().:-]{2,80})\s*$")


def convert(path: Path | str) -> dict[str, Any]:
    source = Path(path)
    warnings: list[str] = []
    try:
        text = source.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = source.read_text(encoding="utf-8", errors="replace")
        warnings.append("UTF-8 decode failed; replacement characters were used.")
    except OSError as exc:
        return make_doc("txt", source, warnings=[f"Could not read text file: {exc}"], parse_status="failed")

    sections = _sections_from_text(source, text)
    return make_doc(
        "txt",
        source,
        sections=sections,
        metadata={"line_count": len(text.splitlines())},
        warnings=warnings,
        parse_status="partial" if warnings else "ok",
        degraded=False,
    )


def _sections_from_text(source: Path, text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    sections: list[dict[str, Any]] = []
    heading = source.stem
    body: list[str] = []
    anchor_index = 1

    def flush() -> None:
        nonlocal anchor_index
        normalized = normalize_whitespace("\n".join(body))
        if normalized or heading:
            sections.append(
                {
                    "heading": heading,
                    "level": 1,
                    "body": normalized,
                    "anchors": [f"section-{anchor_index}"],
                }
            )
            anchor_index += 1

    previous_blank = True
    for line in lines:
        stripped = line.strip()
        heading_match = HEADING_RE.match(stripped) if previous_blank else None
        if heading_match and body and len(stripped.split()) <= 8 and not stripped.endswith("."):
            flush()
            heading = heading_match.group(1).strip()
            body = []
            previous_blank = False
            continue
        body.append(line)
        previous_blank = not stripped
    flush()
    return sections
