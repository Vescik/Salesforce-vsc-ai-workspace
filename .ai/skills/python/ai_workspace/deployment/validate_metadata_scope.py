"""Validate changed files against a Work Item metadata scope file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_workspace.security.redactor import load_simple_yaml


ALWAYS_ALLOWED_PREFIXES = (
    ".ai/context/work-items/",
    ".ai/outputs/",
    "docs/",
    "specs/",
    "config/data-promotion/",
    "config/kimbleone-packs/",
    ".github/prompts/",
    ".github/agents/",
)


def load_metadata_scope(path: str) -> dict[str, Any]:
    """Load metadata-scope.yaml from the project's simple YAML subset."""

    source = Path(path)
    if not source.exists():
        return {"_missing": True, "_path": path}
    loaded = load_simple_yaml(path)
    if not isinstance(loaded, dict):
        raise ValueError(f"metadata scope must be a YAML mapping: {path}")
    loaded["_missing"] = False
    loaded["_path"] = path
    return loaded


def validate_changed_files_against_scope(
    changed_files: list[str],
    scope: dict[str, Any],
) -> list[dict[str, str]]:
    """Return scope findings for changed files."""

    findings: list[dict[str, str]] = []
    if scope.get("_missing"):
        findings.append(
            {
                "severity": "medium",
                "type": "metadata_scope_missing",
                "path": str(scope.get("_path") or "metadata-scope.yaml"),
                "message": "metadata-scope.yaml is missing; metadata scope was not validated against explicit Work Item boundaries.",
            }
        )
        return findings

    allowed_paths = _string_list(scope.get("allowed_paths"))
    blocked_paths = _string_list(scope.get("blocked_paths"))
    manual_review_paths = _string_list(scope.get("requires_manual_review"))

    for changed_file in sorted(changed_files):
        path = _normalize(changed_file)
        if _matches_prefix(path, ALWAYS_ALLOWED_PREFIXES):
            continue
        if not path.startswith("force-app/"):
            continue
        if _matches_prefix(path, blocked_paths):
            findings.append(
                {
                    "severity": "blocking",
                    "type": "blocked_metadata_path",
                    "path": path,
                    "message": "Changed file matches blocked metadata path in metadata-scope.yaml.",
                }
            )
            continue
        if _matches_prefix(path, manual_review_paths):
            findings.append(
                {
                    "severity": "medium",
                    "type": "manual_review_metadata_path",
                    "path": path,
                    "message": "Changed file matches a metadata path requiring manual review.",
                }
            )
        if allowed_paths and not _matches_prefix(path, allowed_paths):
            findings.append(
                {
                    "severity": "high",
                    "type": "metadata_out_of_scope",
                    "path": path,
                    "message": "Changed metadata file is outside allowed_paths in metadata-scope.yaml.",
                }
            )
    return findings


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_normalize(str(item)) for item in value]
    if isinstance(value, str):
        return [_normalize(value)]
    return []


def _matches_prefix(path: str, prefixes: list[str] | tuple[str, ...]) -> bool:
    return any(path == prefix.rstrip("/") or path.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)


def _normalize(path: str) -> str:
    return Path(path).as_posix()
