"""Read-only Salesforce CLI wrapper for schema queries."""

from __future__ import annotations

import json
import subprocess
from typing import Any


def run_sf_json(args: list[str]) -> dict[str, Any]:
    """Run an sf CLI command that is expected to return JSON.

    This helper is intentionally narrow and read-only. Callers should pass only
    Salesforce CLI read commands. Errors include CLI stdout and stderr so query
    problems are visible, but this module does not print credentials or auth
    details itself.
    """

    if args[:2] != ["data", "query"]:
        raise RuntimeError("This Salesforce CLI helper only supports read-only 'sf data query' commands")

    command = ["sf"] + args
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Salesforce CLI executable 'sf' was not found on PATH") from exc

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()

    parsed: dict[str, Any] | None = None
    if stdout:
        try:
            loaded = json.loads(stdout)
            if isinstance(loaded, dict):
                parsed = loaded
        except json.JSONDecodeError as exc:
            if completed.returncode == 0:
                raise RuntimeError(
                    "Salesforce CLI returned non-JSON stdout: "
                    f"{stdout[:2000]}"
                ) from exc

    if completed.returncode != 0:
        message_parts = [f"Salesforce CLI command failed with exit code {completed.returncode}."]
        if stderr:
            message_parts.append(f"stderr: {stderr[:4000]}")
        if stdout:
            message_parts.append(f"stdout: {stdout[:4000]}")
        raise RuntimeError(" ".join(message_parts))

    if parsed is None:
        raise RuntimeError("Salesforce CLI returned no JSON stdout")

    status = parsed.get("status")
    if isinstance(status, int) and status != 0:
        raise RuntimeError(f"Salesforce CLI JSON status was non-zero: {json.dumps(parsed, sort_keys=True)[:4000]}")

    return parsed


def query_soql(org: str, query: str) -> list[dict[str, Any]]:
    """Run a read-only SOQL query through ``sf data query --json``."""

    result = run_sf_json(
        [
            "data",
            "query",
            "--target-org",
            org,
            "--query",
            query,
            "--json",
        ]
    )

    query_result = result.get("result", {})
    if not isinstance(query_result, dict):
        raise RuntimeError(f"Unexpected Salesforce CLI query result shape: {json.dumps(result, sort_keys=True)[:4000]}")

    records = query_result.get("records", [])
    if not isinstance(records, list):
        raise RuntimeError(f"Unexpected Salesforce CLI records shape: {json.dumps(result, sort_keys=True)[:4000]}")

    return [record for record in records if isinstance(record, dict)]
