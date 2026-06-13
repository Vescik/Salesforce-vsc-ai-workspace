"""Route generated documentation to an Azure DevOps Wiki page path."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

from ai_workspace.wiki.wiki_scanner import normalize_wiki_path, tokenize_text


def classify_document_topic(text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = metadata or {}
    tokens = tokenize_text(" ".join([text, str(metadata.get("title") or ""), str(metadata.get("work_item") or "")]))
    object_names = set(str(item) for item in metadata.get("object_names", []) if item)
    object_names.update(re.findall(r"\b[A-Za-z][A-Za-z0-9_]+__(?:c|mdt|x|b)\b", text))
    return {
        "keywords": sorted(tokens),
        "object_names": sorted(object_names),
        "title": str(metadata.get("title") or ""),
        "work_item": str(metadata.get("work_item") or ""),
    }


def find_existing_object_page(wiki_index: dict[str, Any], object_names: list[str]) -> list[dict[str, Any]]:
    if not object_names:
        return []
    wanted = {_normalize_token(name) for name in object_names}
    matches = []
    for page in wiki_index.get("pages", []):
        haystack = _page_haystack(page)
        score = sum(1 for name in wanted if name and name in haystack)
        if score:
            matches.append({"page": page, "score": score, "reason": "object_name_match"})
    return sorted(matches, key=lambda item: (-int(item["score"]), str(item["page"].get("path"))))


def find_existing_functionality_page(wiki_index: dict[str, Any], keywords: list[str]) -> list[dict[str, Any]]:
    wanted = {keyword.lower() for keyword in keywords if len(keyword) >= 4}
    matches = []
    for page in wiki_index.get("pages", []):
        page_keywords = set(str(item).lower() for item in page.get("keywords", []))
        overlap = wanted & page_keywords
        if len(overlap) >= 2:
            matches.append({"page": page, "score": len(overlap), "matched_keywords": sorted(overlap), "reason": "keyword_overlap"})
    return sorted(matches, key=lambda item: (-int(item["score"]), str(item["page"].get("path"))))


def find_best_module(wiki_index: dict[str, Any], module_map: dict[str, Any], keywords: list[str]) -> dict[str, Any]:
    modules = module_map.get("modules") if isinstance(module_map.get("modules"), dict) else {}
    wanted = {keyword.lower() for keyword in keywords}
    best: dict[str, Any] = {}
    for key, module in modules.items():
        if not isinstance(module, dict):
            continue
        module_keywords = {str(item).lower() for item in module.get("keywords", []) if item}
        related_objects = {str(item).lower() for item in module.get("related_objects", []) if item}
        overlap = wanted & (module_keywords | related_objects)
        score = len(overlap)
        if not score:
            continue
        existing_path = _first_existing_candidate_path(wiki_index, _string_list(module.get("candidate_paths")))
        candidate = {
            "module_key": str(key),
            "display_name": str(module.get("display_name") or key),
            "score": score,
            "matched_keywords": sorted(overlap),
            "existing_path": existing_path,
            "candidate_paths": _string_list(module.get("candidate_paths")),
        }
        if not best or score > int(best.get("score", 0)):
            best = candidate
    return best


def propose_target_path(
    wiki_index: dict[str, Any],
    module_map: dict[str, Any],
    source_text: str,
    work_item: str,
    title: str,
    explicit_module: str = "",
    explicit_target_path: str = "",
    object_names: list[str] | None = None,
    functionality_name: str = "",
) -> dict[str, Any]:
    """Return a routing decision with target wiki path and reasoning."""

    warnings: list[str] = []
    title = title.strip() or functionality_name.strip() or work_item
    slug = slugify_title(title)
    topic = classify_document_topic(
        source_text,
        {"title": title, "work_item": work_item, "object_names": object_names or []},
    )
    keywords = sorted(set(topic["keywords"]) | set(tokenize_text(functionality_name)))

    if explicit_target_path.strip():
        target_path = _normalize_target_file_path(explicit_target_path, slug)
        return _decision(
            target_path=target_path,
            confidence="high",
            reasoning=["Explicit target path was provided and validated."],
            matched_pages=[],
            matched_module={},
            warnings=warnings,
        )

    modules = module_map.get("modules") if isinstance(module_map.get("modules"), dict) else {}
    if explicit_module:
        module = modules.get(explicit_module)
        if isinstance(module, dict):
            existing = _first_existing_candidate_path(wiki_index, _string_list(module.get("candidate_paths")))
            if existing:
                target_path = f"{existing}/{slug}.md"
                return _decision(
                    target_path=target_path,
                    confidence="high",
                    reasoning=[f"Explicit module `{explicit_module}` maps to existing wiki section `{existing}`."],
                    matched_pages=[],
                    matched_module={"module_key": explicit_module, "display_name": str(module.get("display_name") or explicit_module), "existing_path": existing},
                    warnings=warnings,
                )
            proposed_root = _fallback_root(module_map, "proposed_root", "/_Proposed")
            module_slug = slugify_title(str(module.get("display_name") or explicit_module))
            target_path = f"{proposed_root}/{module_slug}/{slug}.md"
            warnings.append(f"Explicit module `{explicit_module}` was found in module map, but no existing wiki section matched its candidate paths.")
            return _decision(
                target_path=target_path,
                confidence="medium",
                reasoning=[f"Routed to proposed module area for `{explicit_module}`."],
                matched_pages=[],
                matched_module={"module_key": explicit_module, "display_name": str(module.get("display_name") or explicit_module), "existing_path": ""},
                warnings=warnings,
            )
        warnings.append(f"Explicit module `{explicit_module}` was not found in module map.")

    object_matches = find_existing_object_page(wiki_index, topic["object_names"])
    if object_matches:
        page = object_matches[0]["page"]
        parent = normalize_wiki_path(str(page.get("path") or ""))
        target_path = f"{parent}/{slug}.md"
        return _decision(
            target_path=target_path,
            confidence="high",
            reasoning=[f"Existing object-related page `{parent}` matched source object references."],
            matched_pages=[object_matches[0]],
            matched_module={},
            warnings=warnings,
        )

    functionality_matches = find_existing_functionality_page(wiki_index, keywords)
    if functionality_matches:
        page = functionality_matches[0]["page"]
        parent = normalize_wiki_path(str(page.get("path") or ""))
        target_path = f"{parent}/{slug}.md"
        return _decision(
            target_path=target_path,
            confidence="medium",
            reasoning=[f"Existing functionality page `{parent}` had keyword overlap with the source document."],
            matched_pages=[functionality_matches[0]],
            matched_module={},
            warnings=warnings,
        )

    best_module = find_best_module(wiki_index, module_map, keywords)
    if best_module:
        existing = str(best_module.get("existing_path") or "")
        if existing:
            target_path = f"{existing}/{slug}.md"
            return _decision(
                target_path=target_path,
                confidence="medium",
                reasoning=[f"Module `{best_module['display_name']}` matched keywords: {', '.join(best_module['matched_keywords'])}."],
                matched_pages=[],
                matched_module=best_module,
                warnings=warnings,
            )
        proposed_root = _fallback_root(module_map, "proposed_root", "/_Proposed")
        module_slug = slugify_title(str(best_module.get("display_name") or best_module.get("module_key") or "Module"))
        target_path = f"{proposed_root}/{module_slug}/{slug}.md"
        warnings.append("Matched module keywords, but no existing module section was found in the wiki.")
        return _decision(
            target_path=target_path,
            confidence="low",
            reasoning=[f"Proposed a new module area for `{best_module['display_name']}`."],
            matched_pages=[],
            matched_module=best_module,
            warnings=warnings,
        )

    unclassified_root = _fallback_root(module_map, "unclassified_root", "/_Unclassified")
    warnings.append("No existing object, functionality, or module section matched confidently.")
    return _decision(
        target_path=f"{unclassified_root}/{slug}.md",
        confidence="low",
        reasoning=["Routed to unclassified fallback for human placement review."],
        matched_pages=[],
        matched_module={},
        warnings=warnings,
    )


def slugify_title(title: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", title.strip()).strip("-")
    return slug or "Untitled"


def explain_routing_decision(decision: dict[str, Any]) -> str:
    lines = [
        f"Target path: `{decision.get('target_wiki_path')}`",
        f"Confidence: `{decision.get('confidence')}`",
        "",
        "Reasoning:",
    ]
    reasoning = decision.get("reasoning") if isinstance(decision.get("reasoning"), list) else []
    lines.extend(f"- {item}" for item in reasoning)
    warnings = decision.get("warnings") if isinstance(decision.get("warnings"), list) else []
    if warnings:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {item}" for item in warnings)
    return "\n".join(lines) + "\n"


def _decision(
    target_path: str,
    confidence: str,
    reasoning: list[str],
    matched_pages: list[dict[str, Any]],
    matched_module: dict[str, Any],
    warnings: list[str],
) -> dict[str, Any]:
    target_path = _normalize_target_file_path(target_path, "Untitled")
    target_file_path = target_path.lstrip("/")
    return {
        "target_wiki_path": target_path,
        "target_file_path": target_file_path,
        "confidence": confidence,
        "matched_existing_pages": matched_pages,
        "matched_module": matched_module,
        "reasoning": reasoning,
        "warnings": warnings,
        "requires_human_review": True,
    }


def _normalize_target_file_path(path: str, slug: str) -> str:
    text = normalize_wiki_path(path)
    if ".." in PurePosixPath(text).parts:
        raise ValueError(f"Unsafe wiki target path: {path}")
    if not text.lower().endswith(".md"):
        text = f"{text}/{slug}.md" if not text.split("/")[-1] == slug else f"{text}.md"
    return text


def _page_haystack(page: dict[str, Any]) -> str:
    values = [str(page.get("path") or ""), str(page.get("title") or ""), " ".join(str(item) for item in page.get("headings", []))]
    return _normalize_token(" ".join(values))


def _normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "", value.lower())


def _first_existing_candidate_path(wiki_index: dict[str, Any], candidate_paths: list[str]) -> str:
    folders = {normalize_wiki_path(str(folder.get("path") or "")) for folder in wiki_index.get("folders", [])}
    pages = {normalize_wiki_path(str(page.get("path") or "")) for page in wiki_index.get("pages", [])}
    for candidate in candidate_paths:
        normalized = normalize_wiki_path(candidate)
        if normalized in folders or normalized in pages or any(page.startswith(normalized + "/") for page in pages):
            return normalized
    return ""


def _fallback_root(module_map: dict[str, Any], key: str, default: str) -> str:
    fallback = module_map.get("fallback") if isinstance(module_map.get("fallback"), dict) else {}
    return normalize_wiki_path(str(fallback.get(key) or default))


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []
