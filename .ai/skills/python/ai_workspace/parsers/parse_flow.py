"""Best-effort Salesforce Flow XML parser."""

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
FLOW_ELEMENT_TAGS = {
    "actionCalls",
    "assignments",
    "decisions",
    "recordCreates",
    "recordDeletes",
    "recordLookups",
    "recordUpdates",
    "subflows",
}
RECORD_OPERATION_TAGS = {
    "recordCreates",
    "recordDeletes",
    "recordLookups",
    "recordUpdates",
}


def parse_flow_file(path: Path) -> dict[str, Any]:
    """Parse a Flow metadata XML file with resilient best-effort extraction."""

    full_name = path.name.removesuffix(".flow-meta.xml")
    references = empty_references()
    risk_flags: set[str] = {"flow_metadata"}
    details: dict[str, Any] = {}

    try:
        text, used_replacement = read_utf8(path)
    except OSError as exc:
        warn(f"Could not read Flow file {path}: {exc}")
        return {
            "full_name": full_name,
            "summary": "Flow metadata could not be read.",
            "references": references,
            "risk_flags": ["flow_metadata", "parse_failed"],
            "parse_status": "failed",
            "details": {"error": str(exc)},
        }

    parse_status = "partial" if used_replacement else "ok"

    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        warn(f"Could not parse Flow XML {path}: {exc}")
        _extract_text_patterns(text, references)
        return {
            "full_name": full_name,
            "summary": "Flow metadata XML parse failed; references are regex-only.",
            "references": _dedupe_references(references),
            "risk_flags": sorted(risk_flags | {"parse_failed"}),
            "parse_status": "failed",
            "details": {"error": str(exc)},
        }

    process_type = _first_text(root, "processType")
    if process_type:
        details["process_type"] = process_type

    start = _first_child(root, "start")
    start_details = _extract_start_details(start) if start is not None else {}
    if start_details:
        details["start"] = start_details
    start_object = str(start_details.get("object") or "")
    if start_object:
        details["start_object"] = start_object
        references["objects"].append(start_object)

    if process_type and "record" in process_type.lower():
        risk_flags.add("record_triggered_flow_candidate")
    elif start_object:
        risk_flags.add("record_triggered_flow_candidate")

    if start_details.get("trigger_type"):
        risk_flags.add("record_triggered_flow_candidate")

    elements = _extract_flow_elements(root)
    for key, value in elements.items():
        if value:
            details[key] = value

    record_operations = details.get("record_operations") or []
    if record_operations:
        for operation in record_operations:
            object_name = operation.get("object")
            if object_name:
                references["objects"].append(str(object_name))
            for field_name in operation.get("fields", []):
                _append_field_reference(references, str(field_name), str(object_name or ""))
        risk_flags.add("record_operation_candidate")

    for field_name in start_details.get("fields", []):
        _append_field_reference(references, str(field_name), start_object)

    apex_actions = _extract_apex_actions(root)
    if apex_actions:
        references["apex_classes"].extend(apex_actions)
        risk_flags.add("apex_action_candidate")
        details["apex_action_candidates"] = sorted(set(apex_actions))

    subflows = _extract_subflows(root)
    if subflows:
        references["flows"].extend(subflows)
        details["subflow_candidates"] = sorted(set(subflows))

    _extract_text_patterns("\n".join(root.itertext()), references)

    references = _dedupe_references(references)
    summary_parts = [f"Flow metadata {full_name}."]
    if process_type:
        summary_parts.append(f"Process type: {process_type}.")
    if start_object:
        summary_parts.append(f"Start object: {start_object}.")
    if references["objects"]:
        summary_parts.append(f"References {len(references['objects'])} object candidate(s).")
    if references["apex_classes"]:
        summary_parts.append("Contains Apex action candidate(s).")
    if record_operations:
        summary_parts.append(f"Contains {len(record_operations)} record operation candidate(s).")

    return {
        "full_name": full_name,
        "summary": " ".join(summary_parts),
        "references": references,
        "risk_flags": sorted(risk_flags),
        "parse_status": parse_status,
        "details": details,
    }


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _first_text(root: ET.Element, tag_name: str) -> str | None:
    for element in root.iter():
        if _local_name(element.tag) == tag_name and element.text:
            return element.text.strip()
    return None


