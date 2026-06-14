"""CSV converter for Knowledge Base Creator 2.0."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from ai_workspace.knowledge.converters import make_doc
from ai_workspace.knowledge.parse_documents import normalize_whitespace


ROW_SAMPLE_LIMIT = 50


def convert(path: Path | str) -> dict[str, Any]:
    source = Path(path)
    warnings: list[str] = []
    try:
        with source.open("r", encoding="utf-8", newline="") as handle:
            sample = handle.read(4096)
            handle.seek(0)
            dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
            has_header = csv.Sniffer().has_header(sample) if sample.strip() else False
            rows = list(csv.reader(handle, dialect))
    except UnicodeDecodeError:
        with source.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            rows = list(csv.reader(handle))
        has_header = True
        warnings.append("UTF-8 decode failed; replacement characters were used.")
    except csv.Error as exc:
        return make_doc("csv", source, warnings=[f"CSV parse failed: {exc}"], parse_status="failed")
    except OSError as exc:
        return make_doc("csv", source, warnings=[f"Could not read CSV: {exc}"], parse_status="failed")

    if not rows:
        return make_doc("csv", source, metadata={"row_count": 0, "column_count": 0}, parse_status="ok")

    if has_header:
        header = [cell.strip() for cell in rows[0]]
        data_rows = rows[1:]
    else:
        max_cols = max(len(row) for row in rows)
        header = [f"Column {index}" for index in range(1, max_cols + 1)]
        data_rows = rows
        warnings.append("CSV header was not detected; generated generic column names.")

    row_count = len(data_rows)
    sample_rows = data_rows[:ROW_SAMPLE_LIMIT]
    sections = [
        {
            "heading": f"{source.stem} CSV Summary",
            "level": 1,
            "body": normalize_whitespace(
                "\n".join(
                    [
                        f"Columns: {', '.join(header)}",
                        f"Data rows: {row_count}",
                        f"Sampled rows: {len(sample_rows)}",
                    ]
                )
            ),
            "anchors": ["csv-summary"],
        }
    ]
    table_rows = [header]
    for row in sample_rows:
        padded = list(row) + [""] * max(0, len(header) - len(row))
        table_rows.append([str(cell).strip() for cell in padded[: len(header)]])
    if row_count > ROW_SAMPLE_LIMIT:
        warnings.append(f"CSV rows capped at {ROW_SAMPLE_LIMIT} sample rows from {row_count} data row(s).")
    return make_doc(
        "csv",
        source,
        sections=sections,
        tables=[{"caption": f"{source.stem} sample rows", "rows": table_rows}],
        metadata={
            "row_count": row_count,
            "column_count": len(header),
            "columns": header,
            "sample_rows": len(sample_rows),
        },
        warnings=warnings,
        parse_status="partial" if warnings else "ok",
        degraded=False,
    )
