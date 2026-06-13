"""Health checks for the local Salesforce AI Workspace."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_workspace.configuration.workspace_config import (
    FORBIDDEN_SECURITY_FLAGS,
    get_path,
    get_salesforce_alias,
    load_workspace_config,
    mask_sensitive,
    validate_workspace_config,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Salesforce AI Workspace health checks.")
    parser.add_argument("--config", default=".ai/config/workspace.local.json")
    parser.add_argument("--json-out", default=".ai/outputs/doctor/doctor.json")
    parser.add_argument("--md-out", default=".ai/outputs/doctor/doctor.md")
    parser.add_argument("--check-salesforce-auth", action="store_true")
    parser.add_argument("--check-knowledge", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = run_doctor(
            config_path=args.config,
            check_salesforce_auth=args.check_salesforce_auth,
            check_knowledge=args.check_knowledge,
            strict=args.strict,
        )
    except ValueError as exc:
        print(f"CONFIGURATION ERROR: {exc}", file=sys.stderr)
        return 2

    _write_reports(report, Path(args.json_out), Path(args.md_out))
    print(_console_summary(report))
    if report["summary"]["status"] == "FAIL":
        return 1
    if args.strict and report["summary"]["warnings"] > 0:
        return 1
    return 0


def run_doctor(
    config_path: str | Path | None = None,
    check_salesforce_auth: bool = False,
    check_knowledge: bool = False,
    strict: bool = False,
) -> dict[str, Any]:
    config = load_workspace_config(config_path)
    repo_root = get_path(config, "repo_root")
    checks: list[dict[str, Any]] = []

    config_errors, config_warnings = validate_workspace_config(config)
    for warning in config_warnings:
        checks.append(_check("configuration", "Config warning", "WARN", warning))
    for error in config_errors:
        checks.append(_check("configuration", "Config error", "FAIL", error))

    checks.extend(_environment_checks(config))
    checks.extend(_required_file_checks(repo_root))
    checks.extend(_directory_checks(config))
    checks.extend(_security_checks(config))
    checks.extend(_salesforce_cli_checks(config, check_salesforce_auth))
    checks.extend(_azure_devops_checks(config, repo_root))
    if check_knowledge or bool(config.get("knowledge_base", {}).get("enabled")):
        checks.extend(_knowledge_checks(config))

    errors = sum(1 for check in checks if check["status"] == "FAIL")
    warnings = sum(1 for check in checks if check["status"] == "WARN")
    status = "FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "strict": strict,
        "summary": {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "passed": sum(1 for check in checks if check["status"] == "PASS"),
        },
        "config": {
            "path": config.get("_meta", {}).get("config_path"),
            "exists": bool(config.get("_meta", {}).get("config_exists")),
            "workspace": config.get("workspace", {}),
        },
        "repo_root": repo_root.as_posix(),
        "checks": checks,
        "next_steps": _next_steps(config),
    }


def _environment_checks(config: dict[str, Any]) -> list[dict[str, Any]]:
    checks = []
    min_version = str(config.get("python", {}).get("min_version") or "3.11")
    current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append(_check("environment", "Python version", "PASS", f"Current Python {current}; required {min_version}+."))

    if bool(config.get("github", {}).get("requires_git", True)):
        git_path = shutil.which("git")
        checks.append(
            _check("tools", "Git installed", "PASS" if git_path else "WARN", git_path or "Git not found on PATH.")
        )
    if bool(config.get("github", {}).get("requires_github_cli", False)):
        gh_path = shutil.which("gh")
        checks.append(
            _check("tools", "GitHub CLI installed", "PASS" if gh_path else "WARN", gh_path or "GitHub CLI not found on PATH.")
        )
    return checks


def _required_file_checks(repo_root: Path) -> list[dict[str, Any]]:
    files = [
        "Makefile",
        ".vscode/tasks.json",
        ".github/copilot-instructions.md",
        "AGENTS.md",
    ]
    return [
        _check("required_files", path, "PASS" if (repo_root / path).exists() else "WARN", "found" if (repo_root / path).exists() else "missing")
        for path in files
    ]


def _directory_checks(config: dict[str, Any]) -> list[dict[str, Any]]:
    keys = [
        "ai_root",
        "context_index_dir",
        "work_items_dir",
        "outputs_dir",
        "knowledge_root",
        "specs_proposed_dir",
        "specs_approved_dir",
        "architecture_docs_dir",
        "qa_docs_dir",
    ]
    checks = []
    for key in keys:
        path = get_path(config, key)
        checks.append(_check("required_directories", key, "PASS" if path.exists() and path.is_dir() else "WARN", path.as_posix()))
    return checks


def _security_checks(config: dict[str, Any]) -> list[dict[str, Any]]:
    security = config.get("security") if isinstance(config.get("security"), dict) else {}
    checks = []
    for flag in FORBIDDEN_SECURITY_FLAGS:
        enabled = bool(security.get(flag))
        checks.append(
            _check(
                "security_guardrails",
                flag,
                "FAIL" if enabled else "PASS",
                "must remain false" if enabled else "false",
            )
        )
    return checks


def _salesforce_cli_checks(config: dict[str, Any], check_auth: bool) -> list[dict[str, Any]]:
    sf_config = config.get("salesforce_cli") if isinstance(config.get("salesforce_cli"), dict) else {}
    required = bool(sf_config.get("required", True))
    command = str(sf_config.get("command") or "sf")
    command_path = shutil.which(command)
    status_if_missing = "WARN" if required else "PASS"
    checks = [
        _check("salesforce_cli", "Salesforce CLI command", "PASS" if command_path else status_if_missing, command_path or f"{command} not found on PATH.")
    ]
    if command_path:
        version = _run([command, "--version"])
        checks.append(_check("salesforce_cli", "sf --version", "PASS" if version["ok"] else "WARN", version["output"]))
    if check_auth:
        alias = get_salesforce_alias(config)
        if not alias:
            checks.append(_check("salesforce_cli", "Salesforce org auth", "WARN", "No default dev org alias configured."))
        elif command_path:
            result = _run([command, "org", "display", "--target-org", alias, "--json"])
            message = "authenticated" if result["ok"] else f"Run: sf org login web --alias {alias}"
            checks.append(_check("salesforce_cli", f"Salesforce org auth: {alias}", "PASS" if result["ok"] else "WARN", message))
        else:
            checks.append(_check("salesforce_cli", "Salesforce org auth", "WARN", f"Install Salesforce CLI, then run: sf org login web --alias {alias}"))
    return checks


def _knowledge_checks(config: dict[str, Any]) -> list[dict[str, Any]]:
    kb = config.get("knowledge_base") if isinstance(config.get("knowledge_base"), dict) else {}
    repo_root = get_path(config, "repo_root")
    repo_url = str(kb.get("repo_url") or "")
    knowledge_root = get_path(config, "knowledge_root")
    sync_state = knowledge_root / "sync-state.json"
    index = repo_root / ".ai/context/index/knowledge-cards.jsonl"
    return [
        _check("knowledge_base", "Knowledge enabled", "PASS" if bool(kb.get("enabled")) else "WARN", str(bool(kb.get("enabled")))),
        _check("knowledge_base", "Knowledge repo URL", "PASS" if repo_url else "WARN", mask_sensitive(repo_url) or "not configured"),
        _check("knowledge_base", "Knowledge sync state", "PASS" if sync_state.exists() else "WARN", sync_state.as_posix()),
        _check("knowledge_base", "Knowledge cards index", "PASS" if index.exists() else "WARN", index.as_posix()),
    ]


def _azure_devops_checks(config: dict[str, Any], repo_root: Path) -> list[dict[str, Any]]:
    ado = config.get("azure_devops") if isinstance(config.get("azure_devops"), dict) else {}
    if not bool(ado.get("enabled", False)):
        return [_check("azure_devops", "Azure DevOps MCP enabled", "WARN", "disabled")]
    organization = str(ado.get("organization") or "")
    project = str(ado.get("default_project") or "")
    server_name = str(ado.get("mcp_server_name") or "ado-remote-mcp")
    mcp_path = repo_root / ".vscode/mcp.json"
    mcp_status = "WARN"
    mcp_message = "missing .vscode/mcp.json"
    if mcp_path.exists():
        try:
            loaded = json.loads(mcp_path.read_text(encoding="utf-8"))
            servers = loaded.get("servers") if isinstance(loaded, dict) else {}
            server = servers.get(server_name) if isinstance(servers, dict) else None
            if isinstance(server, dict):
                mcp_status = "PASS"
                mcp_message = str(server.get("url") or server.get("command") or "configured")
            else:
                mcp_message = f"server `{server_name}` not found in .vscode/mcp.json"
        except json.JSONDecodeError as exc:
            mcp_message = f"invalid .vscode/mcp.json: {exc}"
    org_status = "PASS"
    org_message = organization
    if not organization or organization == "YOUR_ADO_ORG":
        org_status = "WARN"
        org_message = "Set azure_devops.organization in local config and update .vscode/mcp.json URL before using /fetch-us."
    return [
        _check("azure_devops", "Azure DevOps MCP enabled", "PASS", "true"),
        _check("azure_devops", "Azure DevOps organization", org_status, mask_sensitive(org_message)),
        _check("azure_devops", "Azure DevOps default project", "PASS" if project else "WARN", project or "optional project is not configured"),
        _check("azure_devops", "Azure DevOps MCP server", mcp_status, mcp_message),
    ]


def _run(args: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(args, text=True, capture_output=True, check=False, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "output": str(exc)}
    output = (result.stdout or result.stderr or "").strip()
    return {"ok": result.returncode == 0, "output": output[:2000]}


def _write_reports(report: dict[str, Any], json_out: Path, md_out: Path) -> None:
    repo_root = Path(str(report.get("repo_root") or Path.cwd())).resolve()
    json_path = json_out if json_out.is_absolute() else repo_root / json_out
    md_path = md_out if md_out.is_absolute() else repo_root / md_out
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_markdown_report(report), encoding="utf-8")


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# AI Workspace Doctor Report",
        "",
        "## Summary",
        "",
        f"- Status: `{report['summary']['status']}`",
        f"- Passed: {report['summary']['passed']}",
        f"- Warnings: {report['summary']['warnings']}",
        f"- Errors: {report['summary']['errors']}",
        "",
    ]
    for section in (
        "environment",
        "configuration",
        "tools",
        "salesforce_cli",
        "azure_devops",
        "knowledge_base",
        "required_directories",
        "required_files",
        "security_guardrails",
    ):
        lines.append(f"## {_title(section)}")
        lines.append("")
        selected = [check for check in report["checks"] if check["category"] == section]
        if not selected:
            lines.append("- No checks in this category.")
        for check in selected:
            lines.append(f"- `{check['status']}` {check['name']}: {check['message']}")
        lines.append("")
    lines.append("## Recommended Next Steps")
    lines.append("")
    lines.extend(f"- {step}" for step in report.get("next_steps", []))
    return "\n".join(lines).rstrip() + "\n"


def _console_summary(report: dict[str, Any]) -> str:
    lines = [
        f"AI Workspace doctor: {report['summary']['status']}",
        f"Passed={report['summary']['passed']} warnings={report['summary']['warnings']} errors={report['summary']['errors']}",
        f"Wrote .ai/outputs/doctor/doctor.md",
        f"Wrote .ai/outputs/doctor/doctor.json",
    ]
    for check in report["checks"]:
        if check["status"] in {"WARN", "FAIL"}:
            lines.append(f"- {check['status']} {check['name']}: {check['message']}")
    return "\n".join(lines)


def _next_steps(config: dict[str, Any]) -> list[str]:
    alias = get_salesforce_alias(config) or "IntDev"
    return [
        f"Authenticate Salesforce if needed: sf org login web --alias {alias}",
        "Run: make setup",
        "Run: make ai-index-repo",
        "Run: make knowledge-index",
        "Build context: make ai-context WORK_ITEM=EXAMPLE-WI QUERY=\"example\"",
    ]


def _check(category: str, name: str, status: str, message: str) -> dict[str, str]:
    return {"category": category, "name": name, "status": status, "message": message}


def _title(value: str) -> str:
    return value.replace("_", " ").title()


if __name__ == "__main__":
    raise SystemExit(main())