def _first_child(root: ET.Element, tag_name: str) -> ET.Element | None:
    for element in list(root):
        if _local_name(element.tag) == tag_name:
            return element
    return None


def _child_text(element: ET.Element, tag_name: str) -> str | None:
    for child in list(element):
        if _local_name(child.tag) == tag_name and child.text:
            value = child.text.strip()
            if value:
                return value
    return None


def _child_texts(element: ET.Element, tag_name: str) -> list[str]:
    values: list[str] = []
    for child in list(element):
        if _local_name(child.tag) == tag_name and child.text:
            value = child.text.strip()
            if value:
                values.append(value)
    return values


def _extract_text_patterns(text: str, references: dict[str, list[str]]) -> None:
    objects = set(CUSTOM_OBJECT_RE.findall(text))
    fields = set()
    for match in FIELD_REF_RE.finditer(text):
        object_name, field_name = match.groups()
        fields.add(f"{object_name}.{field_name}")
        objects.add(object_name)
    references["objects"].extend(sorted(objects))
    references["fields"].extend(sorted(fields))


def _extract_start_details(start: ET.Element) -> dict[str, Any]:
    details: dict[str, Any] = {}
    for tag_name in {
        "object",
        "recordTriggerType",
        "triggerType",
        "filterLogic",
        "schedule",
    }:
        value = _child_text(start, tag_name)
        if value:
            details[_snake(tag_name)] = value

    filter_fields = [
        field
        for filters in _children(start, "filters")
        for field in _child_texts(filters, "field")
    ]
    if filter_fields:
        details["fields"] = sorted(set(filter_fields))

    scheduled_paths = []
    for scheduled_path in _children(start, "scheduledPaths"):
        item = _named_element_details(scheduled_path)
        for tag_name in {"offsetNumber", "offsetUnit", "timeSource", "connector"}:
            value = _child_text(scheduled_path, tag_name)
            if value:
                item[_snake(tag_name)] = value
        if item:
            scheduled_paths.append(item)
    if scheduled_paths:
        details["scheduled_paths"] = scheduled_paths

    return details


def _extract_flow_elements(root: ET.Element) -> dict[str, Any]:
    decisions: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    subflows: list[dict[str, Any]] = []
    record_operations: list[dict[str, Any]] = []
    fault_paths: list[dict[str, str]] = []

    for element in root.iter():
        tag = _local_name(element.tag)
        if tag not in FLOW_ELEMENT_TAGS:
            continue

        item = _named_element_details(element)
        fault_target = _connector_target(element, "faultConnector")
        if fault_target:
            name = str(item.get("name") or "")
            fault_paths.append({"element_type": tag, "name": name, "target": fault_target})

        if tag == "decisions":
            rule_names = [
                name
                for rule in _children(element, "rules")
                for name in _child_texts(rule, "name")
            ]
            condition_fields = [
                field
                for rule in _children(element, "rules")
                for condition in _children(rule, "conditions")
                for field in _child_texts(condition, "leftValueReference")
            ]
            if rule_names:
                item["rules"] = sorted(set(rule_names))
            if condition_fields:
                item["condition_references"] = sorted(set(condition_fields))
            decisions.append(item)
        elif tag == "assignments":
            assignment_refs = [
                ref
                for assignment_item in _children(element, "assignmentItems")
                for ref in _child_texts(assignment_item, "assignToReference")
            ]
            if assignment_refs:
                item["assignment_references"] = sorted(set(assignment_refs))
            assignments.append(item)
        elif tag == "actionCalls":
            for tag_name in {"actionName", "actionType", "flowTransactionModel"}:
                value = _child_text(element, tag_name)
                if value:
                    item[_snake(tag_name)] = value
            actions.append(item)
        elif tag == "subflows":
            flow_name = _child_text(element, "flowName")
            if flow_name:
                item["flow_name"] = flow_name
            subflows.append(item)
        elif tag in RECORD_OPERATION_TAGS:
            object_name = _child_text(element, "object") or _child_text(element, "sObjectType")
            if object_name:
                item["object"] = object_name
            fields = [
                field
                for input_assignment in _children(element, "inputAssignments")
                for field in _child_texts(input_assignment, "field")
            ]
            fields.extend(_child_texts(element, "queriedFields"))
            if fields:
                item["fields"] = sorted(set(fields))
            item["operation_type"] = tag
            record_operations.append(item)

    return {
        "decisions": _drop_empty_named_items(decisions),
        "assignments": _drop_empty_named_items(assignments),
        "action_calls": _drop_empty_named_items(actions),
        "subflows": _drop_empty_named_items(subflows),
        "record_operations": _drop_empty_named_items(record_operations),
        "fault_paths": sorted(fault_paths, key=lambda item: (item["element_type"], item["name"], item["target"])),
    }


