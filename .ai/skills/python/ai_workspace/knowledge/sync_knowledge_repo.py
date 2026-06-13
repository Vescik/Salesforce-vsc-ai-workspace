"""Sync curated internal knowledge from an external Git repository."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_workspace.security.redactor import load_simple_yaml


DEFAULT_INCLUDE = [
    "README.md",
    "index.yaml",
    "domains/*.md",
    "domains/**/*.md",
    "object-notes/*.md",
    "object-notes/**/*.md",
    "process-maps/*.md",
    "process-maps/**/*.md",
    "decisions/*.md",
    "decisions/**/*.md",
    "governance/*.md",
    "governance/**/*.md",
]
DEFAULT_EXCLUDE = [
    "imports/**",
    "archive/**",
    "**/*.pdf",
    "**/*.docx",
    "**/*.xlsx",
    "**/*.png",
    "**/*.jpg",
    "**/*.jpeg",
    "**/*.zip",
    ".env",
    ".env.*",
    "**/.env",
    "**/.env.*",
    "secrets/**",
    "**/secrets/**",
    ".git/**",
]
PRESERVE_LOCAL_FILES = {
    ".ai/knowledge/sync-policy.yaml",
    ".ai/knowledge/sync-state.json",
}
SECRET_PATTERNS = [
    re.compile(r"(?i)\bpassword\s*="),
    re.compile(r"(?i)\bclient_secret\b"),
    re.compile(r"PRIVATE KEY"),
    re.compile(r"(?i)\baccess_token\b"),
    re.compile(r"(?i)\brefresh_token\b"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\bxoxb-[A-Za-z0-9-]{12,}"),
    re.compile(r"\bAWS_ACCESS_KEY\b"),
]
RAW_IMPORT_PATTERNS = {
    "imports/**",
    "imports/**/*",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync curated internal knowledge from an external Git repository.")
    parser.add_argument("--repo-url", default="")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--vendor-dir", default=".ai/vendor/knowledge-base")
    parser.add_argument("--knowledge-root", default=".ai/knowledge")
    parser.add_argument("--policy", default=".ai/knowledge/sync-policy.yaml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--allow-imports", action="store_true")
    parser.add_argument("--max-file-mb", type=float)
    parser.add_argument("--report-out", default=".ai/outputs/knowledge-sync/knowledge-sync.md")
    parser.add_argument("--json-out", default=".ai/outputs/knowledge-sync/knowledge-sync.json")
    args = parser.parse_args(argv)

    repo_url = (args.repo_url or os.environ.get("KB_REPO") or "").strip()
    if not repo_url:
        print("ERROR: provide --repo-url or set KB_REPO.", file=sys.stderr)
        return 2

    repo_root = Path(".").resolve()
    try:
        vendor_dir = _resolve_inside_repo(Path(args.vendor_dir), repo_root)
        knowledge_root = _resolve_inside_repo(Path(args.knowledge_root), repo_root)
        policy_path = _resolve_inside_repo(Path(args.policy), repo_root)

        report = sync_knowledge_repo(
            repo_url=repo_url,
            branch=args.branch,
            vendor_dir=vendor_dir,
            knowledge_root=knowledge_root,
            policy_path=policy_path,
            dry_run=args.dry_run,
            clean=args.clean,
            allow_imports=args.allow_imports,
            max_file_mb=args.max_file_mb,
            repo_root=repo_root,
        )
        _write_reports(report, Path(args.report_out), Path(args.json_out), repo_root)
    except Exception as exc:  # noqa: BLE001 - CLI should fail with a concise local error.
        print(f"ERROR: knowledge sync failed: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {args.report_out}")
    print(f"Wrote {args.json_out}")
    if report["warnings"]:
        print(f"Knowledge sync completed with {len(report['warnings'])} warning(s).")
    else:
        print("Knowledge sync completed.")
    return 1 if report.get("failed") else 0


def sync_knowledge_repo(
    repo_url: str,
    branch: str,
    vendor_dir: Path,
    knowledge_root: Path,
    policy_path: Path,
    dry_run: bool,
    clean: bool,
    allow_imports: bool,
    max_file_mb: float | None,
    repo_root: Path,
) -> dict[str, Any]:
    """Clone/pull the source repo and copy curated KB files locally."""

    warnings: list[str] = []
    policy = _load_policy(policy_path, warnings)
    if branch == "main":
        branch = str(_nested(policy, "source", "default_branch") or branch)
    max_file_mb = max_file_mb if max_file_mb is not None else _float(_nested(policy, "safety", "reject_large_file_mb"), 2.0)
    fail_on_secret = bool(_nested(policy, "safety", "fail_on_secret_like_values") is True)
    reject_binary = bool(_nested(policy, "safety", "reject_binary_files") is not False)
    scan_secrets = bool(_nested(policy, "safety", "scan_for_secret_like_values") is not False)
    warn_missing_front_matter = bool(_nested(policy, "safety", "warn_on_missing_front_matter") is True)

    _sync_git_repo(repo_url, branch, vendor_dir)
    commit = _git(["-C", str(vendor_dir), "rev-parse", "HEAD"]).strip()

    include_patterns = _string_list(_nested(policy, "copy_rules", "include")) or DEFAULT_INCLUDE
    exclude_patterns = _string_list(_nested(policy, "copy_rules", "exclude")) or DEFAULT_EXCLUDE
    if allow_imports:
        exclude_patterns = [pattern for pattern in exclude_patterns if pattern not in RAW_IMPORT_PATTERNS and not pattern.startswith("imports/")]

    copied_files: list[str] = []
    skipped_files: list[dict[str, str]] = []
    secret_hits = 0
    large_limit = int(max_file_mb * 1024 * 1024)

    for source in sorted(path for path in vendor_dir.rglob("*") if path.is_file()):
        relative = source.relative_to(vendor_dir).as_posix()
        reason = _skip_reason(
            source=source,
            relative=relative,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            large_limit=large_limit,
            reject_binary=reject_binary,
        )
        if reason:
            skipped_files.append({"path": relative, "reason": reason})
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        if scan_secrets and _contains_secret_like_value(text):
            secret_hits += 1
            warning = f"Possible secret-like value detected in `{relative}`."
            warnings.append(warning)
            if fail_on_secret:
                skipped_files.append({"path": relative, "reason": "possible_secret"})
                continue
        if warn_missing_front_matter and source.suffix.lower() == ".md" and not text.lstrip().startswith("---"):
            warnings.append(f"Missing front matter in `{relative}`.")

        destination = knowledge_root / relative
        copied_files.append(relative)
        if not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    removed_files: list[str] = []
    if clean:
        removed_files = _clean_removed_files(knowledge_root, copied_files, dry_run=dry_run)

    synced_at = datetime.now(timezone.utc).isoformat()
    state = {
        "source_repo_url": _mask_repo_url(repo_url),
        "branch": branch,
        "commit": commit,
        "synced_at": synced_at,
        "vendor_dir": _repo_relative(vendor_dir, repo_root),
        "knowledge_root": _repo_relative(knowledge_root, repo_root),
        "copied_files": copied_files,
        "skipped_files": skipped_files,
        "warnings": warnings,
        "policy_path": _repo_relative(policy_path, repo_root),
    }
    if removed_files:
        state["removed_files"] = removed_files

    if not dry_run:
        knowledge_root.mkdir(parents=True, exist_ok=True)
        (knowledge_root / "sync-state.json").write_text(
            json.dumps(state, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return {
        "failed": bool(fail_on_secret and secret_hits),
        "dry_run": dry_run,
        "source": {
            "repo": _mask_repo_url(repo_url),
            "branch": branch,
            "commit": commit,
        },
        "destination": {
            "knowledge_root": _repo_relative(knowledge_root, repo_root),
            "vendor_dir": _repo_relative(vendor_dir, repo_root),
        },
        "copied_files": copied_files,
        "skipped_files": skipped_files,
        "removed_files": removed_files,
        "warnings": warnings,
        "next_steps": [
            "make knowledge-index",
            "make ai-context WORK_ITEM=<WORK_ITEM_ID> QUERY=\"<topic>\"",
        ],
        "state": state,
    }


def _sync_git_repo(repo_url: str, branch: str, vendor_dir: Path) -> None:
    vendor_dir.parent.mkdir(parents=True, exist_ok=True)
    if not vendor_dir.exists():
        _git(["clone", "--branch", branch, repo_url, str(vendor_dir)])
        return
    if not (vendor_dir / ".git").exists():
        raise ValueError(f"Vendor directory exists but is not a Git repository: {vendor_dir}")
    _git(["-C", str(vendor_dir), "fetch"])
    _git(["-C", str(vendor_dir), "checkout", branch])
    _git(["-C", str(vendor_dir), "pull", "--ff-only"])


def _git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], check=False, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout


def _load_policy(path: Path, warnings: list[str]) -> dict[str, Any]:
    if not path.exists():
        warnings.append(f"Sync policy not found; using built-in defaults: {path.as_posix()}")
        return {}
    try:
        loaded = load_simple_yaml(str(path))
        if isinstance(loaded, dict):
            return loaded
        warnings.append(f"Sync policy did not parse as a mapping; using built-in defaults: {path.as_posix()}")
    except Exception as exc:  # noqa: BLE001 - sync should fall back clearly.
        warnings.append(f"Could not parse sync policy; using built-in defaults: {exc}")
    return {}


def _skip_reason(
    source: Path,
    relative: str,
    include_patterns: list[str],
    exclude_patterns: list[str],
    large_limit: int,
    reject_binary: bool,
) -> str:
    if ".git/" in relative or relative.startswith(".git/"):
        return "git_internal"
    if not _matches_any(relative, include_patterns):
        return "not_included"
    if _matches_any(relative, exclude_patterns):
        return "excluded_by_policy"
    try:
        size = source.stat().st_size
    except OSError:
        return "stat_failed"
    if size > large_limit:
        return "file_too_large"
    if reject_binary and _is_binary(source):
        return "binary_file"
    return ""


def _matches_any(relative: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(relative, pattern) for pattern in patterns)


def _is_binary(path: Path) -> bool:
    try:
        data = path.read_bytes()[:4096]
    except OSError:
        return True
    return b"\x00" in data


def _contains_secret_like_value(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def _clean_removed_files(knowledge_root: Path, copied_files: list[str], dry_run: bool) -> list[str]:
    state_path = knowledge_root / "sync-state.json"
    if not state_path.exists():
        return []
    try:
        previous = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    previous_files = set(str(item) for item in previous.get("copied_files", []) if item)
    current_files = set(copied_files)
    removed: list[str] = []
    for relative in sorted(previous_files - current_files):
        local_path = knowledge_root / relative
        repo_relative = f".ai/knowledge/{relative}"
        if repo_relative in PRESERVE_LOCAL_FILES:
            continue
        if local_path.exists() and local_path.is_file():
            removed.append(relative)
            if not dry_run:
                local_path.unlink()
    return removed


def _write_reports(report: dict[str, Any], report_out: Path, json_out: Path, repo_root: Path) -> None:
    report_out = _resolve_inside_repo(report_out, repo_root)
    json_out = _resolve_inside_repo(json_out, repo_root)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_out.write_text(_markdown_report(report), encoding="utf-8")


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Knowledge Sync Report",
        "",
        "## Source",
        "",
        f"- Repo: `{report['source']['repo']}`",
        f"- Branch: `{report['source']['branch']}`",
        f"- Commit: `{report['source']['commit']}`",
        f"- Dry run: `{str(report.get('dry_run', False)).lower()}`",
        "",
        "## Destination",
        "",
        f"- Knowledge root: `{report['destination']['knowledge_root']}`",
        f"- Vendor clone: `{report['destination']['vendor_dir']}`",
        "",
        "## Copied Files",
        "",
    ]
    copied = report.get("copied_files", [])
    lines.extend(f"- `{path}`" for path in copied) if copied else lines.append("- None")
    lines.extend(["", "## Skipped Files", ""])
    skipped = report.get("skipped_files", [])
    lines.extend(f"- `{item['path']}`: {item['reason']}" for item in skipped) if skipped else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    warnings = report.get("warnings", [])
    lines.extend(f"- {warning}" for warning in warnings) if warnings else lines.append("- None")
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- `{step}`" for step in report.get("next_steps", []))
    return "\n".join(lines).rstrip() + "\n"


def _nested(mapping: dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mask_repo_url(repo_url: str) -> str:
    masked = re.sub(r"(https?://)[^/@]+@", r"\1[REDACTED]@", repo_url)
    masked = re.sub(r"([?&](?:token|access_token|client_secret)=)[^&]+", r"\1[REDACTED]", masked, flags=re.IGNORECASE)
    return masked


def _resolve_inside_repo(path: Path, repo_root: Path) -> Path:
    candidate = path if path.is_absolute() else repo_root / path
    candidate = candidate.resolve()
    candidate.relative_to(repo_root.resolve())
    return candidate


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
