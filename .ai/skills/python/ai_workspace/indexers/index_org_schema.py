"""Index Salesforce org schema metadata into AI-readable JSON files."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_workspace.salesforce.cli import query_soql
from ai_workspace.salesforce.soql import (
    child_relationship_query,
    entity_definition_query,
    entity_definition_query_with_fields,
    field_definition_query,
    field_definition_query_with_fields,
)
from ai_workspace.utils.io import write_jsonl


ENTITY_FALLBACK_FIELDS = [
    [
        "QualifiedApiName",
        "Label",
        "PluralLabel",
        "NamespacePrefix",
        "IsCustomizable",
        "IsDeprecatedAndHidden",
        "IsQueryable",
        "IsSearchable",
        "IsTriggerable",
    ],
    [
        "QualifiedApiName",
        "Label",
        "PluralLabel",
        "NamespacePrefix",
        "IsCustomizable",
        "IsQueryable",
    ],
    [
        "QualifiedApiName",
        "Label",
        "NamespacePrefix",
    ],
    [
        "QualifiedApiName",
    ],
]

FIELD_FALLBACK_FIELDS = [
    [
        "EntityDefinition.QualifiedApiName",
        "QualifiedApiName",
        "Label",
        "DataType",
        "IsNillable",
        "IsCalculated",
        "IsIndexed",
        "IsUnique",
        "RelationshipName",
        "ReferenceTo",
        "ValueTypeId",
    ],
    [
        "EntityDefinition.QualifiedApiName",
        "QualifiedApiName",
        "Label",
        "DataType",
        "IsNillable",
        "IsCalculated",
        "RelationshipName",
        "ReferenceTo",
    ],
    [
        "EntityDefinition.QualifiedApiName",
        "QualifiedApiName",
        "Label",
        "DataType",
        "IsNillable",
        "IsCalculated",
    ],
    [
        "EntityDefinition.QualifiedApiName",
        "QualifiedApiName",
        "Label",
        "DataType",
    ],
    [
        "EntityDefinition.QualifiedApiName",
        "QualifiedApiName",
    ],
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Index Salesforce org schema metadata for Copilot AI context."
    )
    parser.add_argument("--org", required=True, help="Salesforce org alias or username.")
    parser.add_argument("--namespace", help="Managed package namespace to prioritize.")
    parser.add_argument("--out-dir", default=".ai/context/index", help="Output directory.")
    parser.add_argument(
        "--include-standard",
        action="store_true",
        help="Include obvious standard objects even when not referenced by namespaced fields.",
    )
    parser.add_argument(
        "--object-like",
        action="append",
        default=[],
        help="Repeatable object API name filter. Supports shell-style wildcards.",
    )
    args = parser.parse_args(argv)

    warnings: list[str] = []
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        entity_fallback_queries = [
            entity_definition_query_with_fields(args.namespace, fields)
            for fields in ENTITY_FALLBACK_FIELDS[1:]
        ]
        field_fallback_queries = [
            field_definition_query_with_fields(args.namespace, fields)
            for fields in FIELD_FALLBACK_FIELDS[1:]
        ]
        if args.namespace:
            entity_fallback_queries.extend(
                entity_definition_query_with_fields(None, fields)
                for fields in ENTITY_FALLBACK_FIELDS[1:]
            )
            field_fallback_queries.extend(
                field_definition_query_with_fields(None, fields)
                for fields in FIELD_FALLBACK_FIELDS[1:]
            )

        entities = _query_with_fallback(
            label="EntityDefinition",
            org=args.org,
            primary_query=entity_definition_query(args.namespace),
            fallback_queries=entity_fallback_queries,
            warnings=warnings,
        )
        fields = _query_with_fallback(
            label="FieldDefinition",
            org=args.org,
            primary_query=field_definition_query(args.namespace),
            fallback_queries=field_fallback_queries,
            warnings=warnings,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    child_relationships: list[dict[str, Any]] = []
    try:
        child_relationships = query_soql(args.org, child_relationship_query(args.namespace))
    except RuntimeError as exc:
        warning = (
            "ChildRelationship query failed; relationship cards will be derived "
            f"from FieldDefinition where possible. Error: {exc}"
        )
        warnings.append(warning)
        print(f"WARNING: {warning}", file=sys.stderr)

    selected_object_names = _selected_object_names(
        entities=entities,
        fields=fields,
        namespace=args.namespace,
        include_standard=args.include_standard,
        object_patterns=args.object_like,
    )
    object_cards = _build_object_cards(entities, selected_object_names, args.namespace)
    field_cards = _build_field_cards(fields, selected_object_names)
    relationship_cards = _build_relationship_cards(field_cards, child_relationships, selected_object_names)

    object_cards = _attach_counts(object_cards, field_cards, relationship_cards)

    object_cards.sort(key=lambda item: item["api_name"])
    field_cards.sort(key=lambda item: (item["object_api_name"], item["field_api_name"]))
    relationship_cards.sort(
        key=lambda item: (item["from_object"], item["field_api_name"], item["relationship_name"])
    )

    write_jsonl(out_dir / "sobject-cards.jsonl", object_cards)
    write_jsonl(out_dir / "field-cards.jsonl", field_cards)
    write_jsonl(out_dir / "relationship-cards.jsonl", relationship_cards)

    summary = {
        "org": args.org,
        "namespace": args.namespace,
        "object_count": len(object_cards),
        "field_count": len(field_cards),
        "relationship_count": len(relationship_cards),
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "schema-index-summary.json").write_text(
        json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        "Wrote schema index: "
        f"{len(object_cards)} object card(s), "
        f"{len(field_cards)} field card(s), "
        f"{len(relationship_cards)} relationship card(s)"
    )
    return 0


def _query_with_fallback(
    label: str,
    org: str,
    primary_query: str,
    fallback_queries: list[str],
    warnings: list[str],
) -> list[dict[str, Any]]:
    attempts = [primary_query] + fallback_queries
    errors: list[str] = []
    for index, query in enumerate(attempts):
        try:
            records = query_soql(org, query)
            if index > 0:
                warnings.append(f"{label} query used fallback attempt {index + 1}.")
            return records
        except RuntimeError as exc:
            errors.append(str(exc))
            if index == 0:
                warnings.append(f"{label} full query failed; trying smaller fallback query.")
    raise RuntimeError(f"{label} query failed after {len(attempts)} attempt(s): {' | '.join(errors)}")


def _selected_object_names(
    entities: list[dict[str, Any]],
    fields: list[dict[str, Any]],
    namespace: str | None,
    include_standard: bool,
    object_patterns: list[str],
) -> set[str]:
    namespaced_field_objects = {
        _entity_name_from_field(record)
        for record in fields
        if _is_namespaced_name(_string(record.get("QualifiedApiName")), namespace)
    }
    selected: set[str] = set()
    for record in entities:
        api_name = _string(record.get("QualifiedApiName"))
        if not api_name:
            continue
        if object_patterns and not _matches_any(api_name, object_patterns):
            continue
        if include_standard:
            selected.add(api_name)
            continue
        if _is_relevant_object(record, namespace, namespaced_field_objects):
            selected.add(api_name)

    for record in fields:
        object_api_name = _entity_name_from_field(record)
        field_api_name = _string(record.get("QualifiedApiName"))
        if not object_api_name:
            continue
        if object_patterns and not _matches_any(object_api_name, object_patterns):
            continue
        if (
            include_standard
            or object_api_name in selected
            or _is_nonstandard_object_name(object_api_name)
            or _is_namespaced_name(field_api_name, namespace)
        ):
            selected.add(object_api_name)
    return selected


def _is_relevant_object(
    record: dict[str, Any],
    namespace: str | None,
    namespaced_field_objects: set[str],
) -> bool:
    api_name = _string(record.get("QualifiedApiName"))
    namespace_prefix = _string(record.get("NamespacePrefix"))
    if api_name in namespaced_field_objects:
        return True
    if namespace and (namespace_prefix == namespace or api_name.startswith(f"{namespace}__")):
        return True
    return _is_nonstandard_object_name(api_name)


def _is_nonstandard_object_name(api_name: str) -> bool:
    return api_name.endswith("__c") or api_name.endswith("__mdt") or "__" in api_name


def _build_object_cards(
    entities: list[dict[str, Any]],
    selected_object_names: set[str],
    namespace: str | None,
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in entities:
        api_name = _string(record.get("QualifiedApiName"))
        if not api_name or api_name not in selected_object_names:
            continue
        seen.add(api_name)
        namespace_prefix = _string(record.get("NamespacePrefix"))
        managed_package_candidate = bool(
            namespace
            and (namespace_prefix == namespace or api_name.startswith(f"{namespace}__"))
        )
        cards.append(
            {
                "card_type": "sobject",
                "api_name": api_name,
                "label": _string(record.get("Label")),
                "plural_label": _string(record.get("PluralLabel")),
                "namespace": namespace_prefix,
                "source": "org_schema",
                "managed_package_candidate": managed_package_candidate,
                "is_customizable": _bool_or_none(record.get("IsCustomizable")),
                "is_queryable": _bool_or_none(record.get("IsQueryable")),
                "is_searchable": _bool_or_none(record.get("IsSearchable")),
                "is_triggerable": _bool_or_none(record.get("IsTriggerable")),
                "field_count": 0,
                "relationship_count": 0,
                "summary": _object_summary(api_name, record, managed_package_candidate),
            }
        )
    for api_name in sorted(selected_object_names - seen):
        cards.append(
            {
                "card_type": "sobject",
                "api_name": api_name,
                "label": "",
                "plural_label": "",
                "namespace": "",
                "source": "org_schema",
                "managed_package_candidate": bool(namespace and api_name.startswith(f"{namespace}__")),
                "is_customizable": None,
                "is_queryable": None,
                "is_searchable": None,
                "is_triggerable": None,
                "field_count": 0,
                "relationship_count": 0,
                "summary": f"SObject schema card for {api_name}; details were inferred from field metadata.",
            }
        )
    return cards


def _build_field_cards(
    fields: list[dict[str, Any]],
    selected_object_names: set[str],
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for record in fields:
        object_api_name = _entity_name_from_field(record)
        field_api_name = _string(record.get("QualifiedApiName"))
        if not object_api_name or not field_api_name or object_api_name not in selected_object_names:
            continue
        reference_to = _reference_list(record.get("ReferenceTo"))
        cards.append(
            {
                "card_type": "field",
                "object_api_name": object_api_name,
                "field_api_name": field_api_name,
                "label": _string(record.get("Label")),
                "data_type": _string(record.get("DataType")),
                "is_required": _is_required(record.get("IsNillable")),
                "is_calculated": _bool_or_none(record.get("IsCalculated")),
                "is_indexed": _bool_or_none(record.get("IsIndexed")),
                "is_unique": _bool_or_none(record.get("IsUnique")),
                "relationship_name": _string(record.get("RelationshipName")),
                "reference_to": reference_to,
                "source": "org_schema",
                "summary": _field_summary(object_api_name, field_api_name, record, reference_to),
            }
        )
    return cards


def _build_relationship_cards(
    field_cards: list[dict[str, Any]],
    child_relationships: list[dict[str, Any]],
    selected_object_names: set[str],
) -> list[dict[str, Any]]:
    cards: dict[tuple[str, str, str], dict[str, Any]] = {}
    for field in field_cards:
        reference_to = field.get("reference_to") or []
        relationship_name = _string(field.get("relationship_name"))
        if not reference_to and not relationship_name:
            continue
        from_object = _string(field.get("object_api_name"))
        field_api_name = _string(field.get("field_api_name"))
        key = (from_object, field_api_name, relationship_name)
        cards[key] = {
            "card_type": "relationship",
            "from_object": from_object,
            "field_api_name": field_api_name,
            "to_objects": sorted(reference_to),
            "relationship_name": relationship_name,
            "source": "org_schema",
            "summary": _relationship_summary(from_object, field_api_name, reference_to, relationship_name),
        }

    for record in child_relationships:
        child_object = _string(record.get("ChildSObject"))
        parent_object = _string(record.get("ParentSObject"))
        field_api_name = _string(record.get("Field"))
        relationship_name = _string(record.get("RelationshipName"))
        if not child_object or child_object not in selected_object_names:
            continue
        key = (child_object, field_api_name, relationship_name)
        cards.setdefault(
            key,
            {
                "card_type": "relationship",
                "from_object": child_object,
                "field_api_name": field_api_name,
                "to_objects": [parent_object] if parent_object else [],
                "relationship_name": relationship_name,
                "source": "org_schema",
                "summary": _relationship_summary(
                    child_object,
                    field_api_name,
                    [parent_object] if parent_object else [],
                    relationship_name,
                ),
            },
        )

    return list(cards.values())


def _attach_counts(
    object_cards: list[dict[str, Any]],
    field_cards: list[dict[str, Any]],
    relationship_cards: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    field_counts: dict[str, int] = {}
    relationship_counts: dict[str, int] = {}
    for field in field_cards:
        object_api_name = _string(field.get("object_api_name"))
        field_counts[object_api_name] = field_counts.get(object_api_name, 0) + 1
    for relationship in relationship_cards:
        from_object = _string(relationship.get("from_object"))
        relationship_counts[from_object] = relationship_counts.get(from_object, 0) + 1
    for card in object_cards:
        api_name = _string(card.get("api_name"))
        card["field_count"] = field_counts.get(api_name, 0)
        card["relationship_count"] = relationship_counts.get(api_name, 0)
    return object_cards


def _entity_name_from_field(record: dict[str, Any]) -> str:
    entity = record.get("EntityDefinition")
    if isinstance(entity, dict):
        return _string(entity.get("QualifiedApiName"))
    return _string(record.get("EntityDefinition.QualifiedApiName"))


def _reference_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return sorted(str(item) for item in value if item)
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return []
        if "," in cleaned:
            return sorted(part.strip() for part in cleaned.split(",") if part.strip())
        return [cleaned]
    return [str(value)]


def _matches_any(api_name: str, patterns: list[str]) -> bool:
    return any(
        fnmatch.fnmatchcase(api_name.lower(), pattern.lower())
        for pattern in patterns
    )


def _is_namespaced_name(name: str, namespace: str | None) -> bool:
    return bool(namespace and name.startswith(f"{namespace}__"))


def _is_required(is_nillable: Any) -> bool:
    if isinstance(is_nillable, bool):
        return not is_nillable
    return False


def _bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _string(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _object_summary(api_name: str, record: dict[str, Any], managed_package_candidate: bool) -> str:
    label = _string(record.get("Label"))
    package_note = " Managed package namespace candidate." if managed_package_candidate else ""
    return f"SObject schema card for {api_name}" + (f" ({label})." if label else ".") + package_note


def _field_summary(
    object_api_name: str,
    field_api_name: str,
    record: dict[str, Any],
    reference_to: list[str],
) -> str:
    data_type = _string(record.get("DataType"))
    base = f"Field schema card for {object_api_name}.{field_api_name}"
    if data_type:
        base += f" ({data_type})"
    if reference_to:
        base += f"; references {', '.join(reference_to)}"
    return base + "."


def _relationship_summary(
    from_object: str,
    field_api_name: str,
    to_objects: list[str],
    relationship_name: str,
) -> str:
    target = ", ".join(to_objects) if to_objects else "unknown target object"
    relation = f" via {relationship_name}" if relationship_name else ""
    field_part = f".{field_api_name}" if field_api_name else ""
    return f"Relationship from {from_object}{field_part} to {target}{relation}."


if __name__ == "__main__":
    raise SystemExit(main())
