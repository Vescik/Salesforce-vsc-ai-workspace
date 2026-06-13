"""Detect Salesforce ID-looking strings in changed files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


SALESFORCE_ID_RE = re.compile(r"(?<![A-Za-z0-9])([A-Za-z0-9]{15}(?:[A-Za-z0-9]{3})?)(?![A-Za-z0-9])")
COMMON_PREFIXES = {
    "001",
    "003",
    "005",
    "006",
    "00Q",
    "00T",
    "00U",
    "00D",
    "00e",
    "00G",
    "00k",
    "00N",
    "00P",
    "a0B",
    "a0D",
    "a0E",
    "a0F",
    "a0K",
    "a0M",
    "a0N",
}
SKIP_DIRS = {".git", "node_modules", ".sfdx", ".sf", "coverage", "dist", "build"}
HIGH_PATH_PREFIXES = ("force-app/", "docs/", "specs/", ".ai/context/", ".ai/outputs/")


def find_salesforce_id_candidates_in_text(text: str) -> list[dict[str, Any]]:
    """Return Salesforce ID-looking candidates with line numbers."""

    findings: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in SALESFORCE_ID_RE.finditer(line):
            candidate = match.group(1)
            if not _candidate_plausible(candidate):
                continue
            prefix_note = "common Salesforce prefix" if candidate[:3] in COMMON_PREFIXES else "generic ID-like string"
            findings.append(
                {
                    "line": line_number,
                    "candidate": candidate,
                    "severity": "medium",
                    "message": f"Salesforce ID candidate detected ({prefix_note}); avoid hardcoded record IDs.",
                }
            )
    return findings


def scan_paths_for_salesforce_ids(paths: list[str], repo_root: str = ".") -> list[dict[str, Any]]:
    """Scan changed paths for Salesforce ID-looking strings."""

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
        if not file_path.is_file() or _is_binary(file_path):
            continue
        try:
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        severity = "high" if path.startswith(HIGH_PATH_PREFIXES) else "medium"
        for finding in find_salesforce_id_candidates_in_text(text):
            enriched = dict(finding)
            enriched["path"] = path
            enriched["severity"] = severity
            findings.append(enriched)
    return findings


def _candidate_plausible(candidate: str) -> bool:
    if candidate[:3] in COMMON_PREFIXES:
        return True
    return any(char.isdigit() for char in candidate) and any(char.isalpha() for char in candidate)


def _should_skip(path: str) -> bool:
    parts = Path(path).parts
    return any(part in SKIP_DIRS for part in parts)


def _is_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return True
    return b"\0" in chunk
