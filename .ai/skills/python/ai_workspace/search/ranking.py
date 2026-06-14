"""Shared ranking constants and helpers for knowledge-aware search.

Extracted from ``indexers.build_context_pack`` so that the validator, MCP server,
and search layer can share one source of truth for the status/confidence
ordering. Adds ``accepted`` (used by ADRs) and ``deprecated`` to the rank tables
to match the JSON Schema introduced in Phase 1.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any


STATUS_RANK: dict[str, int] = {
    "reviewed": 0,
    "approved": 0,
    "accepted": 0,
    "": 1,
    "draft": 2,
    "deprecated": 3,
}

CONFIDENCE_RANK: dict[str, int] = {
    "high": 0,
    "medium": 1,
    "": 2,
    "low": 3,
}

RISK_PENALTY: dict[str, int] = {
    "possible_secret": 10,
    "missing_front_matter": 3,
    "stale_review": 2,
    "low_confidence": 1,
    "draft_status": 1,
    "missing_owner": 1,
}


def status_rank(record: dict[str, Any]) -> int:
    return STATUS_RANK.get(str(record.get("status") or "").lower(), 1)


def confidence_rank(record: dict[str, Any]) -> int:
    return CONFIDENCE_RANK.get(str(record.get("confidence") or "").lower(), 2)


def knowledge_quality_rank(record: dict[str, Any]) -> float:
    """Lower is better. Combines status, confidence, and risk-flag penalties."""

    flags = record.get("risk_flags") if isinstance(record.get("risk_flags"), list) else []
    penalty = sum(RISK_PENALTY.get(str(flag), 0) for flag in flags)
    return float(status_rank(record) * 10 + confidence_rank(record) + penalty)


def recency_negative_days(record: dict[str, Any]) -> float:
    """Return negative age in days so newer records sort earlier (ascending)."""

    raw = str(record.get("last_reviewed") or "").strip()
    if not raw or raw == "YYYY-MM-DD":
        return 1e9
    try:
        reviewed = date.fromisoformat(raw[:10])
    except ValueError:
        return 1e9
    return float((datetime.now(timezone.utc).date() - reviewed).days)


__all__ = [
    "STATUS_RANK",
    "CONFIDENCE_RANK",
    "RISK_PENALTY",
    "status_rank",
    "confidence_rank",
    "knowledge_quality_rank",
    "recency_negative_days",
]
