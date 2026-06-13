"""Analyze local Work Item artifacts for KimbleOne/Kantata config impact."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_workspace.search.simple_search import search_jsonl, tokenize


CONFIG_TERMS = (
    "config",
    "configuration",
    "rule",
    "approval",
    "routing",
    "mapping",
    "rate",
    "template",
    "calendar",
    "billing",
    "invoice",
    "approval step",
    "policy",
    "setup",
    "kimbleone",
    "kantata",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze local Work Item config impact.")
    parser.add_argument("--work-item", required=True)
    parser.add_argument("--work-item-dir")
    parser.add_argument("--index-dir", default=".ai/context/index")
    parser.add_argument("--out")
    parser.add_argument("--report-out")
    args = parser.parse_args(argv)

    work_item_dir = Path(args.work_item_dir or f".ai/context/work-items/{args.work_item}")
    index_dir = Path(args.index_dir)
    out_path = Path(args.out or work_item_dir / "config-impact.yaml")
    report_path = Path(args.report_out or f".ai/outputs/config-impact/{args.work_item}.config-impact.md")

    analysis = analyze_config_impact(args.work_item, work_item_dir, index_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_impact_yaml(analysis), encoding="utf-8")
    report_path.write_text(_impact_markdown(analysis), encoding="utf-8")

    print(
        "Config impact analysis: "
        f"required={analysis['config_impact_required']} "
        f"confidence={analysis['confidence']}"
    )
    print(f"Wrote {out_path}")
    print(f"Wrote {report_path}")
    return 0


def analyze_config_impact(work_item: str, work_item_dir: Path, index_dir: Path) -> dict[str, Any]:
    warnings: list[str] = []
    source_artifacts: list[str] = []
    texts: list[str] = []

    for path in _input_paths(work_item, work_item_dir):
        text = _read_optional(path, warnings)
        if text:
            texts.append(text)
            source_artifacts.append(path.as_posix())

    combined_text = "\n".join(texts)
    matched_terms = _matched_terms(combined_text)
    relevant_config_path = work_item_dir / "relevant-config-records.yaml"
    relevant_config_has_content = bool(_read_optional(relevant_config_path, warnings))
    if relevant_config_has_content and relevant_config_path.as_posix() not in source_artifacts:
        source_artifacts.append(relevant_config_path.as_posix())

    query = _query_from_text(combined_text, matched_terms, work_item)
    config_index = index_dir / "config-record-cards.jsonl"
    config_matches: list[dict[str, Any]] = []
    if config_index.exists():
        source_artifacts.append(config_index.as_posix())
        config_matches = search_jsonl(str(config_index), query, 20)
    else:
        warnings.append(f"Missing config record index: {config_index.as_posix()}")

    impacted_objects = sorted({
        str(record.get("object_api_name"))
        for record in config_matches
        if record.get("object_api_name")
    })
    impacted_records = sorted({
        str(record.get("record_key"))
        for record in config_matches
        if record.get("record_key")
    })

    decision = _decision(matched_terms, relevant_config_has_content, config_matches)
    confidence = _confidence(matched_terms, relevant_config_has_content, config_matches)
    reasoning = _reasoning(matched_terms, relevant_config_has_content, config_matches, warnings)

    if decision == "true":
        promotion_strategy = "config_delta_pack_required"
        config_pack_required = "true"
    elif decision == "false":
        promotion_strategy = "none"
        config_pack_required = "false"
    else:
        promotion_strategy = "analyze_only"
        config_pack_required = "unknown"

    return {
        "work_item": work_item,
        "status": "draft",
        "config_impact_required": decision,
        "confidence": confidence,
        "reasoning": reasoning,
        "matched_terms": matched_terms,
        "impacted_config_objects": impacted_objects,
        "impacted_config_records": impacted_records,
        "config_pack_required": config_pack_required,
        "config_pack_name": f"{work_item}-config-delta",
        "promotion_strategy": promotion_strategy,
        "source_org": "IntDev",
        "target_environments": [],
        "risks": _risks(decision, warnings),
        "open_questions": _open_questions(decision, impacted_objects, impacted_records),
        "approval_required": "true" if decision in {"true", "unknown"} else "false",
        "source_artifacts": sorted(set(source_artifacts)),
        "warnings": warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _input_paths(work_item: str, work_item_dir: Path) -> list[Path]:
    return [
        work_item_dir / "work-item-summary.md",
        work_item_dir / "acceptance-criteria.md",
        work_item_dir / "context-pack.md",
        work_item_dir / "relevant-config-records.yaml",
        work_item_dir / "relevant-metadata.yaml",
        Path("specs/proposed") / f"{work_item}.solution-design.md",
        Path("specs/approved") / f"{work_item}.solution-design.md",
    ]


def _read_optional(path: Path, warnings: list[str]) -> str:
    if not path.exists():
        warnings.append(f"Missing input artifact: {path.as_posix()}")
        return ""
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        warnings.append(f"Could not read {path.as_posix()}: {exc}")
        return ""


def _matched_terms(text: str) -> list[str]:
    lowered = text.lower()
    return sorted(term for term in CONFIG_TERMS if term in lowered)


def _query_from_text(text: str, matched_terms: list[str], work_item: str) -> str:
    terms = [term for term in tokenize(text) if len(term) > 3]
    stable_terms = []
    seen = set()
    for term in list(matched_terms) + terms:
        normalized = term.lower()
        if normalized not in seen:
            seen.add(normalized)
            stable_terms.append(term)
        if len(stable_terms) >= 12:
            break
    if not stable_terms:
        stable_terms = [work_item]
    return " ".join(stable_terms)


def _decision(
    matched_terms: list[str],
    relevant_config_has_content: bool,
    config_matches: list[dict[str, Any]],
) -> str:
    if relevant_config_has_content or config_matches:
        return "true"
    if len(matched_terms) >= 2:
        return "unknown"
    if matched_terms:
        return "unknown"
    return "false"


def _confidence(
    matched_terms: list[str],
    relevant_config_has_content: bool,
    config_matches: list[dict[str, Any]],
) -> str:
    if relevant_config_has_content and config_matches:
        return "high"
    if config_matches or len(matched_terms) >= 3:
        return "medium"
    if matched_terms or relevant_config_has_content:
        return "low"
    return "low"


def _reasoning(
    matched_terms: list[str],
    relevant_config_has_content: bool,
    config_matches: list[dict[str, Any]],
    warnings: list[str],
) -> list[str]:
    reasons = []
    if matched_terms:
        reasons.append(f"Work Item/context text contains config-impact terms: {', '.join(matched_terms)}.")
    if relevant_config_has_content:
        reasons.append("Relevant config record summary exists for this Work Item.")
    if config_matches:
        reasons.append(f"Local config-record index returned {len(config_matches)} candidate match(es).")
    if not reasons:
        reasons.append("No strong local evidence of config record impact was found.")
    if warnings:
        reasons.append("Some input artifacts were missing, so the analysis is incomplete.")
    return reasons


def _risks(decision: str, warnings: list[str]) -> list[str]:
    risks = []
    if decision in {"true", "unknown"}:
        risks.append("Configuration impact must remain separate from Salesforce metadata deployment.")
        risks.append("Stable external keys must be confirmed before any future apply process.")
    if warnings:
        risks.append("Missing local artifacts may hide configuration dependencies.")
    return risks


def _open_questions(decision: str, impacted_objects: list[str], impacted_records: list[str]) -> list[str]:
    questions = []
    if decision in {"true", "unknown"}:
        questions.append("Which configuration objects and records are actually in scope?")
        questions.append("What stable external keys should identify each config record?")
        questions.append("What target environments require this config delta?")
    if not impacted_objects:
        questions.append("No impacted config objects were confirmed from local indexed records.")
    if not impacted_records:
        questions.append("No impacted config record keys were confirmed from local indexed records.")
    return questions


def _impact_yaml(analysis: dict[str, Any]) -> str:
    lines = [
        f"work_item: {_yaml_scalar(analysis['work_item'])}",
        f"status: {_yaml_scalar(analysis['status'])}",
        f"config_impact_required: {analysis['config_impact_required']}",
        f"confidence: {_yaml_scalar(analysis['confidence'])}",
        "reasoning:",
    ]
    lines.extend(_yaml_list_items(analysis["reasoning"]))
    lines.append("impacted_config_objects:")
    lines.extend(_yaml_list_items(analysis["impacted_config_objects"]))
    lines.append("impacted_config_records:")
    lines.extend(_yaml_list_items(analysis["impacted_config_records"]))
    lines.extend(
        [
            f"config_pack_required: {analysis['config_pack_required']}",
            f"config_pack_name: {_yaml_scalar(analysis['config_pack_name'])}",
            f"promotion_strategy: {_yaml_scalar(analysis['promotion_strategy'])}",
            f"source_org: {_yaml_scalar(analysis['source_org'])}",
            "target_environments:",
        ]
    )
    lines.extend(_yaml_list_items(analysis["target_environments"]))
    lines.append("risks:")
    lines.extend(_yaml_list_items(analysis["risks"]))
    lines.append("open_questions:")
    lines.extend(_yaml_list_items(analysis["open_questions"]))
    lines.append(f"approval_required: {analysis['approval_required']}")
    lines.append("source_artifacts:")
    lines.extend(_yaml_list_items(analysis["source_artifacts"]))
    lines.append("warnings:")
    lines.extend(_yaml_list_items(analysis["warnings"]))
    lines.append(f"generated_at: {_yaml_scalar(analysis['generated_at'])}")
    return "\n".join(lines) + "\n"


def _impact_markdown(analysis: dict[str, Any]) -> str:
    required = {"true": "yes", "false": "no"}.get(str(analysis["config_impact_required"]), "unknown")
    lines = [
        f"# Config Impact Analysis — {analysis['work_item']}",
        "",
        "## Decision",
        "",
        f"Config impact required: **{required}**",
        "",
        "## Confidence",
        "",
        str(analysis["confidence"]),
        "",
        "## Reasoning",
        "",
    ]
    lines.extend(_md_bullets(analysis["reasoning"]))
    lines.extend(["", "## Impacted Config Objects", ""])
    lines.extend(_md_bullets(analysis["impacted_config_objects"]))
    lines.extend(["", "## Impacted Config Records", ""])
    lines.extend(_md_bullets(analysis["impacted_config_records"]))
    lines.extend(
        [
            "",
            "## Potential Config Pack",
            "",
            f"- Name: `{analysis['config_pack_name']}`",
            f"- Required: {analysis['config_pack_required']}",
            "",
            "## Promotion Strategy",
            "",
            f"`{analysis['promotion_strategy']}`",
            "",
            "## Risks",
            "",
        ]
    )
    lines.extend(_md_bullets(analysis["risks"]))
    lines.extend(["", "## Open Questions", ""])
    lines.extend(_md_bullets(analysis["open_questions"]))
    lines.extend(["", "## Source Artifacts", ""])
    lines.extend(_md_bullets(analysis["source_artifacts"]))
    if analysis["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(_md_bullets(analysis["warnings"]))
    return "\n".join(lines) + "\n"


def _yaml_list_items(values: list[str]) -> list[str]:
    if not values:
        return ["  []"]
    return [f"  - {_yaml_scalar(value)}" for value in values]


def _yaml_scalar(value: Any) -> str:
    return json.dumps(str(value), ensure_ascii=True)


def _md_bullets(values: list[str]) -> list[str]:
    if not values:
        return ["- None confirmed."]
    return [f"- {value}" for value in values]


if __name__ == "__main__":
    raise SystemExit(main())
