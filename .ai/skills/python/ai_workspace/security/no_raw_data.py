"""Detect accidental raw data, exports, dumps, and secrets in changed files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


DEFAULT_LARGE_THRESHOLD = 5 * 1024 * 1024
SKIP_DIRS = {".git", "node_modules", ".sfdx", ".sf", "coverage", "dist", "build"}
RAW_PATH_HINTS = ("raw", "export", "dump")
SECRET_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"password\s*[:=]\s*['\"]?[^'\"\s]{4,}",
        r"(?:api[_-]?token|access[_-]?token|refresh[_-]?token|auth[_-]?token|token)\s*[:=]\s*['\"]?[A-Za-z0-9_/+=.-]{8,}",
        r"client[_-]?secret\s*[:=]\s*['\"]?[^'\"\s]{8,}",
        r"private[_-]?key\s*[:=]\s*['\"]?[^'\"\s]{8,}",
        r"BEGIN\s+PRIVATE\s+KEY",
    )
]
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


def scan_paths_for_raw_data(
    paths: list[str],
    repo_root: str = ".",
    large_threshold: int = DEFAULT_LARGE_THRESHOLD,
) -> list[dict[str, Any]]:
    """Scan changed paths for raw/exported data and obvious secrets."""

    root = Path(repo_root).resolve()
    findings: list[dict[str, Any]] = []
    for path in sorted(set(paths)):
        if _should_skip(path):
            continue
        file_path = (root / path).resolve()
        try:
            file_path.relative_to(root)
        except ValueError:
            continue
        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()
        path_lower = path.lower()
        try:
            size = file_path.stat().st_size
        except OSError:
            continue

        if suffix == ".csv":
            findings.append(_finding(path, "high", "CSV file detected; avoid committing raw or exported data."))
        if suffix in {".xls", ".xlsx"}:
            findings.append(_finding(path, "high", "Spreadsheet file detected; avoid committing raw or exported data."))
        if suffix in {".json", ".jsonl"} and size > large_threshold:
            findings.append(_finding(path, "high", "Large JSON/JSONL file detected; verify this is not a raw data dump."))
        if _has_raw_path_hint(path_lower):
            findings.append(_finding(path, "medium", "Path contains raw/export/dump hint; verify file is controlled context, not raw data."))

        if _is_binary(file_path):
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            findings.append(_finding(path, "blocking", "Likely secret material detected; remove before commit."))
        email_count = len(EMAIL_RE.findall(text))
        if email_count >= 10:
            findings.append(_finding(path, "high", f"Many email-like strings detected ({email_count}); verify data is anonymized and controlled."))
    return findings


def _finding(path: str, severity: str, message: str) -> dict[str, str]:
    return {"path": path, "severity": severity, "message": message}


def _should_skip(path: str) -> bool:
    parts = Path(path).parts
    return any(part in SKIP_DIRS for part in parts)


def _has_raw_path_hint(path_lower: str) -> bool:
    tokens = [token for token in re.split(r"[^a-z0-9]+", path_lower) if token]
    for index, token in enumerate(tokens):
        if token in RAW_PATH_HINTS and not (token == "raw" and index > 0 and tokens[index - 1] == "no"):
            return True
    return False


def _is_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return True
    return b"\0" in chunk
