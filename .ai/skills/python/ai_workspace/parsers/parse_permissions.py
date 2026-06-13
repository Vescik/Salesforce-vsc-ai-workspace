"""Best-effort parsers for Permission Set and Profile metadata."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from ai_workspace.utils.io import empty_references, read_utf8, warn


FIELD_REF_RE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*(?:__c|__mdt|__x)?|[A-Z][A-Za-z0-9_]*)"
    r"\.([A-Za-z_][A-Za-z0-9_]*(?:__c|__r|__pc)|Id|Name|OwnerId|CreatedDate|"
    r"LastModifiedDate|RecordTypeId|Type|[A-Z][A-Za-z0-9_]*)\b"
)
ELEVATED_SYSTEM_PERMISSIONS = {
    "AuthorApex",
    "CustomizeApplication",
    "ManageDataIntegrations",
    "ModifyAllData",
    "ViewAllData",
}


def parse_permission_set_file(path: Path) -> dict[str, Any]:
    """Parse a Permission Set metadata XML file."""

    return _parse_access_metadata(
        path=path,
        suffix=".permissionset-meta.xml",
        metadata_label="Permission Set",
        risk_flag="permissionset_metadata",
    )


def parse_profile_file(path: Path) -> dict[str, Any]:
    """Parse a Profile metadata XML file."""

    return _parse_access_metadata(
        path=path,
        suffix=".profile-meta.xml",
        metadata_label="Profile",
        risk_flag="profile_metadata",
    )


def _parse_access_metadata(
    path: Path,
    suffix: str,
    metadata_label: str,
    risk_flag: str,
) -> dict[str, Any]:
    full_name = path.name.removesuffix(suffix)
    references = empty_references()
    risk_flags: set[str] = {risk_flag}
    details: dict[str, Any] = {}

    try:
        text, used_replacement = read_utf8(path)
    except OSError as exc:
        warn(f"Could not read {metadata_label} file {path}: {exc}")
        return _failed(full_name, metadata_label, references, risk_flag, str(exc))

    parse_status = "partial" if used_replacement else "ok"

    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        warn(f"Could not parse {metadata_label} XML {path}: {exc}")
        return {
            "full_name": full_name,
            "summary": f"{metadata_label} XML parse failed.",
            "references": references,
            "risk_flags": sorted(risk_flags | {"parse_failed"}),
            "parse_status": "failed",
            "details": {"error": str(exc)},
        }

    label = _first_text(root, "label")
    if label:
        details["label"] = label

    object_permissions = _extract_object_permissions(root)
    if object_permissions:
        details["object_permissions"] = object_permissions
        references["objects"].extend(str(item["object"]) for item in object_permissions if item.get("object"))
        risk_flags.add("object_crud_permissions")
        if any(item.get("view_all_records") or item.get("modify_all_records") for item in object_permissions):
            risk_flags.add("elevated_object_permission_candidate")

    field_permissions = _extract_field_permissions(root)
    if field_permissions:
        details["field_permissions"] = field_permissions
        for item in field_permissions:
            field_name = str(item.get("field") or "")
            if not field_name:
                continue
            references["fields"].append(field_name)
            if "." in field_name:
                references["objects"].append(field_name.split(".", 1)[0])
        risk_flags.add("field_level_security_permissions")

    apex_class_accesses = _extract_named_accesses(root, "classAccesses", "apexClass")
    if apex_class_accesses:
        details["apex_class_accesses"] = apex_class_accesses
        references["apex_classes"].extend(
            str(item["apex_class"])
            for item in apex_class_accesses
            if item.get("apex_class") and item.get("enabled") is not False
        )
        risk_flags.add("apex_class_access_candidate")

    flow_accesses = _extract_named_accesses(root, "flowAccesses", "flow")
    if flow_accesses:
        details["flow_accesses"] = flow_accesses
        references["flows"].extend(
            str(item["flow"])
            for item in flow_accesses
            if item.get("flow") and item.get("enabled") is not False
        )
        risk_flags.add("flow_access_candidate")

    tab_settings = _extract_tab_settings(root)
    if tab_settings:
        details["tab_settings"] = tab_settings
        references["objects"].extend(str(item["tab"]) for item in tab_settings if _looks_like_object(str(item.get("tab") or "")))

    application_visibilities = _extract_application_visibilities(root)
    if application_visibilities:
        details["application_visibilities"] = application_visibilities

    custom_metadata_accesses = _extract_custom_metadata_accesses(root)
    if custom_metadata_accesses:
        details["custom_metadata_type_accesses"] = custom_metadata_accesses
        references["custom_metadata"].extend(
            str(item["name"])
            for item in custom_metadata_accesses
            if item.get("name") and item.get("enabled") is not False
        )

    user_permissions = _extract_user_permissions(root)
    if user_permissions:
        details["user_permissions"] = user_permissions
        if any(item.get("name") in ELEVATED_SYSTEM_PERMISSIONS and item.get("enabled") for item in user_permissions):
            risk_flags.add("elevated_system_permission_candidate")

    references = _dedupe_references(references)

    summary_parts = [f"{metadata_label} metadata {full_name}."]
    if object_permissions:
        summary_parts.append(f"Includes {len(object_permissions)} object permission candidate(s).")
    if field_permissions:
        summary_parts.append(f"Includes {len(field_permissions)} field permission candidate(s).")
    if apex_class_accesses:
        summary_parts.append(f"Includes {len(apex_class_accesses)} Apex class access candidate(s).")
    if flow_accesses:
        summary_parts.append(f"Includes {len(flow_accesses)} Flow access candidate(s).")

    return {
        "full_name": full_name,
        "summary": " ".join(summary_parts),
        "references": references,
        "risk_flags": sorted(risk_flags),
        "parse_status": parse_status,
        "details": details,
    }


def _failed(
    full_name: str,
    metadata_label: str,
    references: dict[str, list[str]],
    risk_flag: str,
    error: str,
) -> dict[str, Any]:
    return {
        "full_name": full_name,
        "summary": f"{metadata_label} metadata could not be read.",
        "references": references,
        "risk_flags": [risk_flag, "parse_failed"],
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


def _extract_object_permissions(root: ET.Element) -> list[dict[str, Any]]:
    permissions: list[dict[str, Any]] = []
    for element in _iter_named(root, "objectPermissions"):
        object_name = _child_text(element, "object")
        if not object_name:
            continue
        item: dict[str, Any] = {"object": object_name}
        for tag_name in {
            "allowCreate",
            "allowDelete",
            "allowEdit",
            "allowRead",
            "modifyAllRecords",
            "viewAllRecords",
        }:
            value = _child_text(element, tag_name)
            if value is not None:
                item[_snake(tag_name)] = _as_bool(value)
        permissions.append(item)
    return sorted(permissions, key=lambda value: str(value.get("object") or ""))


def _extract_field_permissions(root: ET.Element) -> list[dict[str, Any]]:
    permissions: list[dict[str, Any]] = []
    for element in _iter_named(root, "fieldPermissions"):
        field_name = _child_text(element, "field")
        if not field_name:
            continue
        item: dict[str, Any] = {"field": field_name}
        for tag_name in {"editable", "readable"}:
            value = _child_text(element, tag_name)
            if value is not None:
                item[tag_name] = _as_bool(value)
        permissions.append(item)
    return sorted(permissions, key=lambda value: str(value.get("field") or ""))


def _extract_named_accesses(root: ET.Element, parent_tag: str, name_tag: str) -> list[dict[str, Any]]:
    accesses: list[dict[str, Any]] = []
    for element in _iter_named(root, parent_tag):
        value = _child_text(element, name_tag)
        if not value:
            continue
        item: dict[str, Any] = {_snake(name_tag): value}
        enabled = _child_text(element, "enabled")
        if enabled is not None:
            item["enabled"] = _as_bool(enabled)
        accesses.append(item)
    return sorted(accesses, key=lambda item: str(next(iter(item.values()))))


def _extract_tab_settings(root: ET.Element) -> list[dict[str, Any]]:
    settings: list[dict[str, Any]] = []
    for element in _iter_named(root, "tabSettings"):
        tab = _child_text(element, "tab")
        if not tab:
            continue
        item: dict[str, Any] = {"tab": tab}
        visibility = _child_text(element, "visibility")
        if visibility:
            item["visibility"] = visibility
        settings.append(item)
    return sorted(settings, key=lambda value: str(value.get("tab") or ""))


def _extract_application_visibilities(root: ET.Element) -> list[dict[str, Any]]:
    visibilities: list[dict[str, Any]] = []
    for element in _iter_named(root, "applicationVisibilities"):
        application = _child_text(element, "application")
        if not application:
            continue
        item: dict[str, Any] = {"application": application}
        visible = _child_text(element, "visible")
        if visible is not None:
            item["visible"] = _as_bool(visible)
        default = _child_text(element, "default")
        if default is not None:
            item["default"] = _as_bool(default)
        visibilities.append(item)
    return sorted(visibilities, key=lambda value: str(value.get("application") or ""))


def _extract_custom_metadata_accesses(root: ET.Element) -> list[dict[str, Any]]:
    accesses: list[dict[str, Any]] = []
    for element in _iter_named(root, "customMetadataTypeAccesses"):
        name = _child_text(element, "name")
        if not name:
            continue
        item: dict[str, Any] = {"name": name}
        enabled = _child_text(element, "enabled")
        if enabled is not None:
            item["enabled"] = _as_bool(enabled)
        accesses.append(item)
    return sorted(accesses, key=lambda value: str(value.get("name") or ""))


def _extract_user_permissions(root: ET.Element) -> list[dict[str, Any]]:
    permissions: list[dict[str, Any]] = []
    for element in _iter_named(root, "userPermissions"):
        name = _child_text(element, "name")
        if not name:
            continue
        item: dict[str, Any] = {"name": name}
        enabled = _child_text(element, "enabled")
        if enabled is not None:
            item["enabled"] = _as_bool(enabled)
        permissions.append(item)
    return sorted(permissions, key=lambda value: str(value.get("name") or ""))


def _as_bool(value: str) -> bool | str:
    lowered = value.strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return value


def _looks_like_object(value: str) -> bool:
    return bool(value and (value.endswith("__c") or value.endswith("__mdt") or value[:1].isupper()))


def _snake(value: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r"_\1", value).lower()


def _dedupe_references(references: dict[str, list[str]]) -> dict[str, list[str]]:
    for field_name in list(references.get("fields", [])):
        match = FIELD_REF_RE.search(field_name)
        if match:
            references["objects"].append(match.group(1))
    return {key: sorted(set(value)) for key, value in references.items()}
