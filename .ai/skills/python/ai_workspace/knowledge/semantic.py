"""Deterministic semantic enrichment for Knowledge Base Creator 2.0.

This module deliberately avoids model calls. It extracts high-signal Salesforce
and business references from source text using conservative parsers and regexes.
Generated facts are marked as detected or inferred in the note body/report so
humans can review them before promoting a knowledge note beyond draft/low.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from ai_workspace.knowledge.parse_documents import normalize_whitespace


STANDARD_OBJECTS = {
    "Account",
    "Asset",
    "Campaign",
    "Case",
    "Contact",
    "Contract",
    "Event",
    "Lead",
    "Opportunity",
    "Order",
    "Pricebook2",
    "PricebookEntry",
    "Product2",
    "Quote",
    "Task",
    "User",
}

USAGE_CONTEXTS = [
    "Solution Design",
    "Development",
    "Code Review",
    "Testing",
    "Deployment",
    "Troubleshooting",
    "Documentation",
]

STOPWORDS = {
    "about",
    "after",
    "also",
    "and",
    "any",
    "are",
    "before",
    "between",
    "but",
    "can",
    "cannot",
    "for",
    "from",
    "has",
    "have",
    "into",
    "its",
    "may",
    "must",
    "not",
    "only",
    "or",
    "our",
    "per",
    "should",
    "than",
    "that",
    "the",
    "then",
    "this",
    "through",
    "when",
    "where",
    "with",
    "without",
}

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")
CUSTOM_NAME_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_]*(?:__c|__mdt|__e|__x|__b)\b")
OBJECT_FIELD_RE = re.compile(
    r"\b([A-Za-z][A-Za-z0-9_]*(?:__c|__mdt|__e|__x|__b)|Account|Asset|Campaign|Case|Contact|"
    r"Contract|Event|Lead|Opportunity|Order|Pricebook2|PricebookEntry|Product2|Quote|Task|User)"
    r"\.([A-Za-z][A-Za-z0-9_]*(?:__c|__r|__pc|__pr)?|[A-Za-z][A-Za-z0-9_]*)\b"
)
APEX_CLASS_RE = re.compile(r"\b(?:class|interface|enum)\s+([A-Z][A-Za-z0-9_]+)\b")
APEX_METHOD_RE = re.compile(
    r"\b(?:public|private|protected|global|static|virtual|override|testMethod|void|Boolean|String|Integer|Decimal|"
    r"Date|Datetime|Id|List<[^>]+>|Map<[^>]+>|Set<[^>]+>)\s+([a-zA-Z][A-Za-z0-9_]*)\s*\("
)
APEX_TRIGGER_RE = re.compile(r"\btrigger\s+([A-Z][A-Za-z0-9_]+)\s+on\s+([A-Za-z][A-Za-z0-9_]*(?:__c|__mdt|__e|__x|__b)?|[A-Z][A-Za-z0-9_]*)", re.IGNORECASE)
SERVICE_RE = re.compile(r"\b([A-Z][A-Za-z0-9_]*(?:Service|Manager|Selector|Handler|Controller|TriggerHandler))\b")
FLOW_REF_RE = re.compile(r"\b(?:Flow|flow)\s*[:=]\s*([A-Za-z][A-Za-z0-9_ -]{2,})")
VALIDATION_RULE_RE = re.compile(r"\b(?:validation rule|ValidationRule)\s*[:=]?\s*([A-Za-z][A-Za-z0-9_ -]{2,})?", re.IGNORECASE)
INTEGRATION_RE = re.compile(
    r"\b(NamedCredential|ExternalCredential|REST|SOAP|HTTP Callout|callout|webhook|Platform Event|"
    r"Change Data Capture|CDC|API|OAuth|SAML|SSO|MuleSoft|middleware|endpoint|integration)\b",
    re.IGNORECASE,
)
DEPENDENCY_RE = re.compile(r"\b(depends on|requires|calls|invokes|uses|subflow|lookup|depends upon)\s+([A-Za-z][A-Za-z0-9_.:/ -]{2,})", re.IGNORECASE)
RULE_SENTENCE_RE = re.compile(r"(?im)^\s*(?:[-*]\s*)?(?:Given|When|Then|And|Must|Should|Cannot|Validate|Ensure|Acceptance Criteria|AC\d*[:.]?)\b(.+)$")


def enrich_document(
    text: str,
    parse_result: dict[str, Any],
    *,
    title: str,
    domain: str,
    source_path: str,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return v2 semantic fields and review evidence for a source/chunk."""

    manifest = manifest or {}
    normalized = normalize_whitespace(text)
    xml_facts = _extract_xml_facts(parse_result)
    objects = _merge(
        manifest.get("related_objects"),
        xml_facts.get("objects"),
        _extract_objects(normalized),
    )
    related_fields = _merge(
        manifest.get("related_fields"),
        xml_facts.get("fields"),
        _extract_fields(normalized, objects),
    )
    apex_classes = _merge(xml_facts.get("apex_classes"), APEX_CLASS_RE.findall(normalized), SERVICE_RE.findall(normalized))
    apex_methods = _merge(xml_facts.get("apex_methods"), _method_names(normalized))
    apex_triggers = _merge(xml_facts.get("apex_triggers"), [match.group(1) for match in APEX_TRIGGER_RE.finditer(normalized)])
    flow_names = _merge(xml_facts.get("flow_names"), FLOW_REF_RE.findall(normalized))
    flow_steps = _merge(xml_facts.get("flow_steps"), _extract_flow_steps(parse_result), _find_named_lines(normalized, ("decision", "assignment", "screen", "action", "subflow")))
    validation_rules = _merge(xml_facts.get("validation_rules"), _extract_validation_rules(normalized))
    integration_points = _merge(manifest.get("integration_points"), xml_facts.get("integration_points"), _extract_integrations(normalized))
    dependencies = _merge(manifest.get("dependencies"), xml_facts.get("dependencies"), _extract_dependencies(normalized))
    business_rules = _merge(manifest.get("business_rules"), _extract_business_rules(normalized))
    related_metadata = _merge(
        manifest.get("related_metadata"),
        xml_facts.get("metadata"),
        apex_classes,
        apex_triggers,
        flow_names,
        validation_rules,
    )
    related_processes = _merge(manifest.get("related_processes"), _extract_process_terms(title, normalized))
    key_concepts = _merge(
        manifest.get("key_concepts"),
        related_processes,
        _noun_terms(normalized, limit=12),
        objects[:6],
        flow_names[:4],
    )
    usage_context = _merge(manifest.get("usage_context"), _infer_usage_context(normalized, parse_result))
    aliases = _merge(manifest.get("aliases"), _aliases(objects, related_fields, related_metadata, key_concepts))
    keywords = _merge(
        manifest.get("tags"),
        manifest.get("keywords"),
        [domain, "managed-package", "knowledge-base"],
        objects,
        related_fields,
        related_metadata,
        related_processes,
        key_concepts,
        aliases,
        integration_points,
        _keyword_terms(normalized, limit=20),
    )
    summary = _extractive_summary(normalized, title)
    purpose = _purpose(title, source_path, usage_context, key_concepts, objects)
    facts = _fact_rows(
        objects=objects,
        fields=related_fields,
        apex_classes=apex_classes,
        apex_methods=apex_methods,
        apex_triggers=apex_triggers,
        flow_names=flow_names,
        flow_steps=flow_steps,
        validation_rules=validation_rules,
        integration_points=integration_points,
        dependencies=dependencies,
        business_rules=business_rules,
    )
    return {
        "purpose": purpose,
        "summary": summary,
        "key_concepts": key_concepts,
        "keywords": keywords,
        "tags": _merge(manifest.get("tags"), domain, "knowledge-base"),
        "aliases": aliases,
        "usage_context": usage_context,
        "related_objects": objects,
        "related_fields": related_fields,
        "related_metadata": related_metadata,
        "related_processes": related_processes,
        "integration_points": integration_points,
        "dependencies": dependencies,
        "business_rules": business_rules,
        "apex_classes": apex_classes,
        "apex_methods": apex_methods,
        "apex_triggers": apex_triggers,
        "flow_names": flow_names,
        "flow_steps": flow_steps,
        "validation_rules": validation_rules,
        "facts": facts,
        "quality_warnings": _quality_warnings(normalized, keywords, summary, source_path),
    }


