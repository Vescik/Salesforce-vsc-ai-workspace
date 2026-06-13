"""Masking and minimal YAML helpers for config record indexing."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


SALESFORCE_ID_RE = re.compile(r"^[A-Za-z0-9]{15}(?:[A-Za-z0-9]{3})?$")


def load_masking_policy(path: str) -> dict[str, Any]:
    """Load a masking policy from the project's simple YAML format."""

    loaded = load_simple_yaml(path)
    if not isinstance(loaded, dict):
        raise ValueError(f"Masking policy must be a YAML mapping: {path}")
    return loaded


def mask_record(record: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """Return a masked copy of a Salesforce record."""

    masked: dict[str, Any] = {}
    blocked_fields = _blocked_fields(policy)
    for field_name in sorted(record):
        if field_name == "attributes" or field_name in blocked_fields:
            continue
        masked[field_name] = mask_value(field_name, record[field_name], policy)
    return masked


def mask_value(field_name: str, value: Any, policy: dict[str, Any]) -> Any:
    """Mask a single field value according to the policy."""

    action = classify_field_action(field_name, policy)
    if action == "blocked":
        return None
    if value is None:
        return None
    if action == "redact":
        return "[REDACTED]"
    if action == "bucketize":
        return _bucketize(value)

    max_length = _max_string_length(policy)
    if isinstance(value, str):
        if SALESFORCE_ID_RE.fullmatch(value) and any(char.isdigit() for char in value):
            return "[SALESFORCE_ID]"
        return _truncate(value, max_length)
    if isinstance(value, list):
        return [mask_value(field_name, item, policy) for item in value]
    if isinstance(value, dict):
        return {
            str(key): mask_value(str(key), item, policy)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
            if str(key) not in _blocked_fields(policy)
        }
    return value


def classify_field_action(field_name: str, policy: dict[str, Any]) -> str:
    """Classify a field as blocked, redact, bucketize, summarize, or allow."""

    if field_name in _blocked_fields(policy):
        return "blocked"

    rules = policy.get("field_name_rules", {})
    if not isinstance(rules, dict):
        rules = {}

    for action in ("redact", "bucketize", "summarize"):
        patterns = rules.get(action, [])
        if _matches_any_pattern(field_name, patterns):
            return action

    return str(policy.get("default_action") or "allow_anonymized")


def load_simple_yaml(path: str) -> Any:
    """Load the small YAML subset used by this workspace.

    Supported:
    - mappings by indentation
    - lists of scalar values
    - strings, quoted strings, booleans, integers, null, and []
    - comments outside quoted strings

    Not supported:
    - anchors, aliases, multi-line block scalars, inline maps, nested list items,
      flow-style non-empty lists, or complex YAML tags.
    """

    source = Path(path)
    lines = source.read_text(encoding="utf-8").splitlines()
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]

    for line_number, raw_line in enumerate(lines, start=1):
        line = _strip_comment(raw_line).rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if "\t" in raw_line[:indent]:
            raise ValueError(f"Tabs are not supported in YAML indentation at {path}:{line_number}")
        content = line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError(f"Invalid YAML indentation at {path}:{line_number}")
        parent = stack[-1][1]

        if content == "[]" and isinstance(parent, list):
            continue

        if content.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"YAML list item without list parent at {path}:{line_number}")
            item_text = content[2:].strip()
            if ":" in item_text and not _is_quoted(item_text):
                raise ValueError(f"Inline mappings in lists are not supported at {path}:{line_number}")
            parent.append(_parse_scalar(item_text))
            continue

        key, value_text = _split_key_value(content, path, line_number)
        if not isinstance(parent, dict):
            raise ValueError(f"YAML mapping item under non-mapping parent at {path}:{line_number}")
        if value_text == "":
            container = _next_container(lines, line_number - 1, indent)
            parent[key] = container
            stack.append((indent, container))
        else:
            parent[key] = _parse_scalar(value_text)

    return root


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_double:
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if char == "#" and not in_single and not in_double:
            return line[:index]
    return line


def _split_key_value(content: str, path: str, line_number: int) -> tuple[str, str]:
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(content):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_double:
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if char == ":" and not in_single and not in_double:
            key = content[:index].strip()
            value = content[index + 1 :].strip()
            if not key:
                raise ValueError(f"Empty YAML key at {path}:{line_number}")
            return key, value
    raise ValueError(f"Expected YAML key/value mapping at {path}:{line_number}")


def _next_container(lines: list[str], current_index: int, parent_indent: int) -> Any:
    for raw_line in lines[current_index + 1 :]:
        line = _strip_comment(raw_line).rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()
        if indent <= parent_indent:
            return {}
        if content == "[]":
            return []
        return [] if content.startswith("- ") else {}
    return {}


def _parse_scalar(value: str) -> Any:
    if value == "[]":
        return []
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none", "~"}:
        return None
    if _is_quoted(value):
        quote = value[0]
        inner = value[1:-1]
        if quote == '"':
            return bytes(inner, "utf-8").decode("unicode_escape")
        return inner.replace("''", "'")
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def _is_quoted(value: str) -> bool:
    return len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}


def _blocked_fields(policy: dict[str, Any]) -> set[str]:
    blocked = policy.get("blocked_fields", [])
    if not isinstance(blocked, list):
        return set()
    return {str(field) for field in blocked}


def _matches_any_pattern(field_name: str, patterns: Any) -> bool:
    if not isinstance(patterns, list):
        return False
    return any(re.fullmatch(str(pattern), field_name, flags=re.IGNORECASE) for pattern in patterns)


def _max_string_length(policy: dict[str, Any]) -> int:
    limits = policy.get("limits", {})
    if not isinstance(limits, dict):
        return 500
    value = limits.get("max_string_length", 500)
    return value if isinstance(value, int) and value > 0 else 500


def _truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[:max_length] + "...[TRUNCATED]"


def _bucketize(value: Any) -> str | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "[BUCKETIZED]"
    if number == 0:
        return "0"
    if 1 <= abs(number) <= 100:
        return "1-100"
    if 101 <= abs(number) <= 1000:
        return "101-1000"
    if 1001 <= abs(number) <= 10000:
        return "1001-10000"
    if abs(number) > 10000:
        return ">10000"
    return "[BUCKETIZED]"
