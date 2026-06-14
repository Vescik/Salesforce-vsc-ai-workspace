"""Salesforce XML/metadata converter for Knowledge Base Creator 2.0."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from ai_workspace.knowledge.converters import make_doc
from ai_workspace.knowledge.parse_documents import normalize_whitespace


def convert(path: Path | str) -> dict[str, Any]:
    source = Path(path)
    warnings: list[str] = []
    try:
        raw = source.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw = source.read_text(encoding="utf-8", errors="replace")
        warnings.append("UTF-8 decode failed; replacement characters were used.")
    except OSError as exc:
        return make_doc("xml", source, warnings=[f"Could not read XML: {exc}"], parse_status="failed")

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        warnings.append(f"XML parse failed; falling back to stripped text: {exc}")
        body = normalize_whitespace(_strip_tags(raw))
        return make_doc(
            "xml",
            source,
            sections=[{"heading": source.stem, "level": 1, "body": body, "anchors": ["xml-raw"]}],
            metadata={"raw_xml": raw[:200_000], "component_type": "unknown"},
            warnings=warnings,
            parse_status="partial",
            degraded=True,
        )

    component_type = _local_name(root.tag)
    component_name = _child_text(root, "fullName") or source.stem
    sections = [
        {
            "heading": f"{component_type}: {component_name}",
            "level": 1,
            "body": _summary_lines(root),
            "anchors": ["xml-component"],
        }
    ]
    sections.extend(_metadata_sections(root))
    return make_doc(
        "xml",
        source,
        sections=sections,
        metadata={
            "raw_xml": raw[:200_000],
            "component_type": component_type,
            "component_name": component_name,
            "root_tag": component_type,
        },
        warnings=warnings,
        parse_status="partial" if warnings else "ok",
        degraded=False,
    )


def _metadata_sections(root: ET.Element) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    counters: dict[str, int] = {}
    for element in root.iter():
        tag = _local_name(element.tag)
        if tag not in {
            "fields",
            "validationRules",
            "recordTypes",
            "businessProcesses",
            "listViews",
            "decisions",
            "assignments",
            "screens",
            "actionCalls",
            "subflows",
            "recordLookups",
            "recordUpdates",
        }:
            continue
        name = _child_text(element, "fullName") or _child_text(element, "name") or tag
        counters[tag] = counters.get(tag, 0) + 1
        lines = []
        for child in list(element):
            child_name = _local_name(child.tag)
            text = normalize_whitespace(child.text or "")
            if text:
                lines.append(f"{child_name}: {text}")
        sections.append(
            {
                "heading": f"{tag}: {name}",
                "level": 2,
                "body": "\n".join(lines),
                "anchors": [f"xml-{tag}-{counters[tag]}"],
            }
        )
    return sections


def _summary_lines(root: ET.Element) -> str:
    lines: list[str] = []
    for key in ("fullName", "label", "processType", "status", "object", "description"):
        value = _child_text(root, key)
        if value:
            lines.append(f"{key}: {value}")
    if not lines:
        for element in list(root)[:20]:
            value = normalize_whitespace(element.text or "")
            if value:
                lines.append(f"{_local_name(element.tag)}: {value}")
    return "\n".join(lines)


def _child_text(element: ET.Element, local_name: str) -> str:
    for child in list(element):
        if _local_name(child.tag) == local_name:
            return normalize_whitespace(child.text or "")
    return ""


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _strip_tags(raw: str) -> str:
    import re

    return re.sub(r"<[^>]+>", " ", raw)