def source_checksum(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def low_value_text(text: str) -> bool:
    normalized = normalize_whitespace(text)
    if not normalized:
        return True
    terms = TOKEN_RE.findall(normalized)
    return len(normalized) < 80 and len(set(term.lower() for term in terms)) < 8


def normalized_checksum(text: str) -> str:
    import hashlib

    normalized = normalize_whitespace(text).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _extract_xml_facts(parse_result: dict[str, Any]) -> dict[str, list[str]]:
    raw = str((parse_result.get("metadata") or {}).get("raw_xml") or "")
    if not raw:
        return {}
    facts: dict[str, list[str]] = {}
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return facts

    def add(key: str, value: str | None) -> None:
        value = (value or "").strip()
        if value:
            facts.setdefault(key, []).append(value)

    root_name = _local_name(root.tag)
    add("metadata", root_name)
    root_object = _child_text(root, "fullName") if root_name == "CustomObject" else ""
    if root_object:
        add("objects", root_object)
    current_parent = ""
    for element in root.iter():
        tag = _local_name(element.tag)
        text = (element.text or "").strip()
        parent_key = current_parent
        if tag in {"fields", "validationRules", "recordTypes", "businessProcesses", "listViews"}:
            parent_key = tag
        if tag == "fullName":
            if parent_key == "fields":
                add("fields", f"{root_object}.{text}" if root_object else text)
            elif parent_key == "validationRules":
                add("validation_rules", text)
            else:
                add("metadata", text)
        elif tag == "label":
            add("key_concepts", text)
        elif tag in {"object", "objectName", "sobjectType"}:
            add("objects", text)
        elif tag in {"name", "interviewLabel"}:
            add("flow_steps", text)
        elif tag in {"actionName", "flowName", "processMetadataValues"}:
            add("metadata", text)
        elif tag in {"processType"} and text:
            add("metadata", f"Flow:{text}")
        elif tag in {"endpoint", "calloutName"}:
            add("integration_points", text)
        if tag in {"decisions", "assignments", "screens", "actionCalls", "subflows", "recordLookups", "recordUpdates"}:
            name = _child_text(element, "name")
            if name:
                add("flow_steps", f"{tag}:{name}")
            if tag in {"actionCalls", "subflows"}:
                add("dependencies", name)
        if tag == "validationRules":
            add("validation_rules", _child_text(element, "fullName"))
        current_parent = parent_key
    return {key: _merge(value) for key, value in facts.items()}


def _child_text(element: ET.Element, local_name: str) -> str:
    for child in list(element):
        if _local_name(child.tag) == local_name:
            return (child.text or "").strip()
    return ""


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _extract_objects(text: str) -> list[str]:
    found = set(CUSTOM_NAME_RE.findall(text))
    for standard in STANDARD_OBJECTS:
        if re.search(rf"\b{re.escape(standard)}\b", text):
            found.add(standard)
    for match in APEX_TRIGGER_RE.finditer(text):
        if match.group(2):
            found.add(match.group(2))
    return sorted(found)


def _extract_fields(text: str, objects: list[str]) -> list[str]:
    fields = {f"{match.group(1)}.{match.group(2)}" for match in OBJECT_FIELD_RE.finditer(text)}
    object_set = set(objects)
    for name in CUSTOM_NAME_RE.findall(text):
        if name not in object_set and re.search(rf"\b(field|fields|column|columns|formula|lookup)\b[^\n]{{0,80}}\b{re.escape(name)}\b", text, re.IGNORECASE):
            fields.add(name)
    return sorted(fields)


def _method_names(text: str) -> list[str]:
    names = []
    for name in APEX_METHOD_RE.findall(text):
        if name in {"if", "for", "while", "switch", "catch", "return", "new"}:
            continue
        names.append(name)
    return sorted(set(names))


def _extract_flow_steps(parse_result: dict[str, Any]) -> list[str]:
    steps: list[str] = []
    for section in parse_result.get("sections") or []:
        heading = str(section.get("heading") or "")
        body = str(section.get("body") or "")
        if heading.lower().startswith("flow "):
            steps.append(heading)
        steps.extend(_find_named_lines(body, ("decision", "assignment", "screen", "action", "subflow", "lookup", "update")))
    return _merge(steps)


def _find_named_lines(text: str, labels: Iterable[str]) -> list[str]:
    out: list[str] = []
    for label in labels:
        pattern = re.compile(rf"\b{re.escape(label)}s?\b\s*[:=-]?\s*([A-Za-z][A-Za-z0-9_ -]{{2,80}})", re.IGNORECASE)
        for match in pattern.finditer(text):
            out.append(f"{label}:{match.group(1).strip()}")
    return out


def _extract_validation_rules(text: str) -> list[str]:
    out: list[str] = []
    for match in VALIDATION_RULE_RE.finditer(text):
        name = (match.group(1) or "").strip(" .:-")
        out.append(name or "Validation rule")
    return _merge(out)


def _extract_integrations(text: str) -> list[str]:
    return _merge(match.group(1).strip() for match in INTEGRATION_RE.finditer(text))


def _extract_dependencies(text: str) -> list[str]:
    out = []
    for match in DEPENDENCY_RE.finditer(text):
        target = match.group(2).strip(" .,:;")
        if target:
            out.append(target[:120])
    return _merge(out)


def _extract_business_rules(text: str) -> list[str]:
    rules: list[str] = []
    for match in RULE_SENTENCE_RE.finditer(text):
        candidate = normalize_whitespace(match.group(0)).strip("-* ")
        if 12 <= len(candidate) <= 240:
            rules.append(candidate)
    for sentence in _sentences(text):
        if re.search(r"\b(must|should|cannot|required|validate|approval|eligible|criteria)\b", sentence, re.IGNORECASE):
            if 20 <= len(sentence) <= 220:
                rules.append(sentence)
    return _merge(rules)[:12]


def _extract_process_terms(title: str, text: str) -> list[str]:
    candidates = []
    for value in (title,):
        if re.search(r"\b(process|flow|journey|approval|onboarding|billing|invoice|timesheet)\b", value, re.IGNORECASE):
            candidates.append(value)
    for match in re.finditer(r"\b([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,4}\s+(?:Process|Flow|Journey|Approval|Review))\b", text):
        candidates.append(match.group(1))
    return _merge(candidates)[:10]


def _infer_usage_context(text: str, parse_result: dict[str, Any]) -> list[str]:
    contexts: set[str] = {"Documentation"}
    lowered = text.lower()
    fmt = str(parse_result.get("format") or parse_result.get("source_format") or "").lower()
    if any(term in lowered for term in ("acceptance criteria", "business rule", "solution design", "requirement")):
        contexts.add("Solution Design")
    if any(term in lowered for term in ("apex", "class", "trigger", "flow", "metadata", "field", "__c")) or fmt == "xml":
        contexts.add("Development")
        contexts.add("Code Review")
    if any(term in lowered for term in ("test", "qa", "expected result", "given", "when", "then")):
        contexts.add("Testing")
    if any(term in lowered for term in ("deploy", "deployment", "devops center", "promotion")):
        contexts.add("Deployment")
    if any(term in lowered for term in ("error", "issue", "fail", "troubleshoot", "debug")):
        contexts.add("Troubleshooting")
    return [context for context in USAGE_CONTEXTS if context in contexts]


def _aliases(objects: list[str], fields: list[str], metadata: list[str], concepts: list[str]) -> list[str]:
    aliases: list[str] = []
    for value in objects + fields + metadata:
        aliases.append(value.replace("__c", "").replace("__mdt", "").replace("__", " ").replace("_", " "))
    for concept in concepts:
        slug = concept.replace("-", " ").replace("_", " ")
        if slug.lower() != concept.lower():
            aliases.append(slug)
    return _merge(aliases)[:30]


def _keyword_terms(text: str, limit: int) -> list[str]:
    counts: Counter[str] = Counter()
    for token in TOKEN_RE.findall(text):
        lowered = token.lower()
        if lowered in STOPWORDS or len(lowered) < 3:
            continue
        counts[lowered] += 1
    return [term for term, _ in counts.most_common(limit)]


def _noun_terms(text: str, limit: int) -> list[str]:
    phrases: list[str] = []
    for match in re.finditer(r"\b([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){1,4})\b", text):
        phrase = match.group(1).strip()
        if not any(word.lower() in STOPWORDS for word in phrase.split()):
            phrases.append(phrase)
    phrases.extend(_keyword_terms(text, limit=limit))
    return _merge(phrases)[:limit]


def _extractive_summary(text: str, title: str) -> str:
    sentences = _sentences(text)
    if not sentences:
        return f"Draft knowledge note generated from source content for {title}; human review is required."
    ranked = sorted(
        sentences[:80],
        key=lambda sentence: (
            -sum(1 for term in ("must", "should", "flow", "apex", "field", "object", "validation", "approval", "integration") if term in sentence.lower()),
            len(sentence),
        ),
    )
    selected = ranked[:2] if ranked else sentences[:2]
    return normalize_whitespace(" ".join(selected))[:700]


def _purpose(title: str, source_path: str, usage_context: list[str], concepts: list[str], objects: list[str]) -> str:
    parts = []
    if concepts:
        parts.append(", ".join(concepts[:3]))
    if objects:
        parts.append("Salesforce references " + ", ".join(objects[:4]))
    context = ", ".join(usage_context[:4]) if usage_context else "Documentation"
    subject = "; ".join(parts) if parts else title
    return f"Support {context} by converting `{source_path}` into reviewed, searchable knowledge about {subject}."


def _sentences(text: str) -> list[str]:
    compact = normalize_whitespace(text)
    raw = re.split(r"(?<=[.!?])\s+|\n{2,}", compact)
    return [sentence.strip() for sentence in raw if 20 <= len(sentence.strip()) <= 320]


def _fact_rows(**groups: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    labels = {
        "objects": "Salesforce object",
        "fields": "Salesforce field",
        "apex_classes": "Apex class/service",
        "apex_methods": "Apex method",
        "apex_triggers": "Apex trigger",
        "flow_names": "Flow",
        "flow_steps": "Flow step",
        "validation_rules": "Validation rule",
        "integration_points": "Integration point",
        "dependencies": "Dependency",
        "business_rules": "Business rule",
    }
    for key, values in groups.items():
        for value in values[:30]:
            rows.append({"type": labels.get(key, key), "value": value, "source": "detected", "confidence": "low"})
    return rows


def _quality_warnings(text: str, keywords: list[str], summary: str, source_path: str) -> list[str]:
    warnings: list[str] = []
    if low_value_text(text):
        warnings.append("Source section appears low-value or too short for a standalone knowledge note.")
    if not keywords:
        warnings.append("No indexing keywords were detected.")
    if not summary.strip():
        warnings.append("No extractive summary could be generated.")
    if not source_path:
        warnings.append("No source file reference is available.")
    return warnings


def _merge(*groups: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for group in groups:
        if group is None:
            continue
        values: Iterable[Any]
        if isinstance(group, str):
            values = [group]
        elif isinstance(group, Iterable):
            values = group
        else:
            values = [group]
        for value in values:
            text = normalize_whitespace(str(value or "")).strip()
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(text)
    return out


__all__ = [
    "USAGE_CONTEXTS",
    "enrich_document",
    "low_value_text",
    "normalized_checksum",
    "source_checksum",
]
