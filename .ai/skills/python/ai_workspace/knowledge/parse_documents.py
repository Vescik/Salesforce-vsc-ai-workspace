"""Deterministic local document text extraction for internal KB imports."""

from __future__ import annotations

import argparse
import csv
import html.parser
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


TEXT_FORMATS = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "txt",
    ".xml": "xml",
    ".json": "json",
    ".csv": "csv",
    ".yaml": "txt",
    ".yml": "txt",
    ".html": "html",
    ".htm": "html",
    ".pdf": "pdf",
}


def detect_format(path: Path | str) -> str:
    """Return the supported source format for a path."""

    suffix = Path(path).suffix.lower()
    return TEXT_FORMATS.get(suffix, "unknown")


def extract_text(path: Path | str, max_chars: int = 200_000) -> dict[str, Any]:
    """Extract text from a supported document format."""

    source = Path(path)
    source_format = detect_format(source)
    if source_format == "markdown":
        return _limit_result(extract_text_from_markdown(source), max_chars)
    if source_format == "txt":
        return _limit_result(extract_text_from_txt(source), max_chars)
    if source_format == "xml":
        return _limit_result(extract_text_from_xml(source), max_chars)
    if source_format == "json":
        return _limit_result(extract_text_from_json(source), max_chars)
    if source_format == "csv":
        return _limit_result(extract_text_from_csv(source), max_chars)
    if source_format == "html":
        return _limit_result(extract_text_from_html(source), max_chars)
    if source_format == "pdf":
        return _limit_result(extract_text_from_pdf(source), max_chars)
    return {
        "text": "",
        "source_format": "unknown",
        "warnings": [f"Unsupported source format: {source.suffix or '(none)'}"],
        "parse_status": "failed",
    }


def extract_text_from_markdown(path: Path | str) -> dict[str, Any]:
    return _read_text(path, "markdown")


def extract_text_from_txt(path: Path | str) -> dict[str, Any]:
    return _read_text(path, "txt")


def extract_text_from_xml(path: Path | str) -> dict[str, Any]:
    source = Path(path)
    warnings: list[str] = []
    try:
        raw = source.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw = source.read_text(encoding="utf-8", errors="replace")
        warnings.append("UTF-8 decode failed; replacement characters were used.")
    except OSError as exc:
        return _failed("xml", str(exc))

    try:
        root = ET.fromstring(raw)
        parts: list[str] = []
        for element in root.iter():
            tag = _local_name(element.tag)
            text = (element.text or "").strip()
            if text:
                parts.append(f"{tag}: {text}")
            for key, value in sorted(element.attrib.items()):
                if value:
                    parts.append(f"{tag}.{key}: {value}")
        return {
            "text": normalize_whitespace("\n".join(parts)),
            "source_format": "xml",
            "warnings": warnings,
            "parse_status": "partial" if warnings else "ok",
        }
    except ET.ParseError as exc:
        warnings.append(f"XML parse failed; falling back to stripped text: {exc}")
        return {
            "text": normalize_whitespace(_strip_xml_tags(raw)),
            "source_format": "xml",
            "warnings": warnings,
            "parse_status": "partial",
        }


def extract_text_from_json(path: Path | str) -> dict[str, Any]:
    source = Path(path)
    try:
        raw = source.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw = source.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return _failed("json", str(exc))
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {
            "text": normalize_whitespace(raw),
            "source_format": "json",
            "warnings": [f"JSON parse failed; using raw text: {exc}"],
            "parse_status": "partial",
        }
    lines: list[str] = []
    _json_lines(loaded, lines, "")
    return {
        "text": normalize_whitespace("\n".join(lines)),
        "source_format": "json",
        "warnings": [],
        "parse_status": "ok",
    }


def extract_text_from_csv(path: Path | str) -> dict[str, Any]:
    source = Path(path)
    warnings: list[str] = []
    try:
        with source.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
    except UnicodeDecodeError:
        with source.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            rows = list(csv.reader(handle))
        warnings.append("UTF-8 decode failed; replacement characters were used.")
    except OSError as exc:
        return _failed("csv", str(exc))
    if not rows:
        return {"text": "", "source_format": "csv", "warnings": warnings, "parse_status": "ok"}
    header = rows[0]
    sample_rows = rows[1:21]
    lines = ["Headers: " + ", ".join(header)]
    for index, row in enumerate(sample_rows, start=1):
        values = []
        for column, value in zip(header, row):
            values.append(f"{column}={_clip(value, 160)}")
        lines.append(f"Row {index}: " + ", ".join(values))
    if len(rows) > 21:
        warnings.append(f"CSV rows capped at 20 sample rows from {len(rows) - 1} data row(s).")
    return {
        "text": normalize_whitespace("\n".join(lines)),
        "source_format": "csv",
        "warnings": warnings,
        "parse_status": "partial" if warnings else "ok",
    }


