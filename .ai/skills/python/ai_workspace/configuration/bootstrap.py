"""Bootstrap local employee setup for the Salesforce AI Workspace."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import venv
from pathlib import Path
from typing import Any

from ai_workspace.configuration.workspace_config import (
    DEFAULT_CONFIG,
    EXAMPLE_CONFIG,
    LOCAL_CONFIG,
    ensure_required_dirs,
    get_knowledge_config,
    get_path,
    load_workspace_config,
    mask_sensitive,
    resolve_repo_root,
    validate_workspace_config,
)
from ai_workspace.knowledge.sync_knowledge_repo import sync_knowledge_repo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Set up the local Salesforce AI Workspace.")
    parser.add_argument("--config", default=".ai/config/workspace.local.json")
    parser.add_argument("--create-local-config", action="store_true")
    parser.add_argument("--overwrite-config", action="store_true")
    parser.add_argument("--create-venv", action="store_true")
    parser.add_argument("--install-dev-deps", action="store_true")
    parser.add_argument("--skip-venv", action="store_true")
    parser.add_argument("--skip-python-install", action="store_true")
    parser.add_argument("--skip-knowledge-sync", action="store_true")
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--print-next-steps", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = bootstrap_workspace(args)
    except Exception as exc:  # noqa: BLE001 - setup should fail with a concise error.
        print(f"ERROR: setup failed: {exc}", file=sys.stderr)
        return 1

    print(_console_report(report, print_next_steps=args.print_next_steps))
    return 1 if report["errors"] else 0


def bootstrap_workspace(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = resolve_repo_root()
    config_path = _resolve_config_path(args.config, repo_root)
    created_config = False
    errors: list[str] = []
    warnings: list[str] = []
    actions: list[str] = []

    if args.create_local_config or not config_path.exists():
        created_config = _create_local_config(config_path, repo_root, overwrite=args.overwrite_config)
        actions.append(f"created local config: {_repo_relative(config_path, repo_root)}" if created_config else "local config already exists")

    config = load_workspace_config(config_path)
    config_errors, config_warnings = validate_workspace_config(config)
    errors.extend(config_errors)
    warnings.extend(config_warnings)

    created_dirs = ensure_required_dirs(config)
    actions.extend(f"created directory: {path}" for path in created_dirs)

    if args.create_venv and not args.skip_venv:
        venv_path = get_path(config, "repo_root") / str(config.get("python", {}).get("venv_path") or ".venv")
        if venv_path.exists():
            actions.append(f"venv already exists: {_repo_relative(venv_path, repo_root)}")
        else:
            venv.EnvBuilder(with_pip=True).create(venv_path)
            actions.append(f"created venv: {_repo_relative(venv_path, repo_root)}")

    if args.install_dev_deps and not args.skip_python_install:
        installed = _install_dependencies(config)
        actions.extend(installed or ["no requirements file found; skipped dependency installation"])

    kb_report = None
    kb = get_knowledge_config(config)
    if bool(kb.get("enabled")) and bool(kb.get("sync_on_setup")) and not args.skip_knowledge_sync:
        repo_url = str(kb.get("repo_url") or "").strip()
        if repo_url:
            kb_report = sync_knowledge_repo(
                repo_url=repo_url,
                branch=str(kb.get("branch") or "main"),
                vendor_dir=get_path(config, "knowledge_vendor_dir"),
                knowledge_root=get_path(config, "knowledge_root"),
                policy_path=get_path(config, "repo_root") / ".ai/knowledge/sync-policy.yaml",
                dry_run=False,
                clean=False,
                allow_imports=False,
                max_file_mb=None,
                repo_root=get_path(config, "repo_root"),
            )
            actions.append(f"synced knowledge base from {mask_sensitive(repo_url)}")
        else:
            warnings.append("Knowledge sync_on_setup is enabled but knowledge_base.repo_url is empty.")

    return {
        "created_config": created_config,
        "config_path": _repo_relative(config_path, repo_root),
        "actions": actions,
        "warnings": sorted(set(warnings)),
        "errors": sorted(set(errors)),
        "knowledge_sync": kb_report,
        "next_steps": _next_steps(config),
    }


def _create_local_config(config_path: Path, repo_root: Path, overwrite: bool = False) -> bool:
    if config_path.exists() and not overwrite:
        return False
    source = repo_root / ".ai/config/workspace.local.json.example"
    if not source.exists():
        source = repo_root / EXAMPLE_CONFIG
    config_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, config_path)
    return True


def _install_dependencies(config: dict[str, Any]) -> list[str]:
    repo_root = get_path(config, "repo_root")
    candidates = [repo_root / "requirements-dev.txt", repo_root / "requirements.txt"]
    requirements = next((path for path in candidates if path.exists()), None)
    if not requirements:
        return []
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements)], check=True)
    return [f"installed dependencies from {_repo_relative(requirements, repo_root)}"]


def _next_steps(config: dict[str, Any]) -> list[str]:
    alias = str(config.get("salesforce", {}).get("default_dev_org_alias") or "IntDev")
    return [
        "Activate the venv if you created one.",
        f"Authenticate Salesforce: sf org login web --alias {alias}",
        "Run: make doctor",
        "Run: make ai-index-repo",
        "Run: make knowledge-index",
        "Build context: make ai-context WORK_ITEM=EXAMPLE-WI QUERY=\"example\"",
    ]


def _console_report(report: dict[str, Any], print_next_steps: bool) -> str:
    status = "FAIL" if report["errors"] else ("PASS_WITH_WARNINGS" if report["warnings"] else "PASS")
    lines = [f"AI Workspace setup: {status}", f"Config: {report['config_path']}"]
    if report["actions"]:
        lines.append("Actions:")
        lines.extend(f"- {action}" for action in report["actions"])
    if report["warnings"]:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in report["warnings"])
    if report["errors"]:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in report["errors"])
    if print_next_steps:
        lines.append("Next steps:")
        lines.extend(f"- {step}" for step in report["next_steps"])
    return "\n".join(lines)


def _resolve_config_path(value: str, repo_root: Path) -> Path:
    path = Path(value or LOCAL_CONFIG)
    return path.expanduser().resolve() if path.is_absolute() else (repo_root / path).resolve()


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
