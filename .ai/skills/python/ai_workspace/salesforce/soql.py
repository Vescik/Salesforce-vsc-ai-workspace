"""SOQL builders for schema-only Salesforce indexing."""

from __future__ import annotations


ENTITY_DEFINITION_FIELDS = [
    "QualifiedApiName",
    "Label",
    "PluralLabel",
    "NamespacePrefix",
    "IsCustomizable",
    "IsDeprecatedAndHidden",
    "IsQueryable",
    "IsSearchable",
    "IsTriggerable",
]

FIELD_DEFINITION_FIELDS = [
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
]

CHILD_RELATIONSHIP_FIELDS = [
    "ParentSObject",
    "ChildSObject",
    "Field",
    "RelationshipName",
]


def entity_definition_query(namespace: str | None) -> str:
    """Return a best-effort EntityDefinition query."""

    return _select_query(
        "EntityDefinition",
        ENTITY_DEFINITION_FIELDS,
        _schema_where(namespace, entity_alias=None),
        "QualifiedApiName",
    )


def field_definition_query(namespace: str | None) -> str:
    """Return a best-effort FieldDefinition query."""

    return _select_query(
        "FieldDefinition",
        FIELD_DEFINITION_FIELDS,
        _schema_where(namespace, entity_alias="EntityDefinition"),
        "EntityDefinition.QualifiedApiName, QualifiedApiName",
    )


def child_relationship_query(namespace: str | None) -> str:
    """Return a best-effort ChildRelationship query.

    Some Salesforce org/API combinations do not expose ChildRelationship as a
    queryable object through ``sf data query``. The schema indexer treats this as
    optional and can still derive relationship cards from FieldDefinition when
    relationship metadata is available there.
    """

    where_clause = ""
    if namespace:
        prefix = _quote_like(f"{namespace}__%")
        where_clause = (
            "WHERE ParentSObject LIKE "
            f"{prefix} OR ChildSObject LIKE {prefix}"
        )
    return _select_query(
        "ChildRelationship",
        CHILD_RELATIONSHIP_FIELDS,
        where_clause,
        "ParentSObject, ChildSObject, Field",
    )


def entity_definition_query_with_fields(namespace: str | None, fields: list[str]) -> str:
    """Return an EntityDefinition query with caller-selected fields."""

    return _select_query("EntityDefinition", fields, _schema_where(namespace, None), "QualifiedApiName")


def field_definition_query_with_fields(namespace: str | None, fields: list[str]) -> str:
    """Return a FieldDefinition query with caller-selected fields."""

    return _select_query(
        "FieldDefinition",
        fields,
        _schema_where(namespace, "EntityDefinition"),
        "EntityDefinition.QualifiedApiName, QualifiedApiName",
    )


def _select_query(object_name: str, fields: list[str], where_clause: str, order_by: str) -> str:
    query = f"SELECT {', '.join(fields)} FROM {object_name}"
    if where_clause:
        query += f" {where_clause}"
    if order_by:
        query += f" ORDER BY {order_by}"
    return query


def _schema_where(namespace: str | None, entity_alias: str | None) -> str:
    clauses = ["IsDeprecatedAndHidden = false"] if entity_alias is None else []
    if not namespace:
        return f"WHERE {' AND '.join(clauses)}" if clauses else ""

    namespace_value = _quote(namespace)
    namespace_prefix = _quote_like(f"{namespace}__%")
    custom_object_like = "'%__c'"
    custom_metadata_like = "'%__mdt'"
    entity_prefix = f"{entity_alias}." if entity_alias else ""

    namespace_clauses = [
        f"{entity_prefix}NamespacePrefix = {namespace_value}",
        f"{entity_prefix}QualifiedApiName LIKE {namespace_prefix}",
        f"{entity_prefix}QualifiedApiName LIKE {custom_object_like}",
        f"{entity_prefix}QualifiedApiName LIKE {custom_metadata_like}",
    ]
    if entity_alias:
        namespace_clauses.append(f"QualifiedApiName LIKE {namespace_prefix}")

    clauses.append(f"({' OR '.join(namespace_clauses)})")
    return f"WHERE {' AND '.join(clauses)}"


def _quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _quote_like(value: str) -> str:
    return _quote(value)
