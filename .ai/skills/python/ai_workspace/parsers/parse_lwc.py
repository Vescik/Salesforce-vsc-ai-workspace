"""Best-effort parser for Lightning Web Component folders."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ai_workspace.utils.io import empty_references, is_within, read_utf8, repo_relative_path, warn


APEX_IMPORT_RE = re.compile(
    r"@salesforce/apex/([A-Za-z_][A-Za-z0-9_]*)\.[A-Za-z_][A-Za-z0-9_]*"
)
SCHEMA_IMPORT_RE = re.compile(
    r"@salesforce/schema/([A-Za-z_][A-Za-z0-9_]*(?:__c|__mdt|__x)?|[A-Z][A-Za-z0-9_]*)"
    r"(?:\.([A-Za-z_][A-Za-z0-9_]*(?:__c|__r|__pc)|Id|Name|OwnerId|CreatedDate|"
    r"LastModifiedDate|RecordTypeId|Type|[A-Z][A-Za-z0-9_]*))?"
)


def parse_lwc_component(component_dir: Path, repo_root: Path) -> dict[str, Any]:
    """Parse an LWC component directory."""

    references = empty_references()
    risk_flags = {"lwc_component"}
    files: list[str] = []
    parse_status = "ok"

    for file_path in sorted(path for path in component_dir.rglob("*") if path.is_file()):
        if not is_within(file_path, repo_root):
            warn(f"Skipping LWC file outside repository root: {file_path}")
            parse_status = "partial"
            continue
        files.append(repo_relative_path(file_path, repo_root))
        if file_path.suffix.lower() not in {".js", ".html", ".xml", ".css"}:
            continue
        try:
            text, used_replacement = read_utf8(file_path)
        except OSError as exc:
            warn(f"Could not read LWC file {file_path}: {exc}")
            parse_status = "partial"
            continue
        if used_replacement:
            parse_status = "partial"
        references["apex_classes"].extend(APEX_IMPORT_RE.findall(text))
        for object_name, field_name in SCHEMA_IMPORT_RE.findall(text):
            if object_name:
                references["objects"].append(object_name)
                if object_name.endswith("__mdt"):
                    references["custom_metadata"].append(object_name)
            if object_name and field_name:
                references["fields"].append(f"{object_name}.{field_name}")

    references["lwc_components"].append(component_dir.name)
    references = {key: sorted(set(value)) for key, value in references.items()}

    summary_parts = [f"LWC component {component_dir.name}."]
    summary_parts.append(f"Contains {len(files)} file(s).")
    if references["apex_classes"]:
        summary_parts.append(f"Imports {len(references['apex_classes'])} Apex class candidate(s).")
    if references["fields"]:
        summary_parts.append(f"Imports {len(references['fields'])} schema field candidate(s).")

    return {
        "full_name": component_dir.name,
        "summary": " ".join(summary_parts),
        "references": references,
        "risk_flags": sorted(risk_flags),
        "parse_status": parse_status,
        "details": {"files": files},
    }
