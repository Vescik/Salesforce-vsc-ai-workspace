"""Push curated local knowledge notes to the external Knowledge Base git repository."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from ai_workspace.knowledge.import_knowledge import detect_sensitive_content
from ai_workspace.knowledge.index_knowledge import _knowledge_markdown_files
from ai_workspace.knowledge.sync_knowledge_repo import _git, _mask_repo_url, _sync_git_repo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Push local knowledge notes to the external Knowledge Base git repository."
    )
    parser.add_argument("--vendor-dir", default=".ai/vendor/knowledge-base")
    parser.add_argument("--knowledge-root", default=".ai/knowledge")
    parser.add_argument("--repo-url", default="")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--message", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(".").resolve()
    vendor_dir = repo_root / args.vendor_dir
    knowledge_root = repo_root / args.knowledge_root
    repo_url = (args.repo_url or os.environ.get("KB_REPO") or "").strip()

    try:
        report = push_knowledge(
            vendor_dir=vendor_dir,
            knowledge_root=knowledge_root,
            repo_url=repo_url,
            branch=args.branch,
            message=args.message,
            dry_run=args.dry_run,
            do_push=args.push,
            repo_root=repo_root,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: knowledge push failed: {exc}", file=sys.stderr)
        return 1

    _print_report(report)
    return 1 if report.get("failed") else 0


def push_knowledge(
    vendor_dir: Path,
    knowledge_root: Path,
    repo_url: str,
    branch: str,
    message: str,
    dry_run: bool,
    do_push: bool,
    repo_root: Path,
) -> dict[str, Any]:
    """Copy new/modified knowledge notes to the vendor clone and push to the remote KB repo."""

    warnings: list[str] = []

    # Step 1: Ensure vendor clone exists
    if not vendor_dir.exists():
        if not repo_url:
            raise ValueError(
                "vendor-dir does not exist and --repo-url is not set. "
                "Run: make knowledge-sync KB_REPO=<url> first, or pass --repo-url."
            )
        _sync_git_repo(repo_url, branch, vendor_dir)
    elif not (vendor_dir / ".git").exists():
        raise ValueError(f"vendor-dir exists but is not a git repository: {vendor_dir}")

    # Step 2: Detect changed files via checksum comparison
    changed_files: list[str] = []
    skipped_files: list[dict[str, str]] = []

    for local_path in _knowledge_markdown_files(knowledge_root):
        relative = local_path.relative_to(knowledge_root).as_posix()
        vendor_path = vendor_dir / relative

        local_checksum = _file_checksum(local_path)
        vendor_checksum = _file_checksum(vendor_path) if vendor_path.exists() else None

        if local_checksum == vendor_checksum:
            continue  # identical — nothing to do

        # Step 3: Safety scan before including the file
        text = local_path.read_text(encoding="utf-8", errors="replace")
        hits = detect_sensitive_content(text)
        if hits:
            warnings.append(
                f"Possible secret-like value in `{relative}` — skipped. Review before pushing."
            )
            skipped_files.append({"path": relative, "reason": "possible_secret"})
            continue

        changed_files.append(relative)

    result: dict[str, Any] = {
        "dry_run": dry_run,
        "pushed": False,
        "vendor_dir": _repo_relative(vendor_dir, repo_root),
        "branch": branch,
        "repo": _mask_repo_url(repo_url) if repo_url else "(existing vendor clone)",
        "commit": None,
        "changed_files": changed_files,
        "skipped_files": skipped_files,
        "warnings": warnings,
        "failed": False,
    }

    if not changed_files:
        return result

    # Step 4: Dry-run — stop here, report what would change
    if dry_run:
        return result

    # Step 5: Copy changed files into vendor clone
    for relative in changed_files:
        local_path = knowledge_root / relative
        vendor_path = vendor_dir / relative
        vendor_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, vendor_path)

    # Step 6: Git add
    _git(["-C", str(vendor_dir), "add", "--"] + changed_files)

    # Step 7: Verify something is actually staged (files might already match HEAD)
    status = _git(["-C", str(vendor_dir), "status", "--porcelain"]).strip()
    if not status:
        return result

    # Step 8: Commit
    commit_message = message or _auto_message(changed_files)
    _git(["-C", str(vendor_dir), "commit", "-m", commit_message])
    commit_sha = _git(["-C", str(vendor_dir), "rev-parse", "HEAD"]).strip()
    result["commit"] = commit_sha

    # Step 9: Push only when explicitly requested
    if do_push:
        _git(["-C", str(vendor_dir), "push", "origin", branch])
        result["pushed"] = True
    else:
        print(
            f"Committed locally in vendor clone (commit {commit_sha[:8]}). "
            "Run with --push to push to remote."
        )

    return result


def _file_checksum(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _auto_message(changed_files: list[str]) -> str:
    domains: dict[str, int] = defaultdict(int)
    for relative in changed_files:
        parts = Path(relative).parts
        if len(parts) >= 2 and parts[0] == "domains":
            domains[parts[1]] += 1
        else:
            domains["general"] += 1
    domain_summary = ", ".join(
        f"{domain} ({count})" if count > 1 else domain
        for domain, count in sorted(domains.items())
    )
    n = len(changed_files)
    return f"Add/update knowledge: {domain_summary} ({n} file{'s' if n != 1 else ''})"


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _print_report(report: dict[str, Any]) -> None:
    label = "DRY RUN — " if report.get("dry_run") else ""
    changed = report.get("changed_files", [])
    skipped = report.get("skipped_files", [])
    warnings = report.get("warnings", [])

    print(f"\n{label}Knowledge Push Report")
    print(f"  Vendor clone : {report.get('vendor_dir')}")
    print(f"  Branch       : {report.get('branch')}")
    if report.get("commit"):
        print(f"  Commit       : {report.get('commit')}")
    if report.get("pushed"):
        print(f"  Pushed to    : {report.get('repo')}")

    if changed:
        print(f"\nChanged files ({len(changed)}):")
        for f in changed:
            print(f"  + {f}")
    else:
        print("\nNo changed files.")

    if skipped:
        print(f"\nSkipped ({len(skipped)}):")
        for item in skipped:
            print(f"  ! {item['path']} — {item['reason']}")

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  ! {w}")


if __name__ == "__main__":
    raise SystemExit(main())
