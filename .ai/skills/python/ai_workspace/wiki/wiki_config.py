"""Configuration helpers for Azure DevOps Wiki draft publication."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_workspace.configuration.workspace_config import get_path, load_workspace_config
from ai_workspace.security.redactor import load_simple_yaml


DEFAULT_POLICY_PATH = Path(".ai/wiki/wiki-publish-policy.yaml")
DEFAULT_MODULE_MAP_PATH = Path(".ai/wiki/module-map.yaml")


def load_azure_wiki_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load the Azure Wiki section from workspace config."""

    config = load_workspace_config(config_path)
    wiki = config.get("azure_wiki") if isinstance(config.get("azure_wiki"), dict) else {}
    return {
        "enabled": bool(wiki.get("enabled", False)),
        "repo_url": str(wiki.get("repo_url") or ""),
        "branch": str(wiki.get("branch") or "main"),
        "vendor_dir": str(wiki.get("vendor_dir") or ".ai/vendor/azure-wiki"),
        "default_draft_branch_prefix": str(wiki.get("default_draft_branch_prefix") or "docs/ai-wiki"),
        "default_proposed_root": str(wiki.get("default_proposed_root") or "_Proposed"),
        "require_human_approval": bool(wiki.get("require_human_approval", True)),
        "allow_direct_push_to_default_branch": bool(wiki.get("allow_direct_push_to_default_branch", False)),
        "push_enabled": bool(wiki.get("push_enabled", False)),
        "_workspace": config,
        "_repo_root": get_path(config, "repo_root"),
    }


def load_policy(path: str | Path = DEFAULT_POLICY_PATH) -> dict[str, Any]:
    """Load wiki publication policy from the workspace YAML subset."""

    policy_path = Path(path)
    if not policy_path.exists():
        return {}
    loaded = load_simple_yaml(str(policy_path))
    if not isinstance(loaded, dict):
        raise ValueError(f"Wiki publish policy must be a mapping: {policy_path}")
    return loaded


def load_module_map(path: str | Path = DEFAULT_MODULE_MAP_PATH) -> dict[str, Any]:
    """Load the module routing map from the workspace YAML subset."""

    map_path = Path(path)
    if not map_path.exists():
        return {}
    loaded = load_simple_yaml(str(map_path))
    if not isinstance(loaded, dict):
        raise ValueError(f"Wiki module map must be a mapping: {map_path}")
    return loaded


def policy_list(policy: dict[str, Any], *keys: str) -> list[str]:
    value: Any = policy
    for key in keys:
        if not isinstance(value, dict):
            return []
        value = value.get(key)
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def policy_bool(policy: dict[str, Any], default: bool, *keys: str) -> bool:
    value: Any = policy
    for key in keys:
        if not isinstance(value, dict):
            return default
        value = value.get(key)
    return default if value is None else bool(value)


def policy_string(policy: dict[str, Any], default: str, *keys: str) -> str:
    value: Any = policy
    for key in keys:
        if not isinstance(value, dict):
            return default
        value = value.get(key)
    return default if value is None else str(value)
