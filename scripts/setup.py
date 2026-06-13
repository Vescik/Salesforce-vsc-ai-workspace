#!/usr/bin/env python3
"""Thin wrapper for AI Workspace setup."""

from __future__ import annotations

import os
import subprocess
import sys
import shutil
from pathlib import Path


def _ensure_min_python() -> None:
    if sys.version_info >= (3, 11):
        return
    candidate = shutil.which("python3.11")
    if candidate and Path(candidate).resolve() != Path(sys.executable).resolve():
        result = subprocess.run([candidate, *sys.argv])
        sys.exit(result.returncode)


def _prepare_repo() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    os.chdir(repo_root)
    tools = repo_root / ".ai" / "skills" / "python"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))


def main() -> int:
    _ensure_min_python()
    _prepare_repo()
    from ai_workspace.configuration.bootstrap import main as bootstrap_main

    args = sys.argv[1:] or ["--create-local-config", "--print-next-steps"]
    return bootstrap_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