def _extract_apex_actions(root: ET.Element) -> list[str]:
    actions: list[str] = []
    for action_call in root.iter():
        if _local_name(action_call.tag) != "actionCalls":
            continue
        child_values = {
            _local_name(child.tag): (child.text or "").strip()
            for child in list(action_call)
        }
        action_type = child_values.get("actionType", "").lower()
        action_name = child_values.get("actionName") or child_values.get("name")
        if action_type == "apex" and action_name:
            actions.append(_apex_class_from_action(action_name))

    for element in root.iter():
        tag = _local_name(element.tag)
        value = (element.text or "").strip()
        if tag in {"apexClass", "className"} and value:
            actions.append(_apex_class_from_action(value))
    return sorted(set(action for action in actions if action))


def _extract_subflows(root: ET.Element) -> list[str]:
    flows: list[str] = []
    for subflow in root.iter():
        if _local_name(subflow.tag) != "subflows":
            continue
        for child in list(subflow):
            if _local_name(child.tag) == "flowName" and child.text:
                flows.append(child.text.strip())
    return sorted(set(flows))


def _children(element: ET.Element, tag_name: str) -> list[ET.Element]:
    return [child for child in list(element) if _local_name(child.tag) == tag_name]


def _named_element_details(element: ET.Element) -> dict[str, str]:
    details: dict[str, str] = {}
    for tag_name in {"name", "label", "description"}:
        value = _child_text(element, tag_name)
        if value:
            details[tag_name] = value
    return details


def _connector_target(element: ET.Element, connector_tag: str) -> str | None:
    for connector in _children(element, connector_tag):
        value = _child_text(connector, "targetReference")
        if value:
            return value
    return None


def _drop_empty_named_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item
        for item in sorted(items, key=lambda value: str(value.get("name") or value.get("flow_name") or ""))
        if item
    ]


def _append_field_reference(
    references: dict[str, list[str]],
    field_name: str,
    object_name: str,
) -> None:
    if "." in field_name:
        references["fields"].append(field_name)
        references["objects"].append(field_name.split(".", 1)[0])
    elif object_name:
        references["fields"].append(f"{object_name}.{field_name}")


def _apex_class_from_action(value: str) -> str:
    parts = [part for part in value.split(".") if part]
    if not parts:
        return value
    if len(parts) == 1:
        return parts[0]
    if len(parts) >= 3:
        return parts[-2]
    return parts[0]


def _snake(value: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r"_\1", value).lower()


def _dedupe_references(references: dict[str, list[str]]) -> dict[str, list[str]]:
    return {key: sorted(set(value)) for key, value in references.items()}
