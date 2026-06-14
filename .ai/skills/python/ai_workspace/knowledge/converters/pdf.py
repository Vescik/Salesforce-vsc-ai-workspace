"""PDF converter (``pdfplumber`` preferred, falls back to ``pypdf`` shim)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_workspace.knowledge.converters import make_doc


def convert(path: Path | str) -> dict[str, Any]:
    source = Path(path)
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        return _pypdf_fallback(source)

    try:
        sections: list[dict[str, Any]] = []
        tables: list[dict[str, Any]] = []
        with pdfplumber.open(str(source)) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = (page.extract_text() or "").strip()
                anchor = f"page-{index}"
                sections.append({
                    "heading": f"Page {index}",
                    "level": 2,
                    "body": text,
                    "anchors": [anchor],
                })
                for table_rows in page.extract_tables() or []:
                    rows = [[(cell or "").strip() for cell in row] for row in table_rows]
                    if rows:
                        tables.append({"caption": f"Page {index} table", "rows": rows})
            metadata: dict[str, Any] = {"library": "pdfplumber", "page_count": len(pdf.pages)}
            try:
                metadata.update(dict(pdf.metadata or {}))
            except Exception:  # noqa: BLE001
                pass
    except Exception as exc:  # noqa: BLE001
        return make_doc("pdf", source, warnings=[f"pdfplumber failed: {exc}"], parse_status="failed")

    return make_doc(
        "pdf",
        source,
        sections=sections,
        tables=tables,
        metadata=metadata,
        parse_status="ok",
        degraded=False,
    )


def _pypdf_fallback(source: Path) -> dict[str, Any]:
    """Fall back to the existing pypdf-based extractor in parse_documents."""

    from ai_workspace.knowledge.parse_documents import extract_text_from_pdf

    result = extract_text_from_pdf(source)
    text = str(result.get("text") or "")
    warnings = list(result.get("warnings") or [])
    warnings.insert(0, "pdfplumber not installed; using stdlib pypdf shim with reduced fidelity.")
    parse_status = str(result.get("parse_status") or "partial")
    sections: list[dict[str, Any]] = []
    if text:
        sections.append({"heading": source.stem, "level": 1, "body": text, "anchors": []})
    return make_doc(
        "pdf",
        source,
        sections=sections,
        metadata={"library": "pypdf"},
        warnings=warnings,
        parse_status=parse_status if parse_status != "ok" else "partial",
        degraded=True,
    )