def extract_text_from_html(path: Path | str) -> dict[str, Any]:
    result = _read_text(path, "html")
    if result["parse_status"] == "failed":
        return result
    parser = _HTMLTextExtractor()
    parser.feed(result["text"])
    result["text"] = normalize_whitespace(parser.text())
    return result


def extract_text_from_pdf(path: Path | str) -> dict[str, Any]:
    source = Path(path)
    reader_class = None
    library_name = ""
    try:
        from pypdf import PdfReader  # type: ignore

        reader_class = PdfReader
        library_name = "pypdf"
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore

            reader_class = PdfReader
            library_name = "PyPDF2"
        except ImportError:
            return {
                "text": "",
                "source_format": "pdf",
                "warnings": ["PDF import requires optional dependency pypdf or PyPDF2. No OCR is performed."],
                "parse_status": "failed",
            }

    try:
        reader = reader_class(str(source))
        page_text = []
        for index, page in enumerate(reader.pages, start=1):
            extracted = page.extract_text() or ""
            if extracted.strip():
                page_text.append(f"Page {index}\n{extracted}")
        return {
            "text": normalize_whitespace("\n\n".join(page_text)),
            "source_format": "pdf",
            "warnings": [f"PDF text extracted with optional library {library_name}; OCR was not used."],
            "parse_status": "partial",
        }
    except Exception as exc:  # noqa: BLE001 - optional PDF libraries raise varied exceptions.
        return _failed("pdf", str(exc))


def normalize_whitespace(text: str) -> str:
    """Normalize line whitespace while preserving paragraph breaks."""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    collapsed: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if not blank:
                collapsed.append("")
            blank = True
            continue
        collapsed.append(line)
        blank = False
    return "\n".join(collapsed).strip()


def chunk_text(text: str, max_chars: int = 6000, overlap: int = 500) -> list[str]:
    """Split text into deterministic overlapping chunks."""

    normalized = normalize_whitespace(text)
    if not normalized:
        return []
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    overlap = max(0, min(overlap, max_chars - 1))
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + max_chars)
        chunks.append(normalized[start:end].strip())
        if end >= len(normalized):
            break
        start = end - overlap
    return chunks


def _read_text(path: Path | str, source_format: str) -> dict[str, Any]:
    source = Path(path)
    warnings: list[str] = []
    try:
        text = source.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = source.read_text(encoding="utf-8", errors="replace")
        warnings.append("UTF-8 decode failed; replacement characters were used.")
    except OSError as exc:
        return _failed(source_format, str(exc))
    return {
        "text": normalize_whitespace(text),
        "source_format": source_format,
        "warnings": warnings,
        "parse_status": "partial" if warnings else "ok",
    }


def _limit_result(result: dict[str, Any], max_chars: int) -> dict[str, Any]:
    text = str(result.get("text") or "")
    if len(text) > max_chars:
        result = dict(result)
        result["text"] = text[:max_chars]
        warnings = list(result.get("warnings") or [])
        warnings.append(f"Extracted text capped at {max_chars} characters.")
        result["warnings"] = warnings
        result["parse_status"] = "partial" if result.get("parse_status") != "failed" else "failed"
    return result


def _failed(source_format: str, error: str) -> dict[str, Any]:
    return {"text": "", "source_format": source_format, "warnings": [error], "parse_status": "failed"}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _strip_xml_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def _json_lines(value: Any, lines: list[str], prefix: str, depth: int = 0) -> None:
    if depth > 8:
        lines.append(f"{prefix}: [MAX_DEPTH]")
        return
    if isinstance(value, dict):
        for key in sorted(value, key=str):
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            _json_lines(value[key], lines, next_prefix, depth + 1)
        return
    if isinstance(value, list):
        lines.append(f"{prefix}: list[{len(value)}]")
        for index, item in enumerate(value[:10]):
            _json_lines(item, lines, f"{prefix}[{index}]", depth + 1)
        if len(value) > 10:
            lines.append(f"{prefix}: [TRUNCATED_LIST {len(value) - 10} more]")
        return
    lines.append(f"{prefix}: {_clip(str(value), 500)}")


def _clip(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[:limit] + "...[TRUNCATED]"


class _HTMLTextExtractor(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data.strip():
            self._parts.append(data.strip())

    def text(self) -> str:
        return "\n".join(self._parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract text from a local knowledge source file.")
    parser.add_argument("path")
    parser.add_argument("--max-chars", type=int, default=200_000)
    args = parser.parse_args(argv)
    result = extract_text(args.path, max_chars=args.max_chars)
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0 if result.get("parse_status") != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
