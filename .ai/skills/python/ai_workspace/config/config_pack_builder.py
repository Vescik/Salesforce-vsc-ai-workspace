"""Build a skeleton KimbleOne/Kantata config delta pack folder."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ai_workspace.security.redactor import load_simple_yaml


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a skeleton config delta pack.")
    parser.add_argument("--work-item", required=True)
    parser.add_argument("--config-impact", required=True)
    parser.add_argument("--out-dir")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    impact = load_simple_yaml(args.config_impact)
    if not isinstance(impact, dict):
        raise SystemExit(f"config impact file must be a mapping: {args.config_impact}")

    out_dir = Path(args.out_dir or f"config/kimbleone-packs/{args.work_item}")
    create_pack(args.work_item, impact, out_dir, args.dry_run)
    print(f"Wrote config pack skeleton to {out_dir}")
    return 0


def create_pack(work_item: str, impact: dict[str, Any], out_dir: Path, dry_run: bool) -> None:
    records_dir = out_dir / "records"
    rollback_dir = out_dir / "rollback"
    dry_run_dir = out_dir / "dry-run"
    for directory in (records_dir, rollback_dir, dry_run_dir):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".gitkeep").write_text("", encoding="utf-8")

    (out_dir / "pack.yaml").write_text(_pack_yaml(work_item, impact, dry_run), encoding="utf-8")
    (out_dir / "README.md").write_text(_readme(work_item, impact, dry_run), encoding="utf-8")


def _pack_yaml(work_item: str, impact: dict[str, Any], dry_run: bool) -> str:
    lines = [
        f"work_item: {_yaml_scalar(work_item)}",
        "status: draft",
        "pack_type: kimbleone_config_delta",
        f"source_org: {_yaml_scalar(str(impact.get('source_org') or 'IntDev'))}",
        f"config_impact_required: {_yaml_boolish(impact.get('config_impact_required'))}",
        "impacted_config_objects:",
    ]
    lines.extend(_yaml_list_items(_string_list(impact.get("impacted_config_objects"))))
    lines.append("impacted_config_records:")
    lines.extend(_yaml_list_items(_string_list(impact.get("impacted_config_records"))))
    lines.extend(
        [
            "deployment_order:",
            "  []",
            "records:",
            "  []",
            "approval_required: true",
            "apply_supported: false",
            f"dry_run: {_yaml_boolish(dry_run)}",
            "notes:",
            "  - \"Skeleton config delta pack only; no records are applied by this tool.\"",
            "  - \"Use stable external keys before any future controlled apply process.\"",
            "  - \"Do not include Salesforce Id, OwnerId, or SystemModstamp fields.\"",
        ]
    )
    return "\n".join(lines) + "\n"


def _readme(work_item: str, impact: dict[str, Any], dry_run: bool) -> str:
    required = str(impact.get("config_impact_required") or "unknown")
    return "\n".join([
        f"# KimbleOne/Kantata Config Delta Pack - {work_item}",
        "",
        "This is a skeleton config delta pack generated from local config impact analysis.",
        "",
        "## Scope",
        "",
        f"- Work Item: `{work_item}`",
        f"- Config impact required: `{required}`",
        f"- Dry-run skeleton generated: `{str(dry_run).lower()}`",
        "- Apply supported by this tool: `false`",
        "",
        "## Rules",
        "",
        "- No records are applied by this tool.",
        "- Records must use stable external keys.",
        "- Do not include Salesforce `Id`, `OwnerId`, `SystemModstamp`, or other environment-specific system fields.",
        "- Do not include transactional records.",
        "- Keep configuration promotion separate from DevOps Center metadata promotion.",
        "- Production apply is out of scope and requires manual approval or future controlled tooling.",
        "",
        "## Folder Structure",
        "",
        "- `records/`: future reviewed config delta records.",
        "- `rollback/`: future rollback planning artifacts.",
        "- `dry-run/`: future dry-run output artifacts.",
        "",
    ]) + "\n"


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return []


def _yaml_list_items(values: list[str]) -> list[str]:
    if not values:
        return ["  []"]
    return [f"  - {_yaml_scalar(value)}" for value in values]


def _yaml_scalar(value: Any) -> str:
    return json.dumps(str(value), ensure_ascii=True)


def _yaml_boolish(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).lower()
    if text in {"true", "false", "unknown"}:
        return text
    return _yaml_scalar(value)


if __name__ == "__main__":
    raise SystemExit(main())
