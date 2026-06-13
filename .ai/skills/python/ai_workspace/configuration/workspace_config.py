"""Load and validate local Salesforce AI Workspace configuration."""

from __future__ import annotations

import copy
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


LOCAL_CONFIG = Path(".ai/config/workspace.local.json")
EXAMPLE_CONFIG = Path(".ai/config/workspace.example.json")

FORBIDDEN_SECURITY_FLAGS = (
    "allow_salesforce_writes",
    "allow_config_apply",
    "allow_external_llm_apis",
    "allow_arbitrary_mcp_file_reads",
)

DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "workspace": {
        "name": "salesforce-ai-workspace",
        "description": "Copilot-only Salesforce AI Workspace for Salesforce/KimbleOne development",
    },
    "paths": {
        "repo_root": ".",
        "ai_root": ".ai",
        "python_tools_root": ".ai/skills/python",
        "context_root": ".ai/context",
        "context_index_dir": ".ai/context/index",
        "work_items_dir": ".ai/context/work-items",
        "outputs_dir": ".ai/outputs",
        "knowledge_root": ".ai/knowledge",
        "knowledge_vendor_dir": ".ai/vendor/knowledge-base",
        "specs_proposed_dir": "specs/proposed",
        "specs_approved_dir": "specs/approved",
        "qa_docs_dir": "docs/qa-how-to-test",
        "architecture_docs_dir": "docs/architecture",
    },
    "salesforce": {
        "default_dev_org_alias": "IntDev",
        "validation_org_alias": "",
        "login_url": "https://login.salesforce.com",
        "use_devops_center": True,
        "devops_center_is_official_metadata_promotion": True,
    },
    "knowledge_base": {
        "enabled": False,
        "repo_url": "",
        "branch": "main",
        "sync_on_setup": False,
    },
    "azure_devops": {
        "enabled": True,
        "organization": "YOUR_ADO_ORG",
        "default_project": "",
        "mcp_server_name": "ado-remote-mcp",
    },
    "azure_wiki": {
        "enabled": False,
        "repo_url": "",
        "branch": "main",
        "vendor_dir": ".ai/vendor/azure-wiki",
        "default_draft_branch_prefix": "docs/ai-wiki",
        "default_proposed_root": "_Proposed",
        "require_human_approval": True,
        "allow_direct_push_to_default_branch": False,
        "push_enabled": False,
    },
    "python": {
        "min_version": "3.11",
        "use_venv": True,
        "venv_path": ".venv",
    },
    "node": {
        "required": False,
        "min_version": "",
    },
    "salesforce_cli": {
        "required": True,
        "command": "sf",
    },
    "github": {
        "requires_git": True,
        "requires_github_cli": False,
    },
    "security": {
        "allow_salesforce_writes": False,
        "allow_config_apply": False,
        "allow_external_llm_apis": False,
        "allow_arbitrary_mcp_file_reads": False,
    },
}


def load_workspace_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load workspace config, merge defaults, and apply environment overrides."""

    repo_root = resolve_repo_root()
    selected = _select_config_path(path, repo_root)
    loaded: dict[str, Any] = {}
    warnings: list[str] = []

    if selected.exists():
        try:
            data = json.loads(selected.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON config at {selected}: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"Workspace config must be a JSON object: {selected}")
        loaded = data
    elif path:
        warnings.append(f"Configured workspace file does not exist; using defaults: {selected.as_posix()}")

    config = _deep_merge(DEFAULT_CONFIG, loaded)
    _apply_env_overrides(config)
    config["_meta"] = {
        "repo_root": repo_root.as_posix(),
        "config_path": selected.as_posix(),
        "config_exists": selected.exists(),
        "warnings": warnings,
    }
    return config


def get_path(config: dict[str, Any], key: str) -> Path:
    repo_root = Path(config.get("_meta", {}).get("repo_root") or resolve_repo_root())
    value = str(config.get("paths", {}).get(key) or DEFAULT_CONFIG["paths"].get(key) or "")
    if not value:
        raise KeyError(f"Unknown workspace path key: {key}")
    path = Path(value)
    if key == "repo_root":
        return repo_root
    return path if path.is_absolute() else repo_root / path


def get_salesforce_alias(config: dict[str, Any], key: str = "default_dev_org_alias") -> str:
    return str(config.get("salesforce", {}).get(key) or "").strip()


def get_knowledge_config(config: dict[str, Any]) -> dict[str, Any]:
    value = config.get("knowledge_base")
    return dict(value) if isinstance(value, dict) else {}


def resolve_repo_root() -> Path:
    env_root = os.environ.get("AI_WORKSPACE_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / "AGENTS.md").exists() or (candidate / "sfdx-project.json").exists() or (candidate / "Makefile").exists():
            return candidate
    return current


def ensure_required_dirs(config: dict[str, Any]) -> list[str]:
    created: list[str] = []
    for key in (
        "ai_root",
        "context_root",
        "context_index_dir",
        "work_items_dir",
        "outputs_dir",
        "knowledge_root",
        "specs_proposed_dir",
        "specs_approved_dir",
        "qa_docs_dir",
        "architecture_docs_dir",
    ):
        path = get_path(config, key)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(path.relative_to(get_path(config, "repo_root")).as_posix())
    return created


def validate_workspace_config(config: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for config and local environment."""

    errors: list[str] = []
    warnings: list[str] = list(config.get("_meta", {}).get("warnings") or [])

    if not config.get("version"):
        errors.append("Config is missing required `version`.")

    min_version = str(config.get("python", {}).get("min_version") or "3.11")
    if not _python_version_ok(min_version):
        errors.append(f"Python {min_version}+ is required; current Python is {_current_python_version()}.")

    security = config.get("security") if isinstance(config.get("security"), dict) else {}
    for flag in FORBIDDEN_SECURITY_FLAGS:
        if bool(security.get(flag)):
            errors.append(f"Forbidden security flag is enabled: security.{flag}")

    paths = config.get("paths") if isinstance(config.get("paths"), dict) else {}
    if not paths:
        errors.append("Config is missing `paths` mapping.")
    else:
        for key in ("ai_root", "context_index_dir", "work_items_dir", "outputs_dir", "knowledge_root"):
            if not paths.get(key):
                warnings.append(f"Config path `{key}` is missing; default will be used.")

    return errors, warnings


