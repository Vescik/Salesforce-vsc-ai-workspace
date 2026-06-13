#!/usr/bin/env python3
"""Create or update local AI Workspace configuration."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


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


def main(argv: list[str] | None = None) -> int:
    _ensure_min_python()
    _prepare_repo()
    from ai_workspace.configuration.workspace_config import DEFAULT_CONFIG, mask_sensitive, resolve_repo_root

    parser = argparse.ArgumentParser(description="Configure local Salesforce AI Workspace settings.")
    parser.add_argument("--config", default=".ai/config/workspace.local.json")
    parser.add_argument("--dev-org")
    parser.add_argument("--validation-org", default=None)
    parser.add_argument("--kb-repo", default=None)
    parser.add_argument("--kb-branch", default=None)
    parser.add_argument("--enable-kb", action="store_true")
    parser.add_argument("--disable-kb", action="store_true")
    parser.add_argument("--ado-org", default=None)
    parser.add_argument("--ado-project", default=None)
    parser.add_argument("--disable-ado", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--non-interactive", action="store_true")
    args = parser.parse_args(argv)

    repo_root = resolve_repo_root()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = repo_root / config_path

    if config_path.exists() and not args.overwrite and not args.non_interactive:
        response = input(f"{config_path.relative_to(repo_root).as_posix()} exists. Overwrite? [y/N] ").strip().lower()
        if response not in {"y", "yes"}:
            print("Configuration unchanged.")
            return 0
    elif config_path.exists() and not args.overwrite and args.non_interactive:
        print(f"ERROR: {config_path.as_posix()} exists. Pass --overwrite to replace it.", file=sys.stderr)
        return 1

    config = _load_base_config(repo_root, DEFAULT_CONFIG)
    if args.non_interactive or any(
        [
            args.dev_org,
            args.validation_org is not None,
            args.kb_repo is not None,
            args.kb_branch,
            args.enable_kb,
            args.disable_kb,
            args.ado_org is not None,
            args.ado_project is not None,
            args.disable_ado,
        ]
    ):
        _apply_args(config, args)
    else:
        _interactive_update(config)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {_display_path(config_path, repo_root)}")

    ado_org = config.get("azure_devops", {}).get("organization", "").strip()
    if ado_org and ado_org != "YOUR_ADO_ORG":
        _patch_mcp_json(repo_root, ado_org)

    print("No passwords, Salesforce tokens, or secrets were requested or stored.")
    print("")
    print("Next steps:")
    alias = config["salesforce"]["default_dev_org_alias"] or "IntDev"
    print(f"- sf org login web --alias {alias}")
    print("- make doctor")
    print("- make ai-index-repo")
    if config["knowledge_base"]["enabled"]:
        print(f"- make knowledge-sync KB_REPO={mask_sensitive(config['knowledge_base']['repo_url'])}")
        print("- make knowledge-index")
    if config.get("azure_devops", {}).get("enabled"):
        print("- Start VS Code MCP server `ado-remote-mcp`, then run /fetch-us <WORK_ITEM_ID>")
    return 0


def _load_base_config(repo_root: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    for relative in (".ai/config/workspace.local.json.example", ".ai/config/workspace.example.json"):
        path = repo_root / relative
        if path.exists():
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                return loaded
    return json.loads(json.dumps(fallback))


def _apply_args(config: dict[str, Any], args: argparse.Namespace) -> None:
    salesforce = config.setdefault("salesforce", {})
    knowledge = config.setdefault("knowledge_base", {})
    azure_devops = config.setdefault("azure_devops", {})
    if args.dev_org:
        salesforce["default_dev_org_alias"] = args.dev_org
    if args.validation_org is not None:
        salesforce["validation_org_alias"] = args.validation_org
    if args.kb_repo is not None:
        knowledge["repo_url"] = args.kb_repo
    if args.kb_branch:
        knowledge["branch"] = args.kb_branch
    if args.enable_kb:
        knowledge["enabled"] = True
    if args.disable_kb:
        knowledge["enabled"] = False
    if knowledge.get("repo_url") and not args.disable_kb:
        knowledge["enabled"] = True
    if args.ado_org is not None:
        azure_devops["organization"] = args.ado_org
        azure_devops["enabled"] = True
    if args.ado_project is not None:
        azure_devops["default_project"] = args.ado_project
        azure_devops["enabled"] = True
    if args.disable_ado:
        azure_devops["enabled"] = False


def _interactive_update(config: dict[str, Any]) -> None:
    salesforce = config.setdefault("salesforce", {})
    knowledge = config.setdefault("knowledge_base", {})
    azure_devops = config.setdefault("azure_devops", {})
    salesforce["default_dev_org_alias"] = _prompt("Default Salesforce dev org alias", str(salesforce.get("default_dev_org_alias") or "IntDev"))
    salesforce["validation_org_alias"] = _prompt("Validation org alias (optional)", str(salesforce.get("validation_org_alias") or ""))
    ado_org = _prompt("Azure DevOps organization", str(azure_devops.get("organization") or "YOUR_ADO_ORG"))
    azure_devops["organization"] = ado_org
    azure_devops["default_project"] = _prompt("Azure DevOps default project (optional)", str(azure_devops.get("default_project") or ""))
    ado_enabled = _prompt("Enable Azure DevOps MCP Work Item fetch? yes/no", "yes" if bool(azure_devops.get("enabled", True)) else "no").lower()
    azure_devops["enabled"] = ado_enabled in {"y", "yes", "true", "1"}
    kb_repo = _prompt("Knowledge Base repo URL (optional)", str(knowledge.get("repo_url") or ""))
    knowledge["repo_url"] = kb_repo
    knowledge["branch"] = _prompt("Knowledge Base branch", str(knowledge.get("branch") or "main"))
    default_enabled = "yes" if bool(knowledge.get("enabled") or kb_repo) else "no"
    enabled = _prompt("Enable Knowledge Base sync? yes/no", default_enabled).lower()
    knowledge["enabled"] = enabled in {"y", "yes", "true", "1"}


def _prompt(label: str, default: str) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value if value else default


def _patch_mcp_json(repo_root: Path, ado_org: str) -> None:
    mcp_path = repo_root / ".vscode" / "mcp.json"
    if not mcp_path.exists():
        return
    original = mcp_path.read_text(encoding="utf-8")
    if "YOUR_ADO_ORG" not in original:
        return
    patched = original.replace("YOUR_ADO_ORG", ado_org)
    mcp_path.write_text(patched, encoding="utf-8")
    print(f"Updated .vscode/mcp.json with ADO organization: {ado_org}")


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
