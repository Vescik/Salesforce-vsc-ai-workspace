"""Prepare Azure DevOps Wiki draft pages with a human approval gate."""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_workspace.configuration.workspace_config import resolve_repo_root
from ai_workspace.wiki import wiki_git
from ai_workspace.wiki.wiki_config import load_azure_wiki_config, load_module_map, load_policy, policy_bool
from ai_workspace.wiki.wiki_page_builder import build_wiki_page, read_source_text
from ai_workspace.wiki.wiki_router import explain_routing_decision, propose_target_path, slugify_title
from ai_workspace.wiki.wiki_scanner import scan_wiki


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare Azure DevOps Wiki draft publication artifacts.")
    parser.add_argument("--work-item", required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--repo-url", default="")
    parser.add_argument("--branch", default="")
    parser.add_argument("--vendor-dir", default="")
    parser.add_argument("--module", default="")
    parser.add_argument("--target-path", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--prepare-branch", action="store_true")
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--approved", action="store_true")
    parser.add_argument("--approval-note", default="")
    parser.add_argument("--draft-branch", default="")
    parser.add_argument("--out-dir", default=".ai/outputs/wiki")
    parser.add_argument("--config", default=".ai/config/workspace.local.json")
    parser.add_argument("--policy", default=".ai/wiki/wiki-publish-policy.yaml")
    parser.add_argument("--module-map", default=".ai/wiki/module-map.yaml")
    args = parser.parse_args(argv)

    try:
        report = publish_wiki(args)
    except Exception as exc:  # noqa: BLE001 - CLI should fail with concise local message.
        print(f"ERROR: wiki publication preparation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Azure Wiki publication: {report['status']}")
    print(f"Target: {report.get('target_wiki_path') or '[none]'}")
    for path in report.get("report_paths", {}).values():
        print(f"Wrote {path}")
    if report.get("warnings"):
        print(f"Warnings: {len(report['warnings'])}")
    return 0 if report["status"] not in {"BLOCKED"} else 2


def publish_wiki(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = resolve_repo_root()
    out_dir = _resolve_inside_repo(Path(args.out_dir), repo_root)
    config = load_azure_wiki_config(args.config)
    policy = load_policy(args.policy)
    module_map = load_module_map(args.module_map)

    sources = _parse_sources(args.source)
    repo_url = (args.repo_url or config.get("repo_url") or "").strip()
    branch = (args.branch or config.get("branch") or "main").strip()
    vendor_dir = _resolve_inside_repo(Path(args.vendor_dir or str(config.get("vendor_dir") or ".ai/vendor/azure-wiki")), repo_root)
    title = (args.title or args.work_item).strip()
    dry_run = bool(args.dry_run or (not args.prepare_branch and not args.push))
    mode = "dry_run" if dry_run else ("push_branch_after_approval" if args.push else "prepare_branch")
    warnings: list[str] = []

    preflight = _preflight(
        args=args,
        repo_url=repo_url,
        branch=branch,
        title=title,
        sources=sources,
        mode=mode,
        config=config,
        policy=policy,
    )
    if preflight:
        report = _base_report(args, mode, "BLOCKED", repo_url, branch, vendor_dir, warnings=preflight)
        _write_reports(report, out_dir)
        return report

    wiki_dir = wiki_git.clone_or_update_repo(repo_url, branch, vendor_dir)
    default_branch = wiki_git.get_default_branch(wiki_dir)
    draft_branch = _draft_branch_name(args, config, title)
    if args.prepare_branch and draft_branch in {branch, default_branch}:
        report = _base_report(
            args,
            mode,
            "BLOCKED",
            repo_url,
            branch,
            vendor_dir,
            warnings=[f"Draft branch `{draft_branch}` matches the wiki default/base branch and is blocked."],
        )
        _write_reports(report, out_dir)
        return report

    wiki_index = scan_wiki(wiki_dir)
    source_text, source_warnings = read_source_text(sources, repo_root, policy)
    warnings.extend(source_warnings)
    decision = propose_target_path(
        wiki_index=wiki_index,
        module_map=module_map,
        source_text=source_text,
        work_item=args.work_item,
        title=title,
        explicit_module=args.module.strip(),
        explicit_target_path=args.target_path.strip(),
    )
    warnings.extend(decision.get("warnings", []))

    page = build_wiki_page(
        source_paths=sources,
        repo_root=repo_root,
        policy=policy,
        work_item=args.work_item,
        title=title,
        routing_decision=decision,
        approved=args.approved,
        approval_note=args.approval_note,
    )
    warnings.extend(page["warnings"])
    target_relative = str(decision["target_file_path"])
    target_file = _resolve_inside_wiki(Path(target_relative), wiki_dir)
    target_exists = target_file.exists()
    actual_relative = target_relative
    existing_diff = ""

    if target_exists:
        warnings.append(f"Target wiki page already exists and requires explicit review: {target_relative}")
        existing_text = target_file.read_text(encoding="utf-8", errors="replace")
        existing_diff = _unified_diff(existing_text, str(page["markdown"]), target_relative)
        if args.prepare_branch and not args.approved:
            actual_relative = f"_Proposed/Updates/{slugify_title(title)}-{args.work_item}-update-proposal.md"
            warnings.append(f"Existing page will not be overwritten without approval; writing update proposal to `{actual_relative}`.")

    if page.get("blocked"):
        report = _publication_report(
            args=args,
            mode=mode,
            status="BLOCKED",
            repo_url=repo_url,
            branch=branch,
            vendor_dir=vendor_dir,
            wiki_dir=wiki_dir,
            draft_branch=draft_branch,
            decision=decision,
            source_paths=sources,
            warnings=warnings,
            page_markdown=str(page["markdown"]),
            changed_files=[],
            existing_diff=existing_diff,
            actual_relative=actual_relative,
        )
        _write_reports(report, out_dir)
        return report

    changed_files: list[str] = []
    commit = ""
    pushed = False
    if dry_run:
        preview_path = _write_preview(out_dir, actual_relative, str(page["markdown"]))
        changed_files.append(preview_path.relative_to(repo_root).as_posix())
        status = "DRY_RUN"
    else:
        wiki_git.create_branch(wiki_dir, draft_branch)
        actual_file = _resolve_inside_wiki(Path(actual_relative), wiki_dir)
        actual_file.parent.mkdir(parents=True, exist_ok=True)
        actual_file.write_text(str(page["markdown"]), encoding="utf-8")
        if policy_bool(policy, True, "wiki", "update_order_files"):
            _update_order_file(actual_file, wiki_dir)
        changed_files = wiki_git.list_changed_files(wiki_dir)
        commit = wiki_git.commit_changes(wiki_dir, f"Prepare wiki draft for {args.work_item}")
        status = "BRANCH_PREPARED"
        if args.push:
            if draft_branch == default_branch:
                raise ValueError(f"Refusing to push default branch `{draft_branch}`.")
            wiki_git.push_branch(wiki_dir, draft_branch)
            pushed = True
            status = "BRANCH_PUSHED"

    report = _publication_report(
        args=args,
        mode=mode,
        status=status,
        repo_url=repo_url,
        branch=branch,
        vendor_dir=vendor_dir,
        wiki_dir=wiki_dir,
        draft_branch=draft_branch,
        decision=decision,
        source_paths=sources,
        warnings=warnings,
        page_markdown=str(page["markdown"]),
        changed_files=changed_files,
        existing_diff=existing_diff,
        actual_relative=actual_relative,
        commit=commit,
        pushed=pushed,
    )
    _write_reports(report, out_dir)
    return report


def _preflight(
    args: argparse.Namespace,
    repo_url: str,
    branch: str,
    title: str,
    sources: list[str],
    mode: str,
    config: dict[str, Any],
    policy: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if not repo_url:
        warnings.append("Azure Wiki repo URL is required. Pass AZURE_WIKI_REPO, --repo-url, or local workspace config.")
    if not branch:
        warnings.append("Azure Wiki branch is required.")
    if not title:
        warnings.append("--title is required unless inferable from Work Item ID.")
    if not sources:
        warnings.append("At least one --source artifact is required.")
    if args.push and not args.approved:
        warnings.append("--push is blocked unless --approved is also provided.")
    if args.push and policy_bool(policy, True, "approval", "require_human_approval") and not args.approval_note:
        warnings.append("--push with approval requires --approval-note for review traceability.")
    if args.push and not args.prepare_branch:
        warnings.append("--push requires --prepare-branch.")
    if args.push and not bool(config.get("push_enabled", False)):
        warnings.append("Azure Wiki branch push is blocked because azure_wiki.push_enabled is false in local config.")
    if mode not in set(policy.get("approval", {}).get("allowed_publish_modes", ["dry_run", "prepare_branch", "push_branch_after_approval"])):
        warnings.append(f"Publish mode `{mode}` is not allowed by policy.")
    return warnings


def _base_report(
    args: argparse.Namespace,
    mode: str,
    status: str,
    repo_url: str,
    branch: str,
    vendor_dir: Path,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "status": status,
        "mode": mode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "work_item": args.work_item,
        "title": args.title,
        "source_artifacts": _parse_sources(args.source),
        "repo_url": _mask_repo_url(repo_url),
        "branch": branch,
        "vendor_dir": vendor_dir.as_posix(),
        "warnings": warnings,
        "changed_files": [],
        "next_steps": ["Resolve blockers and rerun wiki-dry-run."],
    }


def _publication_report(
    args: argparse.Namespace,
    mode: str,
    status: str,
    repo_url: str,
    branch: str,
    vendor_dir: Path,
    wiki_dir: Path,
    draft_branch: str,
    decision: dict[str, Any],
    source_paths: list[str],
    warnings: list[str],
    page_markdown: str,
    changed_files: list[str],
    existing_diff: str,
    actual_relative: str,
    commit: str = "",
    pushed: bool = False,
) -> dict[str, Any]:
    page_preview = "\n".join(page_markdown.splitlines()[:80])
    return {
        "status": status,
        "mode": mode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "work_item": args.work_item,
        "title": args.title,
        "source_artifacts": source_paths,
        "repo_url": _mask_repo_url(repo_url),
        "branch": branch,
        "draft_branch": draft_branch,
        "vendor_dir": vendor_dir.as_posix(),
        "wiki_dir": wiki_dir.as_posix(),
        "target_wiki_path": decision.get("target_wiki_path"),
        "actual_write_path": "/" + actual_relative.strip("/"),
        "routing_decision": decision,
        "changed_files": changed_files,
        "commit": commit,
        "pushed": pushed,
        "existing_diff": existing_diff,
        "page_preview": page_preview,
        "warnings": warnings,
        "next_steps": _next_steps(status, draft_branch),
    }


def _write_reports(report: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    work_item = str(report.get("work_item") or "UNKNOWN")
    placement_path = out_dir / f"{work_item}.wiki-placement.md"
    md_path = out_dir / f"{work_item}.wiki-publication-report.md"
    json_path = out_dir / f"{work_item}.wiki-publication-report.json"
    report["report_paths"] = {
        "placement": placement_path.as_posix(),
        "publication": md_path.as_posix(),
        "json": json_path.as_posix(),
    }
    placement_path.write_text(_placement_markdown(report), encoding="utf-8")
    md_path.write_text(_report_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _placement_markdown(report: dict[str, Any]) -> str:
    decision = report.get("routing_decision") if isinstance(report.get("routing_decision"), dict) else {}
    if not decision:
        return "# Azure Wiki Placement Report\n\nNo placement decision was produced.\n"
    return "# Azure Wiki Placement Report\n\n" + explain_routing_decision(decision)


def _report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Azure Wiki Publication Report",
        "",
        "## Status",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Mode: `{report.get('mode')}`",
        f"- Generated at: `{report.get('generated_at')}`",
        "",
        "## Work Item",
        "",
        f"- Work Item: `{report.get('work_item')}`",
        f"- Title: `{report.get('title')}`",
        "",
        "## Source Artifacts",
        "",
    ]
    sources = report.get("source_artifacts") if isinstance(report.get("source_artifacts"), list) else []
    lines.extend(f"- `{source}`" for source in sources)
    if not sources:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Existing Wiki Sections Considered",
            "",
        ]
    )
    decision = report.get("routing_decision") if isinstance(report.get("routing_decision"), dict) else {}
    matched_pages = decision.get("matched_existing_pages") if isinstance(decision.get("matched_existing_pages"), list) else []
    if matched_pages:
        for match in matched_pages:
            page = match.get("page", {}) if isinstance(match, dict) else {}
            lines.append(f"- `{page.get('path')}`: {match.get('reason')} score={match.get('score')}")
    else:
        lines.append("- No existing page match was selected.")
    lines.extend(
        [
            "",
            "## Routing Decision",
            "",
            f"- Target path: `{report.get('target_wiki_path')}`",
            f"- Actual write path: `{report.get('actual_write_path')}`",
            f"- Confidence: `{decision.get('confidence', '')}`",
            "",
            "Reasoning:",
        ]
    )
    reasoning = decision.get("reasoning") if isinstance(decision.get("reasoning"), list) else []
    lines.extend(f"- {item}" for item in reasoning)
    lines.extend(["", "## Page Preview", "", "```markdown", str(report.get("page_preview") or ""), "```", ""])
    lines.extend(["## Files Changed", ""])
    changed = report.get("changed_files") if isinstance(report.get("changed_files"), list) else []
    lines.extend(f"- `{item}`" for item in changed)
    if not changed:
        lines.append("- None")
    lines.extend(["", "## Approval Status", ""])
    lines.append("- Human approval is required before publishing to the wiki default branch.")
    if report.get("status") == "BRANCH_PUSHED":
        lines.append("- Approved branch was pushed. Manual PR creation/review/merge is still required.")
    lines.extend(["", "## Push/PR Instructions", ""])
    lines.extend(f"- {item}" for item in _next_steps(str(report.get("status")), str(report.get("draft_branch") or "")))
    lines.extend(["", "## Warnings", ""])
    warnings = report.get("warnings") if isinstance(report.get("warnings"), list) else []
    lines.extend(f"- {warning}" for warning in warnings)
    if not warnings:
        lines.append("- None")
    if report.get("existing_diff"):
        lines.extend(["", "## Existing Page Diff", "", "```diff", str(report["existing_diff"])[:12000], "```"])
    return "\n".join(lines).rstrip() + "\n"


def _next_steps(status: str, draft_branch: str) -> list[str]:
    if status == "DRY_RUN":
        return [
            "Review the placement report and preview page.",
            "Run `make wiki-prepare-branch ...` only after placement is accepted.",
        ]
    if status == "BRANCH_PREPARED":
        return [
            f"Review local branch `{draft_branch}` in the cached wiki repository.",
            "Run `make wiki-push-approved ...` only after explicit human approval.",
        ]
    if status == "BRANCH_PUSHED":
        return [
            f"Open an Azure DevOps PR from branch `{draft_branch}` manually.",
            "Use normal human review and merge controls outside this tool.",
        ]
    return ["Resolve blockers and rerun the wiki dry run."]


def _write_preview(out_dir: Path, actual_relative: str, markdown: str) -> Path:
    preview = out_dir / "preview" / actual_relative.strip("/")
    preview.parent.mkdir(parents=True, exist_ok=True)
    preview.write_text(markdown, encoding="utf-8")
    return preview


def _update_order_file(actual_file: Path, wiki_dir: Path) -> None:
    relative = actual_file.relative_to(wiki_dir)
    order_file = actual_file.parent / ".order"
    entry = relative.stem
    entries: list[str] = []
    if order_file.exists():
        entries = [line.strip() for line in order_file.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
    if entry not in entries:
        entries.append(entry)
        order_file.write_text("\n".join(entries) + "\n", encoding="utf-8")


def _draft_branch_name(args: argparse.Namespace, config: dict[str, Any], title: str) -> str:
    if args.draft_branch.strip():
        return args.draft_branch.strip()
    prefix = str(config.get("default_draft_branch_prefix") or "docs/ai-wiki").strip("/")
    return f"{prefix}/{args.work_item}-{slugify_title(title)}"


def _parse_sources(values: list[str]) -> list[str]:
    sources: list[str] = []
    for value in values:
        for item in str(value).split(","):
            cleaned = item.strip()
            if cleaned:
                sources.append(cleaned)
    return sources


def _unified_diff(existing: str, proposed: str, path: str) -> str:
    return "".join(
        difflib.unified_diff(
            existing.splitlines(keepends=True),
            proposed.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )


def _resolve_inside_repo(path: Path, repo_root: Path) -> Path:
    resolved = path if path.is_absolute() else repo_root / path
    resolved = resolved.resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"Path must remain inside repository root: {path}") from exc
    return resolved


def _resolve_inside_wiki(path: Path, wiki_dir: Path) -> Path:
    if path.is_absolute():
        raise ValueError(f"Wiki path must be relative: {path}")
    resolved = (wiki_dir / path).resolve()
    try:
        resolved.relative_to(wiki_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"Wiki target path escapes wiki directory: {path}") from exc
    return resolved


def _mask_repo_url(repo_url: str) -> str:
    if "@" in repo_url and "://" in repo_url:
        prefix, rest = repo_url.split("://", 1)
        return prefix + "://[REDACTED]@" + rest.split("@", 1)[1]
    return repo_url


if __name__ == "__main__":
    raise SystemExit(main())
