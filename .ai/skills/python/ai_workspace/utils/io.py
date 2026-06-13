"""I/O helpers for deterministic local metadata indexing."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping


REFERENCE_KEYS = (
    "objects",
    "fields",
    "apex_classes",
    "flows",
    "lwc_components",
    "custom_metadata",
)


def empty_references() -> dict[str, list[str]]:
    """Return the standard reference shape used in JSONL records."""

    return {key: [] for key in REFERENCE_KEYS}


def merge_references(*items: Mapping[str, Iterable[str]]) -> dict[str, list[str]]:
    """Merge reference dictionaries into sorted, duplicate-free lists."""

    merged: MutableMapping[str, set[str]] = {key: set() for key in REFERENCE_KEYS}
    for item in items:
        for key in REFERENCE_KEYS:
            merged[key].update(value for value in item.get(key, []) if value)
    return {key: sorted(values) for key, values in merged.items()}


def warn(message: str) -> None:
    """Emit a warning to stderr."""

    print(f"WARNING: {message}", file=sys.stderr)


def is_within(path: Path, root: Path) -> bool:
    """Return True when path resolves inside root."""

    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def repo_relative_path(path: Path, repo_root: Path) -> str:
    """Return a POSIX relative path for a path inside the repository."""

    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def ensure_parent_dir(path: Path) -> None:
    """Create the parent directory for a file path."""

    path.parent.mkdir(parents=True, exist_ok=True)


def read_utf8(path: Path) -> tuple[str, bool]:
    """Read a UTF-8 text file.

    Returns ``(text, used_replacement)``. Replacement mode is used only as a
    fallback so indexing can continue and mark the parse as partial.
    """

    try:
        return path.read_text(encoding="utf-8"), False
    except UnicodeDecodeError:
        warn(f"UTF-8 decode failed for {path}; using replacement characters")
        return path.read_text(encoding="utf-8", errors="replace"), True


def write_jsonl(path: Path, records: Iterable[Mapping[str, object]]) -> None:
    """Write records as deterministic JSON Lines using UTF-8."""

    ensure_parent_dir(path)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True))
            handle.write("\n")
