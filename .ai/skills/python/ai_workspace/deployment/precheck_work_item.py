"""Run local Work Item prechecks before commit or PR."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_workspace.deployment.git_utils import (
    get_changed_files,
    get_current_branch,
    git_root,
    run_git,
)
from ai_workspace.deployment.validate_metadata_scope import (
    load_metadata_scope,
    validate_changed_files_against_scope,
)
from ai_workspace.security.no_raw_data import scan_paths_for_raw_data
from ai_workspace.security.no_salesforce_ids import scan_paths_for_salesforce_ids


SEVERITIES = ("blocking", "high", "medium", "low")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local Work Item branch prechecks.")
    parser.add_argument("--work-item", required=True)
    parser.add_argument("--work-item-dir")
    parser.add_argument("--base-ref", default="HEAD~1")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out-dir", default=".ai/outputs/precheck")
    parser.add_argument("--fail-on-high", action="store_true")
    args = parser.parse_args(argv)

    try:
        repo_root = git_root(args.repo_root)
        branch = get_current_branch(repo_root)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    findings_by_check: dict[str, list[dict[str, Any]]] = {
        "metadata_scope": [],
        "salesforce_ids": [],
        "raw_data": [],
        "required_artifacts": [],
    }

    changed_files: list[str] = []
    try:
        changed_files = get_changed_files(args.base_ref, repo_root)
    except RuntimeError as exc:
        findings_by_check["metadata_scope"].append(
            {
                "severity": "high",
                "type": "base_ref_unavailable",
                "path": "",
                "message": f"Could not diff against base ref `{args.base_ref}`: {exc}. Falling back to local tracked/untracked file list.",
            }
        )
        changed_files = _fallback_changed_files(repo_root)

    work_item_dir = Path(args.work_item_dir or f".ai/context/work-items/{args.work_item}")
    try:
        scope = load_metadata_scope(str(work_item_dir / "metadata-scope.yaml"))
        findings_by_check["metadata_scope"].extend(
            validate_changed_files_against_scope(changed_files, scope)
        )
    except (OSError, ValueError) as exc:
        findings_by_check["metadata_scope"].append(
            {
                "severity": "high",
                "type": "metadata_scope_parse_error",
                "path": str(work_item_dir / "metadata-scope.yaml"),
                "message": f"Could not parse metadata scope: {exc}",
            }
        )

    findings_by_check["salesforce_ids"].extend(
        _with_type(scan_paths_for_salesforce_ids(changed_files, repo_root), "salesforce_id_candidate")
    )
    findings_by_check["raw_data"].extend(
        _with_type(scan_paths_for_raw_data(changed_files, repo_root), "raw_data_or_secret_risk")
    )
    findings_by_check["required_artifacts"].extend(
        _required_artifact_findings(args.work_item, work_item_dir, Path(repo_root))
    )

    checks = {
        check_name: {
            "status": _check_status(findings),
            "findings": findings,
        }
        for check_name, findings in findings_by_check.items()
    }
    summary = _summary(findings_by_check)
    decision = _decision(summary, args.fail_on_high)
    generated_at = datetime.now(timezone.utc).isoformat()
    report = {
        "work_item": args.work_item,
        "branch": branch,
        "base_ref": args.base_ref,
        "changed_files": changed_files,
        "checks": checks,
        "summary": summary,
        "decision": decision,
        "generated_at": generated_at,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{args.work_item}.precheck.json"
    md_path = out_dir / f"{args.work_item}.precheck.md"
    json_path.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_markdown_report(report, work_item_dir, Path(repo_root)), encoding="utf-8")

    print(
        f"Precheck {decision}: blocking={summary['blocking']} high={summary['high']} "
        f"medium={summary['medium']} low={summary['low']}"
    )
    print(f"Wrote {md_path}")
    print(f"Wrote {json_path}")

    if summary["blocking"] > 0:
        return 1
    if args.fail_on_high and summary["high"] > 0:
        return 1
    return 0


def _fallback_changed_files(repo_root: str) -> list[str]:
    changed: set[str] = set()
    for command in (
        ["diff", "--name-only", "--"],
        ["diff", "--cached", "--name-only", "--"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        try:
            changed.update(line for line in run_git(command, repo_root).splitlines() if line.strip())
        except RuntimeError:
            continue
    return sorted(changed)


def _required_artifact_findings(work_item: str, work_item_dir: Path, repo_root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    checks = [
        (
            work_item_dir / "context-pack.md",
            "context_pack_missing",
            "medium",
            "context-pack.md is missing; run the context pack builder before design/precheck review.",
        ),
        (
            repo_root / "specs" / "proposed" / f"{work_item}.solution-design.md",
            "solution_design_missing",
            "medium",
            "No proposed solution design found for this Work Item.",
        ),
        (
            repo_root / "specs" / "approved" / f"{work_item}.solution-design.md",
            "approved_solution_design_missing",
            "low",
            "No approved solution design found for this Work Item.",
        ),
        (
            repo_root / "docs" / "qa-how-to-test" / f"{work_item}.md",
            "qa_how_to_test_missing",
            "medium",
            "QA how-to-test document is missing for this Work Item.",
        ),
    ]

    proposed = checks[1][0].exists()
    approved = checks[2][0].exists()
    for path, finding_type, severity, message in checks:
        if finding_type in {"solution_design_missing", "approved_solution_design_missing"}:
            continue
        if not path.exists():
            findings.append({"severity": severity, "type": finding_type, "path": _display_path(path, repo_root), "message": message})
    if not proposed and not approved:
        findings.append(
            {
                "severity": "medium",
                "type": "solution_design_missing",
                "path": f"specs/proposed/{work_item}.solution-design.md or specs/approved/{work_item}.solution-design.md",
                "message": "No solution design found for this Work Item.",
            }
        )
    return findings


def _with_type(findings: list[dict[str, Any]], finding_type: str) -> list[dict[str, Any]]:
    enriched = []
    for finding in findings:
        item = dict(finding)
        item.setdefault("type", finding_type)
        enriched.append(item)
    return enriched


def _check_status(findings: list[dict[str, Any]]) -> str:
    if any(finding.get("severity") == "blocking" for finding in findings):
        return "blocked"
    if findings:
        return "warnings"
    return "ok"


def _summary(findings_by_check: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    counts = {severity: 0 for severity in SEVERITIES}
    for findings in findings_by_check.values():
        for finding in findings:
            severity = str(finding.get("severity") or "low")
            if severity in counts:
                counts[severity] += 1
    return counts


def _decision(summary: dict[str, int], fail_on_high: bool) -> str:
    if summary["blocking"] > 0 or (fail_on_high and summary["high"] > 0):
        return "BLOCKED"
    if any(summary[severity] > 0 for severity in ("high", "medium", "low")):
        return "PASS_WITH_WARNINGS"
    return "PASS"


def _markdown_report(report: dict[str, Any], work_item_dir: Path, repo_root: Path) -> str:
    work_item = str(report["work_item"])
    lines = [
        f"# Work Item Precheck — {work_item}",
        "",
        "## Decision",
        "",
        str(report["decision"]),
        "",
        "## Branch and Diff",
        "",
        f"- Branch: `{report['branch']}`",
        f"- Base ref: `{report['base_ref']}`",
        "- Changed files:",
    ]
    changed_files = report.get("changed_files") or []
    if changed_files:
        for path in changed_files:
            lines.append(f"  - `{path}`")
    else:
        lines.append("  - none")

    summary = report.get("summary", {})
    lines.extend(
        [
            "",
            "## Summary",
            "",
            "| Severity | Count |",
            "| --- | ---: |",
        ]
    )
    for severity in SEVERITIES:
        lines.append(f"| {severity.title()} | {summary.get(severity, 0)} |")

    lines.extend(["", "## Findings", ""])
    all_findings = _all_findings(report)
    for severity, title in (
        ("blocking", "Blocking"),
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    ):
        lines.append(f"### {title}")
        lines.append("")
        matching = [finding for finding in all_findings if finding.get("severity") == severity]
        if not matching:
            lines.append("- None")
        else:
            for finding in matching:
                path = finding.get("path") or ""
                path_text = f" `{path}`:" if path else ""
                lines.append(f"- **{finding.get('type', 'finding')}**{path_text} {finding.get('message', '')}")
        lines.append("")

    context_pack = work_item_dir / "context-pack.md"
    proposed_design = repo_root / "specs" / "proposed" / f"{work_item}.solution-design.md"
    approved_design = repo_root / "specs" / "approved" / f"{work_item}.solution-design.md"
    qa_doc = repo_root / "docs" / "qa-how-to-test" / f"{work_item}.md"
    lines.extend(
        [
            "## Required Artifacts",
            "",
            f"- context-pack.md: {'present' if context_pack.exists() else 'missing'}",
            f"- solution design: {'present' if proposed_design.exists() or approved_design.exists() else 'missing'}",
            f"- QA how-to-test: {'present' if qa_doc.exists() else 'missing'}",
            "",
            "## Recommended Next Steps",
            "",
            "- Address blocking findings before commit or PR.",
            "- Review high findings with the Work Item owner or Salesforce architect.",
            "- Confirm metadata scope if `metadata-scope.yaml` is missing or incomplete.",
            "- Generate or update context pack, solution design, and QA how-to-test artifacts as needed.",
        ]
    )
    return "\n".join(lines) + "\n"


def _all_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    checks = report.get("checks")
    if not isinstance(checks, dict):
        return findings
    for check in checks.values():
        if isinstance(check, dict) and isinstance(check.get("findings"), list):
            findings.extend(check["findings"])
    return findings


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
