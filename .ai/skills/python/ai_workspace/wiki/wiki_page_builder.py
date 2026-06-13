"""Build Azure DevOps Wiki markdown pages from local workspace artifacts."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_workspace.wiki.wiki_config import policy_bool, policy_list


SECRET_PATTERNS = [
    re.compile(r"(?i)\bpassword\s*[:=]"),
    re.compile(r"(?i)\bclient_secret\b"),
    re.compile(r"(?i)\baccess_token\b"),
    re.compile(r"(?i)\brefresh_token\b"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\bxoxb-[A-Za-z0-9-]{12,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
MAX_SOURCE_CHARS = 6000
MAX_EXCERPT_CHARS = 1800


def build_wiki_page(
    source_paths: list[str | Path],
    repo_root: str | Path,
    policy: dict[str, Any],
    work_item: str,
    title: str,
    routing_decision: dict[str, Any],
    approved: bool = False,
    approval_note: str = "",
) -> dict[str, Any]:
    """Build a wiki page and return markdown, metadata, and warnings."""

    root = Path(repo_root).resolve()
    warnings: list[str] = []
    source_docs = _load_source_docs(source_paths, root, policy, warnings)
    if policy_bool(policy, True, "safety", "require_source_artifact_references") and not source_docs:
        warnings.append("No readable source artifacts were provided.")

    secret_hits = []
    if policy_bool(policy, True, "safety", "scan_for_secrets"):
        for source in source_docs:
            if _contains_secret_like_value(source["text"]):
                secret_hits.append(source["path"])
        if secret_hits:
            warnings.extend(f"Secret-like value detected in `{path}`." for path in secret_hits)

    review_required = policy_bool(policy, True, "approval", "require_human_approval") and not approved
    source_artifact_lines = "\n".join(f"  - \"{doc['path']}\"" for doc in source_docs) or "  - \"[missing]\""
    source_artifact_list = "\n".join(f"- `{doc['path']}`" for doc in source_docs) or "- Missing source artifact references."
    topic_excerpt = _combined_excerpt(source_docs)
    headings = _collect_headings(source_docs)
    related_objects = _extract_salesforce_object_candidates(topic_excerpt)
    config_records = _extract_config_candidates(topic_excerpt)

    front_matter = [
        "---",
        f'title: "{_escape_yaml_string(title)}"',
        f'work_item: "{_escape_yaml_string(work_item)}"',
        f'status: "{"approved-draft" if approved else "draft"}"',
        "source_artifacts:",
        source_artifact_lines,
        'generated_by: "Salesforce AI Workspace"',
        f"requires_human_review: {'true' if review_required else 'false'}",
        f'generated_at: "{datetime.now(timezone.utc).isoformat()}"',
        "---",
        "",
    ]

    marker = (
        "AI-assisted draft prepared for Azure DevOps Wiki. Requires human review before publication."
        if review_required
        else "Human-approved draft prepared for Azure DevOps Wiki branch publication."
    )
    lines = [
        *front_matter,
        f"# {title}",
        "",
        marker,
        "",
        "## Purpose",
        "",
        _purpose_text(title, work_item, source_docs),
        "",
        "## Scope",
        "",
        "- This page summarizes local workspace artifacts for review in Azure DevOps Wiki.",
        "- It is not deployment evidence and does not replace DevOps Center.",
        "- KimbleOne/Kantata package internals are not assumed.",
        "",
        "## Related Work Item",
        "",
        f"- `{work_item}`",
        "",
        "## Related Salesforce Objects",
        "",
        _bullet_list(related_objects, "No Salesforce object references were identified in the selected source artifacts."),
        "",
        "## Related Configuration Records",
        "",
        _bullet_list(config_records, "No configuration record references were identified in the selected source artifacts."),
        "",
        "## Functional Behavior",
        "",
        _section_from_sources(source_docs, ["functional", "behavior", "business", "acceptance"]),
        "",
        "## Technical Notes",
        "",
        _section_from_sources(source_docs, ["technical", "implementation", "metadata", "flow", "apex", "lwc"]),
        "",
        "## QA / Validation Notes",
        "",
        _section_from_sources(source_docs, ["qa", "test", "validation", "precheck"]),
        "",
        "## Release / Deployment Notes",
        "",
        "- Salesforce metadata promotion remains through DevOps Center.",
        "- This draft does not deploy metadata, apply configuration records, or write Salesforce data.",
        "",
        "## Open Questions",
        "",
        _section_from_sources(source_docs, ["open question", "assumption", "risk", "unknown"]),
        "",
        "## Source Artifacts",
        "",
        source_artifact_list,
        "",
        "## Existing Source Headings Considered",
        "",
        _bullet_list(headings, "No headings were extracted from the selected source artifacts."),
        "",
        "## Wiki Placement",
        "",
        f"- Target path: `{routing_decision.get('target_wiki_path')}`",
        f"- Confidence: `{routing_decision.get('confidence')}`",
        "- Human review required before publication.",
        "",
        "## Review Checklist",
        "",
        "- [ ] Placement matches existing wiki structure.",
        "- [ ] Content is accurate and sourced.",
        "- [ ] No secrets, credentials, raw data dumps, or unsupported package claims are included.",
        "- [ ] QA and release notes are appropriate for the target audience.",
        "- [ ] PR/manual merge is performed by a human reviewer outside this tool.",
        "",
        "## Review History",
        "",
        f"- Draft prepared by Salesforce AI Workspace for `{work_item}`.",
    ]
    if approval_note:
        lines.append(f"- Approval note: {approval_note}")

    return {
        "markdown": "\n".join(lines).rstrip() + "\n",
        "metadata": {
            "work_item": work_item,
            "title": title,
            "source_artifacts": [doc["path"] for doc in source_docs],
            "secret_hits": secret_hits,
            "requires_human_review": review_required,
        },
        "warnings": warnings,
        "blocked": bool(secret_hits and policy_bool(policy, True, "safety", "fail_on_secret_like_values")),
    }


def read_source_text(
    source_paths: list[str | Path],
    repo_root: str | Path,
    policy: dict[str, Any],
) -> tuple[str, list[str]]:
    warnings: list[str] = []
    docs = _load_source_docs(source_paths, Path(repo_root).resolve(), policy, warnings)
    return "\n\n".join(doc["text"] for doc in docs), warnings


def _load_source_docs(source_paths: list[str | Path], repo_root: Path, policy: dict[str, Any], warnings: list[str]) -> list[dict[str, str]]:
    allowed_roots = policy_list(policy, "source_documents", "allowed_roots") or [
        "docs/architecture",
        "docs/qa-how-to-test",
        "specs/approved",
        "specs/proposed",
        ".ai/outputs/pre-promote",
        ".ai/context/work-items",
    ]
    blocked_roots = policy_list(policy, "source_documents", "blocked_roots")
    docs: list[dict[str, str]] = []
    for raw_path in source_paths:
        if not str(raw_path).strip():
            continue
        path = Path(raw_path)
        absolute = path if path.is_absolute() else repo_root / path
        try:
            resolved = absolute.resolve()
            relative = resolved.relative_to(repo_root).as_posix()
        except ValueError:
            warnings.append(f"Source path is outside repository root and was skipped: {raw_path}")
            continue
        if _is_under_any(relative, blocked_roots):
            warnings.append(f"Source path is under a blocked root and was skipped: {relative}")
            continue
        if not _is_under_any(relative, allowed_roots):
            warnings.append(f"Source path is not under an allowed documentation root and was skipped: {relative}")
            continue
        if not resolved.exists() or not resolved.is_file():
            warnings.append(f"Source artifact was not found: {relative}")
            continue
        if resolved.stat().st_size > 1024 * 1024:
            warnings.append(f"Source artifact is too large and was skipped: {relative}")
            continue
        text = resolved.read_text(encoding="utf-8", errors="replace")[:MAX_SOURCE_CHARS]
        docs.append({"path": relative, "text": text})
    return docs


def _is_under_any(relative_path: str, roots: list[str]) -> bool:
    normalized = relative_path.strip("/")
    for root in roots:
        clean_root = root.strip("/")
        if normalized == clean_root or normalized.startswith(clean_root + "/"):
            return True
    return False


def _contains_secret_like_value(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def _combined_excerpt(source_docs: list[dict[str, str]]) -> str:
    return "\n\n".join(doc["text"][:MAX_EXCERPT_CHARS] for doc in source_docs)


def _collect_headings(source_docs: list[dict[str, str]]) -> list[str]:
    headings: list[str] = []
    for doc in source_docs:
        for line in doc["text"].splitlines():
            match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
            if match:
                headings.append(f"{match.group(1).strip()} ({doc['path']})")
    return headings[:30]


def _extract_salesforce_object_candidates(text: str) -> list[str]:
    custom = set(re.findall(r"\b[A-Za-z][A-Za-z0-9_]+__(?:c|mdt|x|b)\b", text))
    standard = set(re.findall(r"\b(Account|Contact|Opportunity|Case|User|Task|Event|Product2|Pricebook2)\b", text))
    return sorted(custom | standard)


def _extract_config_candidates(text: str) -> list[str]:
    candidates = set(re.findall(r"\b[A-Za-z][A-Za-z0-9_]+__(?:mdt|c)\b", text))
    return sorted(item for item in candidates if "Setting" in item or item.endswith("__mdt"))


def _section_from_sources(source_docs: list[dict[str, str]], keywords: list[str]) -> str:
    selected: list[str] = []
    lowered_keywords = [keyword.lower() for keyword in keywords]
    for doc in source_docs:
        paragraphs = re.split(r"\n\s*\n", doc["text"])
        for paragraph in paragraphs:
            cleaned = " ".join(line.strip() for line in paragraph.splitlines()).strip()
            if not cleaned or len(cleaned) < 20:
                continue
            lowered = cleaned.lower()
            if any(keyword in lowered for keyword in lowered_keywords):
                selected.append(f"- {cleaned[:500]} (`{doc['path']}`)")
            if len(selected) >= 5:
                return "\n".join(selected)
    if source_docs:
        return "- Review the source artifacts listed below for the detailed content to include in this section."
    return "- No source artifact content was available for this section."


def _purpose_text(title: str, work_item: str, source_docs: list[dict[str, str]]) -> str:
    if source_docs:
        return f"This page documents `{title}` for Work Item `{work_item}` based on the source artifacts listed below."
    return f"This page is a placeholder draft for `{title}` and Work Item `{work_item}`. Source artifacts must be added before publication."


def _bullet_list(values: list[str], empty_text: str) -> str:
    if not values:
        return f"- {empty_text}"
    return "\n".join(f"- `{value}`" for value in values)


def _escape_yaml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
