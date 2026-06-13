"""Best-effort parser for Salesforce FlexiPage metadata."""

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


def parse_flexipage_file(path: Path) -> dict[str, Any]:
    """Parse a FlexiPage metadata XML file with best-effort extraction."""

    full_name = path.name.removesuffix(".flexipage-meta.xml")
    references = empty_references()
    risk_flags: set[str] = {"flexipage_metadata"}
    details: dict[str, Any] = {}

    try:
        text, used_replacement = read_utf8(path)
    except OSError as exc:
        warn(f"Could not read FlexiPage file {path}: {exc}")
        return _failed(full_name, references, str(exc))

    parse_status = "partial" if used_replacement else "ok"

    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        warn(f"Could not parse FlexiPage XML {path}: {exc}")
        _extract_text_patterns(text, references)
        return {
            "full_name": full_name,
            "summary": "FlexiPage XML parse failed; references are regex-only.",
            "references": _dedupe_references(references),
            "risk_flags": sorted(risk_flags | {"parse_failed"}),
            "parse_status": "failed",
            "details": {"error": str(exc)},
        }

    for tag_name, detail_key in {
        "fullName": "xml_full_name",
        "masterLabel": "master_label",
        "type": "page_type",
        "sobjectType": "sobject_type",
        "template": "template",
    }.items():
        value = _first_text(root, tag_name)
        if value:
            details[detail_key] = value

    object_name = details.get("sobject_type")
    if object_name:
        references["objects"].append(str(object_name))

    regions, component_names, property_values = _extract_regions(root)
    if regions:
        details["regions"] = regions
    if component_names:
        details["component_names"] = sorted(component_names)
    if property_values:
        details["component_property_values"] = sorted(property_values)

    custom_components = _custom_component_names(component_names)
    if custom_components:
        references["lwc_components"].extend(custom_components)
        risk_flags.add("custom_ui_component_candidate")

    field_values = _field_like_property_values(root)
    for field_value in field_values:
        _append_field_reference(references, field_value, str(object_name or ""))
    if field_values:
        details["field_candidates"] = sorted(set(field_values))

    action_values = _action_like_property_values(root)
    if action_values:
        details["action_candidates"] = sorted(set(action_values))
        risk_flags.add("page_action_candidate")

    visibility_rules = _extract_visibility_rules(root)
    if visibility_rules:
        details["visibility_rules"] = visibility_rules
        for rule in visibility_rules:
            references["fields"].extend(rule.get("field_references", []))
            references["objects"].extend(
                field_ref.split(".", 1)[0]
                for field_ref in rule.get("field_references", [])
                if "." in field_ref
            )
        risk_flags.add("dynamic_visibility_candidate")

    _extract_text_patterns("\n".join(root.itertext()), references)
    references = _dedupe_references(references)

    summary_parts = [f"FlexiPage metadata {full_name}."]
    if object_name:
        summary_parts.append(f"Object: {object_name}.")
    if details.get("page_type"):
        summary_parts.append(f"Type: {details['page_type']}.")
    if component_names:
        summary_parts.append(f"Contains {len(component_names)} component candidate(s).")
    if visibility_rules:
        summary_parts.append("Contains dynamic visibility candidate(s).")

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
        "summary": "FlexiPage metadata could not be read.",
        "references": references,
        "risk_flags": ["flexipage_metadata", "parse_failed"],
        "parse_status": "failed",
        "details": {"error": error},
    }


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _first_text(root: ET.Element, tag_name: str) -> str | None:
    for element in root.iter():
        if _local_name(element.tag) == tag_name and element.text:
            value = element.text.strip()
            if value:
                return value
    return None


def _child_text(element: ET.Element, tag_name: str) -> str | None:
    for child in list(element):
        if _local_name(child.tag) == tag_name and child.text:
            value = child.text.strip()
            if value:
                return value
    return None


def _iter_named(root: ET.Element, tag_name: str) -> list[ET.Element]:
    return [element for element in root.iter() if _local_name(element.tag) == tag_name]


def _extract_regions(root: ET.Element) -> tuple[list[dict[str, Any]], set[str], set[str]]:
    regions: list[dict[str, Any]] = []
    component_names: set[str] = set()
    property_values: set[str] = set()

    for region in _iter_named(root, "flexiPageRegions"):
        item: dict[str, Any] = {}
        for tag_name in {"name", "type", "appendable", "mode"}:
            value = _child_text(region, tag_name)
            if value:
                item[tag_name] = value

        region_components: set[str] = set()
        for component_instance in _iter_named(region, "componentInstance"):
            component_name = _child_text(component_instance, "componentName")
            if component_name:
                component_names.add(component_name)
                region_components.add(component_name)
            for prop in _iter_named(component_instance, "componentInstanceProperties"):
                prop_value = _child_text(prop, "value")
                if prop_value:
                    property_values.add(prop_value)

        if region_components:
            item["components"] = sorted(region_components)
        if item:
            regions.append(item)

    return sorted(regions, key=lambda value: str(value.get("name") or "")), component_names, property_values


def _field_like_property_values(root: ET.Element) -> set[str]:
    values: set[str] = set()
    for prop in _iter_named(root, "componentInstanceProperties"):
        name = (_child_text(prop, "name") or "").lower()
        value = _child_text(prop, "value")
        if value and ("field" in name or FIELD_REF_RE.search(value)):
            values.add(value)
    for tag_name in {"field", "fieldName", "recordFieldName"}:
        for element in _iter_named(root, tag_name):
            if element.text and element.text.strip():
                values.add(element.text.strip())
    return values


def _action_like_property_values(root: ET.Element) -> set[str]:
    values: set[str] = set()
    for prop in _iter_named(root, "componentInstanceProperties"):
        name = (_child_text(prop, "name") or "").lower()
        value = _child_text(prop, "value")
        if value and "action" in name:
            values.add(value)
    return values


def _extract_visibility_rules(root: ET.Element) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for rule in _iter_named(root, "visibilityRule"):
        text_values = sorted(set(value.strip() for value in rule.itertext() if value.strip()))
        field_refs = sorted(
            set(
                f"{match.group(1)}.{match.group(2)}"
                for value in text_values
                for match in FIELD_REF_RE.finditer(value)
            )
        )
        item: dict[str, Any] = {}
        if text_values:
            item["values"] = text_values[:20]
        if field_refs:
            item["field_references"] = field_refs
        if item:
            rules.append(item)
    return rules


def _custom_component_names(component_names: set[str]) -> list[str]:
    custom_components: set[str] = set()
    for component_name in component_names:
        if component_name.startswith("c:"):
            custom_components.add(component_name.split(":", 1)[1])
        elif component_name.startswith("c__"):
            custom_components.add(component_name.removeprefix("c__"))
    return sorted(custom_components)


def _append_field_reference(
    references: dict[str, list[str]],
    field_name: str,
    object_name: str,
) -> None:
    for match in FIELD_REF_RE.finditer(field_name):
        references["objects"].append(match.group(1))
        references["fields"].append(f"{match.group(1)}.{match.group(2)}")
    if "." not in field_name and object_name:
        references["fields"].append(f"{object_name}.{field_name}")


def _extract_text_patterns(text: str, references: dict[str, list[str]]) -> None:
    references["objects"].extend(CUSTOM_OBJECT_RE.findall(text))
    for match in FIELD_REF_RE.finditer(text):
        object_name, field_name = match.groups()
        references["objects"].append(object_name)
        references["fields"].append(f"{object_name}.{field_name}")


def _dedupe_references(references: dict[str, list[str]]) -> dict[str, list[str]]:
    return {key: sorted(set(value)) for key, value in references.items()}
