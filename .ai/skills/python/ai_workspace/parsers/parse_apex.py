"""Best-effort Apex parser for local repository metadata indexing."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ai_workspace.utils.io import empty_references, read_utf8, warn


CLASS_RE = re.compile(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\b", re.IGNORECASE)
TRIGGER_RE = re.compile(
    r"\btrigger\s+([A-Za-z_][A-Za-z0-9_]*)\s+on\s+([A-Za-z_][A-Za-z0-9_]*)\b",
    re.IGNORECASE,
)
SOQL_FROM_RE = re.compile(
    r"\bFROM\s+([A-Za-z_][A-Za-z0-9_]*(?:__c|__mdt|__x)?)\b",
    re.IGNORECASE,
)
CUSTOM_OBJECT_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*(?:__c|__mdt|__x)\b")
FIELD_REF_RE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*(?:__c|__mdt|__x)?|[A-Z][A-Za-z0-9_]*)"
    r"\.([A-Za-z_][A-Za-z0-9_]*(?:__c|__r|__pc)|Id|Name|OwnerId|CreatedDate|"
    r"LastModifiedDate|RecordTypeId|Type|[A-Z][A-Za-z0-9_]*)\b"
)
DML_RE = re.compile(r"\b(insert|update|upsert|delete|undelete)\b", re.IGNORECASE)
CALLOUT_RE = re.compile(
    r"(HttpRequest|\bHttp\s*\(|\bHttp\s+[A-Za-z_][A-Za-z0-9_]*|"
    r"\bwebservice\b|@future\s*\(\s*callout\s*=\s*true\s*\)|"
    r"\bQueueable\b|\bContinuation\b)",
    re.IGNORECASE,
)
SALESFORCE_ID_LITERAL_RE = re.compile(
    r"['\"]([A-Za-z0-9]{15}(?:[A-Za-z0-9]{3})?)['\"]"
)


def parse_apex_file(path: Path) -> dict[str, Any]:
    """Parse an Apex class or trigger with best-effort regexes."""

    references = empty_references()
    risk_flags: set[str] = set()
    details: dict[str, Any] = {}

    try:
        text, used_replacement = read_utf8(path)
    except OSError as exc:
        warn(f"Could not read Apex file {path}: {exc}")
        return {
            "full_name": path.stem,
            "summary": "Apex metadata could not be read.",
            "references": references,
            "risk_flags": ["parse_failed"],
            "parse_status": "failed",
            "details": {"error": str(exc)},
        }

    parse_status = "partial" if used_replacement else "ok"
    class_match = CLASS_RE.search(text)
    trigger_match = TRIGGER_RE.search(text)

    if trigger_match:
        full_name = trigger_match.group(1)
        trigger_object = trigger_match.group(2)
        details["kind"] = "trigger"
        details["trigger_object"] = trigger_object
        references["objects"].append(trigger_object)
    elif class_match:
        full_name = class_match.group(1)
        details["kind"] = "class"
    else:
        full_name = path.stem
        details["kind"] = "apex"
        parse_status = "partial"

    sharing = _detect_sharing(text)
    details["sharing"] = sharing
    if details["kind"] == "class" and sharing is None:
        risk_flags.add("sharing_not_declared")

    objects = set(CUSTOM_OBJECT_RE.findall(text))
    objects.update(match.group(1) for match in SOQL_FROM_RE.finditer(text))
    references["objects"].extend(sorted(objects))

    fields = set()
    for match in FIELD_REF_RE.finditer(text):
        object_name, field_name = match.groups()
        fields.add(f"{object_name}.{field_name}")
        if object_name and object_name[0].isupper():
            references["objects"].append(object_name)
    references["fields"].extend(sorted(fields))

    if DML_RE.search(text):
        risk_flags.add("dml_detected")

    if CALLOUT_RE.search(text):
        risk_flags.add("callout_detected")

    id_candidates = [
        value
        for value in SALESFORCE_ID_LITERAL_RE.findall(text)
        if any(char.isdigit() for char in value)
    ]
    if id_candidates:
        risk_flags.add("hardcoded_salesforce_id_candidate")
        details["salesforce_id_candidate_count"] = len(id_candidates)

    references = {
        key: sorted(set(value))
        for key, value in references.items()
    }

    summary_parts = [f"Apex {details['kind']} {full_name}."]
    if sharing:
        summary_parts.append(f"Sharing: {sharing}.")
    if references["objects"]:
        summary_parts.append(f"References {len(references['objects'])} object candidate(s).")
    if risk_flags:
        summary_parts.append(f"Risk flags: {', '.join(sorted(risk_flags))}.")

    return {
        "full_name": full_name,
        "summary": " ".join(summary_parts),
        "references": references,
        "risk_flags": sorted(risk_flags),
        "parse_status": parse_status,
        "details": details,
    }


def _detect_sharing(text: str) -> str | None:
    lowered = re.sub(r"\s+", " ", text.lower())
    if "inherited sharing" in lowered:
        return "inherited sharing"
    if "without sharing" in lowered:
        return "without sharing"
    if "with sharing" in lowered:
        return "with sharing"
    return None