def mask_sensitive(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"(https?://)[^/@]+@", r"\1[REDACTED]@", text)
    text = re.sub(r"([?&](?:token|access_token|client_secret|password)=)[^&]+", r"\1[REDACTED]", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(sk|xoxb)-[A-Za-z0-9_-]{8,}\b", r"\1-[REDACTED]", text)
    return text


def _select_config_path(path: str | Path | None, repo_root: Path) -> Path:
    env_path = os.environ.get("AI_WORKSPACE_CONFIG")
    raw = path or env_path
    if raw:
        selected = Path(raw)
        return selected.expanduser().resolve() if selected.is_absolute() else (repo_root / selected).resolve()
    local = repo_root / LOCAL_CONFIG
    if local.exists():
        return local.resolve()
    return (repo_root / EXAMPLE_CONFIG).resolve()


def _apply_env_overrides(config: dict[str, Any]) -> None:
    salesforce = config.setdefault("salesforce", {})
    knowledge = config.setdefault("knowledge_base", {})
    if os.environ.get("SF_DEV_ORG_ALIAS"):
        salesforce["default_dev_org_alias"] = os.environ["SF_DEV_ORG_ALIAS"]
    if os.environ.get("SF_VALIDATION_ORG_ALIAS"):
        salesforce["validation_org_alias"] = os.environ["SF_VALIDATION_ORG_ALIAS"]
    if os.environ.get("KB_REPO"):
        knowledge["repo_url"] = os.environ["KB_REPO"]
        knowledge["enabled"] = True
    if os.environ.get("KB_BRANCH"):
        knowledge["branch"] = os.environ["KB_BRANCH"]
    azure_devops = config.setdefault("azure_devops", {})
    if os.environ.get("ADO_ORG"):
        azure_devops["organization"] = os.environ["ADO_ORG"]
        azure_devops["enabled"] = True
    if os.environ.get("ADO_PROJECT"):
        azure_devops["default_project"] = os.environ["ADO_PROJECT"]
        azure_devops["enabled"] = True
    azure_wiki = config.setdefault("azure_wiki", {})
    if os.environ.get("AZURE_WIKI_REPO"):
        azure_wiki["repo_url"] = os.environ["AZURE_WIKI_REPO"]
        azure_wiki["enabled"] = True
    if os.environ.get("AZURE_WIKI_BRANCH"):
        azure_wiki["branch"] = os.environ["AZURE_WIKI_BRANCH"]
    if os.environ.get("AZURE_WIKI_VENDOR_DIR"):
        azure_wiki["vendor_dir"] = os.environ["AZURE_WIKI_VENDOR_DIR"]
    if os.environ.get("AI_WORKSPACE_ROOT"):
        config.setdefault("paths", {})["repo_root"] = os.environ["AI_WORKSPACE_ROOT"]


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _python_version_ok(min_version: str) -> bool:
    required = _version_tuple(min_version)
    current = sys.version_info[: len(required)]
    return tuple(current) >= required


def _current_python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def _version_tuple(value: str) -> tuple[int, ...]:
    parts = []
    for part in value.split("."):
        if not part:
            continue
        try:
            parts.append(int(part))
        except ValueError:
            break
    return tuple(parts or [3, 11])
