"""Compare two local config-record-card JSONL files."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare local config record card indexes.")
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    source_records = _load_jsonl(Path(args.source))
    target_records = _load_jsonl(Path(args.target))
    diff = compare_records(source_records, target_records, args.source, args.target)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_markdown(diff), encoding="utf-8")
    if args.json_out:
        json_path = Path(args.json_out)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(diff, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        "Local config diff: "
        f"added={len(diff['added'])} removed={len(diff['removed'])} "
        f"changed={len(diff['changed'])} unchanged={len(diff['unchanged'])}"
    )
    print(f"Wrote {out_path}")
    return 0


def compare_records(
    source_records: list[dict[str, Any]],
    target_records: list[dict[str, Any]],
    source_path: str,
    target_path: str,
) -> dict[str, Any]:
    source = {_record_key(record, index): record for index, record in enumerate(source_records, start=1)}
    target = {_record_key(record, index): record for index, record in enumerate(target_records, start=1)}
    source_keys = set(source)
    target_keys = set(target)
    common = source_keys & target_keys
    changed = [
        key for key in common
        if str(source[key].get("checksum") or "") != str(target[key].get("checksum") or "")
    ]
    unchanged = sorted(common - set(changed))
    return {
        "source": source_path,
        "target": target_path,
        "added": sorted(source_keys - target_keys),
        "removed": sorted(target_keys - source_keys),
        "changed": sorted(changed),
        "unchanged": unchanged,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            loaded = json.loads(line)
            if isinstance(loaded, dict):
                records.append(loaded)
    return records


def _record_key(record: dict[str, Any], row_number: int) -> str:
    return str(record.get("record_key") or f"row_{row_number}")


def _markdown(diff: dict[str, Any]) -> str:
    lines = [
        "# Local Config Record Diff",
        "",
        f"- Source: `{diff['source']}`",
        f"- Target: `{diff['target']}`",
        f"- Generated at: `{diff['generated_at']}`",
        "",
        "## Summary",
        "",
        "| Category | Count |",
        "| --- | ---: |",
        f"| Added | {len(diff['added'])} |",
        f"| Removed | {len(diff['removed'])} |",
        f"| Changed checksum | {len(diff['changed'])} |",
        f"| Unchanged | {len(diff['unchanged'])} |",
        "",
    ]
    for key, title in (("added", "Added"), ("removed", "Removed"), ("changed", "Changed Checksum")):
        lines.extend([f"## {title}", ""])
        values = diff[key]
        if values:
            lines.extend(f"- `{value}`" for value in values)
        else:
            lines.append("- None")
        lines.append("")
    lines.extend([
        "## Notes",
        "",
        "- This is a local-only comparison of config record card indexes.",
        "- No Salesforce org was queried by this command.",
        "- No records were applied or modified.",
    ])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
