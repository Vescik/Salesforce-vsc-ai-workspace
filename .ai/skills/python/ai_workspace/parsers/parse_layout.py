"""Best-effort parser for Salesforce Layout metadata."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from ai_workspace.utils.io import empty_references, read_utf8, warn


CUSTOM_OBJECT_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*(?:__c|__mdt|__x)\b")
FIELD_REF_RE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*(?:__c|__mdt|__x)?|[A-Z][A-Za-z0-9_]*)"
    r"\.([A-Za-z_][A-Za-z0-9_]*(?:__c|__r|__pc)|Id|Name|OwnerId|CreatedDate|"
    r"LastModifiedDate|RecordTypeId|Type|[A-Z][A-Za-z0-9_]*)\b"
)


def parse_layout_file(path: Path) -> dict[str, Any]:
    """Parse a Layout metadata XML file with best-effort extraction."""

    full_name = path.name.removesuffix(".layout-meta.xml")
    object_name = _object_from_layout_full_name(full_name)
    references = empty_references()
    risk_flags: set[str] = {"layout_metadata"}
    details: dict[str, Any] = {}
    if object_name:
        details["object"] = object_name
        references["objects"].append(object_name)

    try:
        text, used_replacement = read_utf8(path)
    except OSError as exc:
        warn(f"Could not read Layout file {path}: {exc}")
        return _failed(full_name, references, str(exc))

    parse_status = "partial" if used_replacement else "ok"

    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        warn(f"Could not parse Layout XML {path}: {exc}")
        _extract_text_patterns(text, references)
        return {
            "full_name": full_name,
            "summary": "Layout XML parse failed; references are regex-only.",
            "references": _dedupe_references(references),
            "risk_flags": sorted(risk_flags | {"parse_failed"}),
            "parse_status": "failed",
            "details": {"error": str(exc), **details},
        }

    layout_sections = _extract_sections(root)
    if layout_sections:
        details["sections"] = layout_sections

    fields = _extract_fields(root)
    for field_name in fields:
        _append_field_reference(references, field_name, object_name)
    if fields:
        details["field_candidates"] = sorted(fields)

    custom_buttons = _texts_for(root, "customButtons")
    excluded_buttons = _texts_for(root, "excludeButtons")
    quick_actions = _extract_quick_actions(root)
    platform_actions = _extract_platform_actions(root)
    related_lists = _extract_related_lists(root)

    if custom_buttons:
        details["custom_buttons"] = sorted(custom_buttons)
        risk_flags.add("custom_button_candidate")
    if excluded_buttons:
        details["excluded_buttons"] = sorted(excluded_buttons)
    if quick_actions:
        details["quick_actions"] = sorted(quick_actions)
        risk_flags.add("quick_action_candidate")
    if platform_actions:
        details["platform_actions"] = sorted(platform_actions)
        risk_flags.add("page_action_candidate")
    if related_lists:
        details["related_lists"] = related_lists
        risk_flags.add("related_list_candidate")

    _extract_text_patterns("\n".join(root.itertext()), references)
    references = _dedupe_references(references)

    summary_parts = [f"Layout metadata {full_name}."]
    if object_name:
        summary_parts.append(f"Object: {object_name}.")
    if fields:
        summary_parts.append(f"Contains {len(fields)} field candidate(s).")
    if custom_buttons or quick_actions or platform_actions:
        summary_parts.append("Contains action/button candidate(s).")
    if related_lists:
        summary_parts.append(f"Contains {len(related_lists)} related list candidate(s).")

    return {
        "full_name": full_name,
        "summary": " ".join(summary_parts),
        "references": references,
        "risk_flags": sorted(risk_flags),
        "parse_status": parse_status,
        "details": details,
    }


def _failed(full_name: str, references: dict[str, list[str]], error: str) -> dict[str, Any]:
    return {
        "full_name": full_name,
        "summary": "Layout metadata could not be read.",
        "references": references,
        "risk_flags": ["layout_metadata", "parse_failed"],
        "parse_status": "failed",
        "details": {"error": error},
    }


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _child_text(element: ET.Element, tag_name: str) -> str | None:
    for child in list(element):
        if _local_name(child.tag) == tag_name and child.text:
            value = child.text.strip()
            if value:
                return value
    return None


def _iter_named(root: ET.Element, tag_name: str) -> list[ET.Element]:
    return [element for element in root.iter() if _local_name(element.tag) == tag_name]


def _texts_for(root: ET.Element, tag_name: str) -> set[str]:
    return {
        element.text.strip()
        for element in _iter_named(root, tag_name)
        if element.text and element.text.strip()
    }


def _extract_sections(root: ET.Element) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for section in _iter_named(root, "layoutSections"):
        item: dict[str, Any] = {}
        for tag_name in {"label", "style", "detailHeading", "editHeading"}:
            value = _child_text(section, tag_name)
            if value:
                item[_snake(tag_name)] = value
        section_fields = sorted(
            {
                field.text.strip()
                for field in _iter_named(section, "field")
                if field.text and field.text.strip()
            }
        )
        if section_fields:
            item["fields"] = section_fields
        if item:
            sections.append(item)
    return sorted(sections, key=lambda value: str(value.get("label") or ""))


def _extract_fields(root: ET.Element) -> set[str]:
    return _texts_for(root, "field")


def _extract_quick_actions(root: ET.Element) -> set[str]:
    actions = _texts_for(root, "quickActionName")
    actions.update(_texts_for(root, "quickActionListItems"))
    return {action for action in actions if action}


def _extract_platform_actions(root: ET.Element) -> set[str]:
    actions: set[str] = set()
    for item in _iter_named(root, "platformActionListItems"):
        action_name = _child_text(item, "actionName")
        if action_name:
            actions.add(action_name)
    return actions


def _extract_related_lists(root: ET.Element) -> list[dict[str, Any]]:
    related_lists: list[dict[str, Any]] = []
    for related_list in _iter_named(root, "relatedLists"):
        item: dict[str, Any] = {}
        for tag_name in {"relatedList", "fields", "customButtons", "sortField"}:
            values = _texts_for(related_list, tag_name)
            if values:
                item[_snake(tag_name)] = sorted(values)
        if item:
            related_lists.append(item)
    return sorted(related_lists, key=lambda value: str(value.get("related_list") or ""))


def _object_from_layout_full_name(full_name: str) -> str:
    if "-" not in full_name:
        return ""
    return full_name.split("-", 1)[0]


def _append_field_reference(
    references: dict[str, list[str]],
    field_name: str,
    object_name: str,
) -> None:
    if "." in field_name:
        object_part, field_part = field_name.split(".", 1)
        references["objects"].append(object_part)
        references["fields"].append(f"{object_part}.{field_part}")
    elif object_name:
        references["fields"].append(f"{object_name}.{field_name}")


def _extract_text_patterns(text: str, references: dict[str, list[str]]) -> None:
    references["objects"].extend(CUSTOM_OBJECT_RE.findall(text))
    for match in FIELD_REF_RE.finditer(text):
        object_name, field_name = match.groups()
        references["objects"].append(object_name)
        references["fields"].append(f"{object_name}.{field_name}")


def _snake(value: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r"_\1", value).lower()


def _dedupe_references(references: dict[str, list[str]]) -> dict[str, list[str]]:
    return {key: sorted(set(value)) for key, value in references.items()}
