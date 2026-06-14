"""Universal document converters that produce a normalized intermediate document.

A NormalizedDocument has this shape (callers may rely on every key being present)::

    {
      "format": "md|pdf|pptx|xlsx|docx|txt|...",
      "source_path": "<repo-relative or absolute path string>",
      "sections": [{"heading": str, "level": int, "body": str, "anchors": [str]}],
      "tables":   [{"caption": str, "rows": [[str, ...]]}],
      "code_blocks": [{"lang": str, "text": str}],
      "metadata": {"author"?: str, "title"?: str, "created"?: str, "modified"?: str, ...},
      "warnings": [str],
      "degraded": bool,
      "parse_status": "ok|partial|failed",
    }

Converters degrade gracefully when their optional dependency from the
``salesforce-ai-workspace-tools[knowledge]`` extras group is missing: they
return a NormalizedDocument with ``degraded=True`` and a warning instead of
raising. Callers (``import_knowledge``, ``validate_knowledge``) are responsible
for redaction and persistence.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


_SUFFIX_TO_FORMAT = {
    ".md": "md",
    ".markdown": "md",
    ".docx": "docx",
    ".pptx": "pptx",
    ".xlsx": "xlsx",
    ".pdf": "pdf",
}


def make_doc(
    fmt: str,
    source_path: Path | str,
    *,
    sections: list[dict[str, Any]] | None = None,
    tables: list[dict[str, Any]] | None = None,
    code_blocks: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    degraded: bool = False,
    parse_status: str = "ok",
) -> dict[str, Any]:
    """Construct a NormalizedDocument dict with all keys populated."""

    return {
        "format": fmt,
        "source_path": str(source_path),
        "sections": list(sections or []),
        "tables": list(tables or []),
        "code_blocks": list(code_blocks or []),
        "metadata": dict(metadata or {}),
        "warnings": list(warnings or []),
        "degraded": bool(degraded),
        "parse_status": parse_status,
    }


def dispatch(path: Path | str) -> dict[str, Any]:
    """Convert a file into a NormalizedDocument based on its suffix.

    Unknown or text-like formats fall back to wrapping ``parse_documents.extract_text``
    into a single-section document so legacy import paths keep working.
    """

    source = Path(path)
    fmt = _SUFFIX_TO_FORMAT.get(source.suffix.lower())
    if fmt == "md":
        from ai_workspace.knowledge.converters import markdown as _markdown
        return _markdown.convert(source)
    if fmt == "docx":
        from ai_workspace.knowledge.converters import docx as _docx
        return _docx.convert(source)
    if fmt == "pptx":
        from ai_workspace.knowledge.converters import pptx as _pptx
        return _pptx.convert(source)
    if fmt == "xlsx":
        from ai_workspace.knowledge.converters import xlsx as _xlsx
        return _xlsx.convert(source)
    if fmt == "pdf":
        from ai_workspace.knowledge.converters import pdf as _pdf
        return _pdf.convert(source)
    return _wrap_extract_text(source)


def _wrap_extract_text(source: Path) -> dict[str, Any]:
    """Wrap the legacy ``parse_documents.extract_text`` into a single-section doc."""

    from ai_workspace.knowledge.parse_documents import detect_format, extract_text

    result = extract_text(source)
    text = str(result.get("text") or "")
    legacy_format = str(result.get("source_format") or detect_format(source))
    warnings = list(result.get("warnings") or [])
    parse_status = str(result.get("parse_status") or "ok")
    sections: list[dict[str, Any]] = []
    if text:
        sections.append({"heading": source.stem, "level": 1, "body": text, "anchors": []})
    return make_doc(
        legacy_format or "unknown",
        source,
        sections=sections,
        warnings=warnings,
        parse_status=parse_status,
        degraded=False,
    )


__all__ = ["dispatch", "make_doc"]
