"""Small Git wrapper for Azure DevOps Wiki draft publication."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_git(args: list[str], cwd: str | Path, check: bool = True) -> str:
    """Run a git command and return stdout."""

    result = subprocess.run(["git", *args], cwd=Path(cwd), text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def clone_or_update_repo(repo_url: str, branch: str, vendor_dir: str | Path) -> Path:
    """Clone or update a wiki Git repository into the local vendor cache."""

    if not repo_url:
        raise ValueError("Azure Wiki repo URL is required. Pass --repo-url or set AZURE_WIKI_REPO.")
    target = Path(vendor_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        run_git(["clone", "--branch", branch, repo_url, str(target)], cwd=target.parent)
        return target
    if not (target / ".git").exists():
        raise ValueError(f"Azure Wiki vendor directory exists but is not a Git repository: {target}")
    run_git(["fetch"], cwd=target)
    run_git(["checkout", branch], cwd=target)
    run_git(["pull", "--ff-only"], cwd=target)
    return target


def get_current_branch(repo_dir: str | Path) -> str:
    return run_git(["branch", "--show-current"], cwd=repo_dir)


def get_default_branch(repo_dir: str | Path) -> str:
    """Best-effort default branch detection."""

    origin_head = run_git(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"], cwd=repo_dir, check=False)
    if origin_head.startswith("origin/"):
        return origin_head.split("/", 1)[1]
    branches = run_git(["branch", "--format=%(refname:short)"], cwd=repo_dir, check=False).splitlines()
    for candidate in ("main", "master"):
        if candidate in branches:
            return candidate
    current = get_current_branch(repo_dir)
    return current or "main"


def create_branch(repo_dir: str | Path, branch_name: str) -> None:
    """Create or switch to a local draft branch."""

    existing = run_git(["branch", "--list", branch_name], cwd=repo_dir, check=False)
    if existing.strip():
        run_git(["checkout", branch_name], cwd=repo_dir)
    else:
        run_git(["checkout", "-b", branch_name], cwd=repo_dir)


def get_status(repo_dir: str | Path) -> str:
    return run_git(["status", "--short"], cwd=repo_dir)


def list_changed_files(repo_dir: str | Path) -> list[str]:
    output = get_status(repo_dir)
    files: list[str] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        files.append(line[3:].strip())
    return sorted(files)


def commit_changes(repo_dir: str | Path, message: str) -> str:
    """Stage all local wiki changes and commit them."""

    if not get_status(repo_dir).strip():
        return ""
    run_git(["add", "."], cwd=repo_dir)
    run_git(["commit", "-m", message], cwd=repo_dir)
    return get_current_commit(repo_dir)


def push_branch(repo_dir: str | Path, branch_name: str) -> None:
    default_branch = get_default_branch(repo_dir)
    if branch_name == default_branch:
        raise ValueError(f"Refusing to push Azure Wiki default branch: {branch_name}")
    run_git(["push", "-u", "origin", branch_name], cwd=repo_dir)


def get_current_commit(repo_dir: str | Path) -> str:
    return run_git(["rev-parse", "HEAD"], cwd=repo_dir)
