"""Small local Git helpers for Work Item prechecks."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_git(args: list[str], repo_root: str = ".") -> str:
    """Run a Git command and return stdout."""

    command = ["git"] + args
    completed = subprocess.run(
        command,
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        stdout = completed.stdout.strip()
        detail = stderr or stdout or "no output"
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout.strip()


def git_root(repo_root: str = ".") -> str:
    """Return the repository root path."""

    return run_git(["rev-parse", "--show-toplevel"], repo_root)


def get_current_branch(repo_root: str = ".") -> str:
    """Return the current branch name."""

    try:
        branch = run_git(["symbolic-ref", "--short", "HEAD"], repo_root)
        return branch or "HEAD"
    except RuntimeError:
        return "HEAD"


def get_changed_files(base_ref: str, repo_root: str = ".") -> list[str]:
    """Return changed and untracked files as POSIX paths relative to repo root."""

    changed: set[str] = set()
    if base_ref:
        diff_output = run_git(["diff", "--name-only", base_ref, "--"], repo_root)
        changed.update(_lines(diff_output))
    else:
        status_output = run_git(["diff", "--name-only", "--"], repo_root)
        changed.update(_lines(status_output))

    try:
        untracked_output = run_git(["ls-files", "--others", "--exclude-standard"], repo_root)
        changed.update(_lines(untracked_output))
    except RuntimeError:
        pass

    return sorted(_normalize(path) for path in changed if path)


def get_file_content(path: str, repo_root: str = ".") -> str:
    """Read a repository file as UTF-8 text."""

    root = Path(git_root(repo_root)).resolve()
    file_path = (root / path).resolve()
    file_path.relative_to(root)
    return file_path.read_text(encoding="utf-8")


def _lines(output: str) -> list[str]:
    return [line.strip() for line in output.splitlines() if line.strip()]


def _normalize(path: str) -> str:
    return Path(path).as_posix()
