"""Index explicitly allow-listed anonymized configuration records."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_workspace.salesforce.cli import query_soql
from ai_workspace.security.redactor import load_masking_policy, load_simple_yaml, mask_record
from ai_workspace.utils.io import write_jsonl


DEFAULT_BLOCKED_FIELDS = {
    "Id",
    "OwnerId",
    "CreatedById",
    "CreatedDate",
    "LastModifiedById",
    "LastModifiedDate",
    "SystemModstamp",
}

FIELD_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?$")
OBJECT_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
ORDER_DIRECTION_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\s+(?:ASC|DESC))?$", re.IGNORECASE)
SALESFORCE_ID_RE = re.compile(r"^[A-Za-z0-9]{15}(?:[A-Za-z0-9]{3})?$")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Index explicitly registered anonymized config records for Copilot AI context."
    )
    parser.add_argument("--org", required=True, help="Salesforce org alias or username.")
    parser.add_argument("--registry", required=True, help="Config object registry YAML path.")
    parser.add_argument("--masking-policy", required=True, help="Masking policy YAML path.")
    parser.add_argument(
        "--out",
        default=".ai/context/index/config-record-cards.jsonl",
        help="Output JSONL path.",
    )
    args = parser.parse_args(argv)

    warnings: list[str] = []

    try:
        registry = _load_registry(args.registry)
        masking_policy = load_masking_policy(args.masking_policy)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    summary_path = out_path.with_name("config-record-index-summary.json")
    records: list[dict[str, Any]] = []
    object_count_indexed = 0

    objects = registry.get("objects", {})
    if not isinstance(objects, dict):
        print("ERROR: registry field 'objects' must be a mapping", file=sys.stderr)
        return 1

    for object_api_name in sorted(objects):
        object_config = objects[object_api_name]
        if not isinstance(object_config, dict):
            warnings.append(f"Skipping {object_api_name}: registry object entry is not a mapping.")
            continue
        if not object_config.get("enabled", False):
            continue
        if object_config.get("index_records") is not True:
            continue
        if not _valid_object_name(object_api_name):
            warnings.append(f"Skipping {object_api_name}: invalid object API name.")
            continue

        try:
            query, selected_fields, external_key_fields, object_limit = _build_query(
                object_api_name=object_api_name,
                object_config=object_config,
                registry=registry,
                masking_policy=masking_policy,
            )
            queried_records = query_soql(args.org, query)
        except (RuntimeError, ValueError) as exc:
            warning = f"Object {object_api_name} query failed: {exc}"
            warnings.append(warning)
            print(f"WARNING: {warning}", file=sys.stderr)
            continue

        object_count_indexed += 1
        for row_number, raw_record in enumerate(queried_records[:object_limit], start=1):
            filtered = {
                field_name: raw_record.get(field_name)
                for field_name in selected_fields
                if field_name in raw_record
            }
            masked = mask_record(filtered, masking_policy)
            card = _config_record_card(
                object_api_name=object_api_name,
                object_config=object_config,
                source_org=args.org,
                row_number=row_number,
                masked_fields=masked,
                external_key_fields=external_key_fields,
            )
            records.append(card)

    records.sort(key=lambda item: (item["object_api_name"], item["record_key"]))
    write_jsonl(out_path, records)

    summary = {
        "org": args.org,
        "registry": args.registry,
        "object_count_configured": len(objects),
        "object_count_indexed": object_count_indexed,
        "record_count": len(records),
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        "Wrote config record index: "
        f"{len(records)} record card(s) from {object_count_indexed} object(s)"
    )
    return 0


def _load_registry(path: str) -> dict[str, Any]:
    loaded = load_simple_yaml(path)
    if not isinstance(loaded, dict):
        raise ValueError(f"Registry must be a YAML mapping: {path}")
    return loaded


def _build_query(
    object_api_name: str,
    object_config: dict[str, Any],
    registry: dict[str, Any],
    masking_policy: dict[str, Any],
) -> tuple[str, list[str], list[str], int]:
    defaults = registry.get("defaults", {})
    if not isinstance(defaults, dict):
        defaults = {}

    external_key_fields = _string_list(object_config.get("external_key"))
    include_fields = _string_list(object_config.get("include_fields"))
    if not include_fields and external_key_fields:
        include_fields = list(external_key_fields)

    blocked_fields = _blocked_fields(defaults, object_config, masking_policy)
    selected_fields = sorted(
        field
        for field in set(include_fields + external_key_fields)
        if field not in blocked_fields
    )
    if not selected_fields:
        raise ValueError("no queryable fields remain after applying include/exclude/blocked fields")
    invalid_fields = [field for field in selected_fields if not _valid_field_name(field)]
    if invalid_fields:
        raise ValueError(f"invalid field name(s): {', '.join(invalid_fields)}")

    query = f"SELECT {', '.join(selected_fields)} FROM {object_api_name}"
    where_clause = object_config.get("where")
    if where_clause:
        if not isinstance(where_clause, str):
            raise ValueError("where clause must be a string")
        query += f" WHERE {where_clause}"

    order_by = _string_list(object_config.get("order_by"))
    if order_by:
        invalid_order = [field for field in order_by if not ORDER_DIRECTION_RE.fullmatch(field)]
        if invalid_order:
            raise ValueError(f"invalid order_by value(s): {', '.join(invalid_order)}")
        query += f" ORDER BY {', '.join(order_by)}"

    max_records = _max_records(object_config, defaults, masking_policy)
    query += f" LIMIT {max_records}"
    return query, selected_fields, [field for field in external_key_fields if field in selected_fields], max_records


def _blocked_fields(
    defaults: dict[str, Any],
    object_config: dict[str, Any],
    masking_policy: dict[str, Any],
) -> set[str]:
    blocked = set(DEFAULT_BLOCKED_FIELDS)
    blocked.update(_string_list(defaults.get("exclude_fields")))
    blocked.update(_string_list(object_config.get("exclude_fields")))
    blocked.update(_string_list(masking_policy.get("blocked_fields")))
    allow_fields = set(_string_list(object_config.get("allow_fields")))
    return blocked - allow_fields


def _max_records(
    object_config: dict[str, Any],
    defaults: dict[str, Any],
    masking_policy: dict[str, Any],
) -> int:
    policy_limits = masking_policy.get("limits", {})
    if not isinstance(policy_limits, dict):
        policy_limits = {}
    configured = (
        object_config.get("max_records")
        or defaults.get("max_records")
        or policy_limits.get("max_records_per_object_default")
        or 500
    )
    if not isinstance(configured, int) or configured < 1:
        return 500
    return configured


def _config_record_card(
    object_api_name: str,
    object_config: dict[str, Any],
    source_org: str,
    row_number: int,
    masked_fields: dict[str, Any],
    external_key_fields: list[str],
) -> dict[str, Any]:
    external_key = {
        field: masked_fields[field]
        for field in external_key_fields
        if field in masked_fields and masked_fields[field] is not None
    }
    record_key = _record_key(object_api_name, external_key, row_number)
    checksum = _checksum(masked_fields)
    return {
        "card_type": "config_record",
        "object_api_name": object_api_name,
        "record_key": record_key,
        "category": str(object_config.get("category") or "unknown"),
        "ai_visibility": str(object_config.get("ai_visibility") or "anonymized_records"),
        "source": "org_config_records",
        "source_org": source_org,
        "external_key": external_key,
        "fields": masked_fields,
        "references": _references(masked_fields),
        "checksum": checksum,
        "summary": f"Anonymized config record card for {record_key}.",
    }


def _record_key(object_api_name: str, external_key: dict[str, Any], row_number: int) -> str:
    if external_key:
        joined = "|".join(f"{field}={external_key[field]}" for field in sorted(external_key))
        return f"{object_api_name}:{joined}"
    return f"{object_api_name}:row_{row_number}"


def _references(fields: dict[str, Any]) -> list[dict[str, str]]:
    references: list[dict[str, str]] = []
    for field_name, value in sorted(fields.items()):
        if value in (None, "", "[REDACTED]"):
            continue
        if _reference_candidate(field_name, value):
            references.append({"field": field_name, "target_hint": str(value)})
    return references


def _reference_candidate(field_name: str, value: Any) -> bool:
    if not field_name.endswith("__c"):
        return False
    value_text = str(value)
    field_hint = any(
        token in field_name.lower()
        for token in ("related", "parent", "rule", "config", "step", "type")
    )
    return bool(SALESFORCE_ID_RE.fullmatch(value_text) or field_hint)


def _checksum(masked_fields: dict[str, Any]) -> str:
    stable = json.dumps(masked_fields, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(stable.encode("utf-8")).hexdigest()


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    raise ValueError(f"Expected string list, got {type(value).__name__}")


def _valid_object_name(value: str) -> bool:
    return bool(OBJECT_NAME_RE.fullmatch(value))


def _valid_field_name(value: str) -> bool:
    return bool(FIELD_NAME_RE.fullmatch(value))


if __name__ == "__main__":
    raise SystemExit(main())
