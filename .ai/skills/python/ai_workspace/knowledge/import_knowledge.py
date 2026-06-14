"""Import local source documents into curated draft knowledge notes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_workspace.knowledge.converters import dispatch as convert_document
from ai_workspace.knowledge.parse_documents import chunk_text, normalize_whitespace
from ai_workspace.knowledge.semantic import (
    enrich_document,
    low_value_text,
    normalized_checksum,
    source_checksum,
)
from ai_workspace.security.no_salesforce_ids import find_salesforce_id_candidates_in_text


DEFAULT_OWNER = "Salesforce Platform Team"
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SECRET_HINT_RE = re.compile(
    r"(?i)(api[_-]?key|client[_-]?secret|password|passwd|token|bearer\s+[A-Za-z0-9._~+/=-]{12,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create draft knowledge notes from local source documents.")
    parser.add_argument("--source", help="Single source file to import.")
    parser.add_argument("--manifest", help="Knowledge import manifest.")
    parser.add_argument("--domain", default="general")
    parser.add_argument("--title")
    parser.add_argument("--owner", default=DEFAULT_OWNER)
    parser.add_argument("--confidence", default="low")
    parser.add_argument("--status", default="draft")
    parser.add_argument("--out-dir", default=".ai/knowledge/domains")
    parser.add_argument("--max-chars", type=int, default=200_000)
    parser.add_argument("--chunk-size", type=int, default=6000)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if not args.source and not args.manifest:
        parser.error("Provide --source or --manifest")
    if args.source and args.manifest:
        parser.error("Use either --source or --manifest, not both")

    repo_root = Path(".").resolve()
    imported: list[dict[str, Any]] = []
    if args.manifest:
        imported.extend(_import_manifest(Path(args.manifest), args, repo_root))
    else:
        title = args.title or Path(args.source).stem.replace("-", " ").replace("_", " ").title()
        imported.extend(
            import_source(
                source=Path(args.source),
                domain=args.domain,
                title=title,
                owner=args.owner,
                confidence=args.confidence,
                status=args.status,
                out_dir=Path(args.out_dir),
                max_chars=args.max_chars,
                chunk_size=args.chunk_size,
                overwrite=args.overwrite,
                dry_run=args.dry_run,
                repo_root=repo_root,
            )
        )

    batch = _batch_name(args.manifest)
    report_paths = _write_report(batch, imported, dry_run=args.dry_run)
    for path in report_paths:
        print(f"Wrote {path}")
    for item in imported:
        status = "DRY-RUN" if item.get("dry_run") else "IMPORTED"
        print(f"{status}: {item.get('source')} -> {item.get('outputs')}")
    return 1 if any(item.get("parse_status") == "failed" for item in imported) else 0


def import_source(
    source: Path,
    domain: str,
    title: str,
    owner: str,
    confidence: str,
    status: str,
    out_dir: Path,
    max_chars: int,
    chunk_size: int,
    overwrite: bool,
    dry_run: bool,
    repo_root: Path,
    tags: list[str] | None = None,
    usage_context: list[str] | None = None,
    aliases: list[str] | None = None,
    key_concepts: list[str] | None = None,
    keywords: list[str] | None = None,
    related_objects: list[str] | None = None,
    related_fields: list[str] | None = None,
    related_config_objects: list[str] | None = None,
    related_metadata: list[str] | None = None,
    related_processes: list[str] | None = None,
    integration_points: list[str] | None = None,
    dependencies: list[str] | None = None,
    business_rules: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Import one source file into one or more markdown notes."""

    source = source.resolve()
    result = convert_document(source)
    text = _text_from_doc(result, max_chars=max_chars)
    sensitive_warnings = detect_sensitive_content(text)
    redacted_text = redact_sensitive_content(text)
    redaction_diff = _diff_redaction_counts(text, redacted_text)
    prohibited_classes = sorted({finding.get("candidate", "") for finding in find_salesforce_id_candidates_in_text(text) if finding.get("candidate")})
    converter_metrics = _converter_metrics(result, prohibited_classes, redaction_diff)
    chunks = _logical_chunks(result, redacted_text, max_chars=chunk_size) or [{"text": "", "anchor": "empty-source", "heading": title}]
    target_dir = _resolve_out_dir(out_dir, domain, repo_root)
    source_rel = _repo_relative(source, repo_root)
    checksum = source_checksum(source) if source.exists() else _checksum(redacted_text)
    slug = _slug(title)
    outputs: list[str] = []
    records: list[dict[str, Any]] = []
    seen_chunks: set[str] = set()
    skipped_duplicates: list[str] = []

    for index, chunk in enumerate(chunks, start=1):
        part = str(chunk.get("text") or "")
        chunk_hash = normalized_checksum(part)
        if chunk_hash in seen_chunks:
            skipped_duplicates.append(str(chunk.get("anchor") or f"part-{index}"))
            continue
        seen_chunks.add(chunk_hash)
        suffix = "" if len(chunks) == 1 else f".part-{index:03d}"
        target = target_dir / f"{slug}{suffix}.md"
        if target.exists() and not overwrite and not dry_run:
            raise FileExistsError(f"Knowledge note already exists: {target}")
        semantic = enrich_document(
            part,
            result,
            title=title if len(chunks) == 1 else f"{title} (Part {index})",
            domain=domain,
            source_path=source_rel,
            manifest={
                "tags": tags or [],
                "usage_context": usage_context or [],
                "aliases": aliases or [],
                "key_concepts": key_concepts or [],
                "keywords": keywords or [],
                "related_objects": related_objects or [],
                "related_fields": related_fields or [],
                "related_config_objects": related_config_objects or [],
                "related_metadata": related_metadata or [],
                "related_processes": related_processes or [],
                "integration_points": integration_points or [],
                "dependencies": dependencies or [],
                "business_rules": business_rules or [],
            },
        )
        note_text = _knowledge_note(
            title=title if len(chunks) == 1 else f"{title} (Part {index})",
            domain=domain,
            source_file=source_rel,
            source_checksum=checksum,
            owner=owner,
            status=status,
            confidence=confidence,
            related_objects=related_objects or [],
            related_config_objects=related_config_objects or [],
            related_processes=related_processes or [],
            extracted_text=part,
            parse_result=result,
            semantic=semantic,
            sensitive_warnings=sensitive_warnings,
            part=index,
            part_count=len(chunks),
            anchor=str(chunk.get("anchor") or f"part-{index}"),
        )
        outputs.append(_repo_relative(target, repo_root))
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(note_text, encoding="utf-8")
        records.append(
            {
                "source": source_rel,
                "outputs": [_repo_relative(target, repo_root)],
                "domain": domain,
                "title": title,
                "parse_status": result.get("parse_status"),
                "warnings": list(result.get("warnings") or []) + sensitive_warnings + list(semantic.get("quality_warnings") or []),
                "dry_run": dry_run,
                "source_checksum": checksum,
                "source_format": str(result.get("format") or result.get("source_format") or ""),
                "chunk_anchor": str(chunk.get("anchor") or ""),
                "low_value_content": low_value_text(part),
                "skipped_duplicate_chunks": skipped_duplicates,
                "extracted_entities": {
                    "related_objects": semantic.get("related_objects") or [],
                    "related_fields": semantic.get("related_fields") or [],
                    "related_metadata": semantic.get("related_metadata") or [],
                    "flow_steps": semantic.get("flow_steps") or [],
                    "business_rules": semantic.get("business_rules") or [],
                    "integration_points": semantic.get("integration_points") or [],
                    "dependencies": semantic.get("dependencies") or [],
                },
                **converter_metrics,
            }
        )

    if records:
        records[0]["outputs"] = outputs
    if records:
        return records[:1]
    return [
        {
            "source": source_rel,
            "outputs": [],
            "domain": domain,
            "title": title,
            "parse_status": result.get("parse_status"),
            "warnings": list(result.get("warnings") or []) + sensitive_warnings,
            "dry_run": dry_run,
            "source_checksum": checksum,
            "source_format": str(result.get("format") or result.get("source_format") or ""),
            "skipped_duplicate_chunks": skipped_duplicates,
            **converter_metrics,
        }
    ]


def _text_from_doc(result: dict[str, Any], max_chars: int) -> str:
    """Concatenate sections + tables + code blocks from a NormalizedDocument into a single text blob.

    Falls back to whatever ``parse_documents.extract_text`` produced (already wrapped
    into a single section by ``converters.dispatch``) when no structured data is
    available. Truncates at ``max_chars`` with a marker so downstream chunking has
    a deterministic upper bound.
    """

    parts: list[str] = []
    for section in result.get("sections") or []:
        heading = str(section.get("heading") or "").strip()
        body = str(section.get("body") or "").strip()
        level = int(section.get("level") or 1)
        if heading:
            parts.append(("#" * max(1, min(6, level))) + " " + heading)
        if body:
            parts.append(body)
    for table in result.get("tables") or []:
        caption = str(table.get("caption") or "").strip()
        if caption:
            parts.append(f"Table: {caption}")
        for row in table.get("rows") or []:
            parts.append(" | ".join(str(cell) for cell in row))
    for code in result.get("code_blocks") or []:
        lang = str(code.get("lang") or "").strip()
        text = str(code.get("text") or "")
        if text:
            parts.append(f"```{lang}\n{text}\n```")
    blob = "\n\n".join(part for part in parts if part)
    if len(blob) > max_chars:
        blob = blob[:max_chars] + "\n\n[TRUNCATED]"
    return blob


def _logical_chunks(result: dict[str, Any], fallback_text: str, max_chars: int) -> list[dict[str, str]]:
    """Split source content by converter structure before falling back to char chunks."""

    chunks: list[dict[str, str]] = []
    for section_index, section in enumerate(result.get("sections") or [], start=1):
        heading = str(section.get("heading") or f"Section {section_index}").strip()
        body = str(section.get("body") or "").strip()
        if not body:
            continue
        anchors = section.get("anchors") if isinstance(section.get("anchors"), list) else []
        anchor = str(anchors[0]) if anchors else f"section-{section_index}"
        section_text = redact_sensitive_content(f"# {heading}\n\n{body}" if heading else body)
        for part_index, text_part in enumerate(chunk_text(section_text, max_chars=max_chars, overlap=500) or [section_text], start=1):
            chunks.append({
                "text": text_part,
                "anchor": anchor if part_index == 1 else f"{anchor}-part-{part_index}",
                "heading": heading,
            })
    if chunks:
        return chunks
    return [
        {"text": part, "anchor": f"chunk-{index}", "heading": ""}
        for index, part in enumerate(chunk_text(fallback_text, max_chars=max_chars, overlap=500), start=1)
    ]


def _converter_metrics(result: dict[str, Any], prohibited_classes: list[str], redaction_diff: dict[str, int]) -> dict[str, Any]:
    metadata = result.get("metadata") or {}
    return {
        "converter": str(result.get("format") or "unknown"),
        "degraded": bool(result.get("degraded")),
        "sections_count": len(result.get("sections") or []),
        "tables_count": len(result.get("tables") or []),
        "code_blocks_count": len(result.get("code_blocks") or []),
        "speaker_notes_present": bool(metadata.get("speaker_notes_present")),
        "prohibited_classes_detected": prohibited_classes,
        "redaction_counts": redaction_diff,
    }


def _diff_redaction_counts(original: str, redacted: str) -> dict[str, int]:
    return {
        "emails": original.count("@") - redacted.count("@") if "[REDACTED_EMAIL]" in redacted else 0,
        "redacted_email_markers": redacted.count("[REDACTED_EMAIL]"),
        "redacted_token_markers": redacted.count("[REDACTED_TOKEN]") + redacted.count("[REDACTED]"),
        "redacted_private_keys": redacted.count("[REDACTED_PRIVATE_KEY]"),
    }


def detect_sensitive_content(text: str) -> list[str]:
    warnings: list[str] = []
    if EMAIL_RE.search(text):
        warnings.append("Source text contains email-like values; imported note redacts them.")
    if SECRET_HINT_RE.search(text):
        warnings.append("Source text contains secret/token-like values; imported note redacts likely sensitive strings.")
    return warnings


def redact_sensitive_content(text: str) -> str:
    redacted = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    redacted = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]{12,}", r"\1[REDACTED_TOKEN]", redacted)
    redacted = re.sub(
        r"(?i)\b(api[_-]?key|client[_-]?secret|password|passwd|token)\s*[:=]\s*['\"]?[^'\"\s]+",
        lambda match: f"{match.group(1)}=[REDACTED]",
        redacted,
    )
    redacted = re.sub(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        "[REDACTED_PRIVATE_KEY]",
        redacted,
        flags=re.DOTALL,
    )
    return redacted


def _import_manifest(manifest_path: Path, args: argparse.Namespace, repo_root: Path) -> list[dict[str, Any]]:
    manifest = _load_manifest(manifest_path)
    defaults = {
        "domain": manifest.get("default_domain") or args.domain or "general",
        "owner": manifest.get("default_owner") or args.owner or DEFAULT_OWNER,
        "confidence": manifest.get("default_confidence") or args.confidence or "low",
        "status": manifest.get("default_status") or args.status or "draft",
    }
    imported: list[dict[str, Any]] = []
    for item in manifest.get("files", []):
        if not item.get("enabled", False):
            continue
        source = Path(str(item.get("path") or ""))
        title = str(item.get("title") or source.stem.replace("-", " ").title())
        domain = str(item.get("domain") or defaults["domain"])
        imported.extend(
            import_source(
                source=source,
                domain=domain,
                title=title,
                owner=str(item.get("owner") or defaults["owner"]),
                confidence=str(item.get("confidence") or defaults["confidence"]),
                status=str(item.get("status") or defaults["status"]),
                out_dir=Path(args.out_dir),
                max_chars=args.max_chars,
                chunk_size=args.chunk_size,
                overwrite=args.overwrite,
                dry_run=args.dry_run,
                repo_root=repo_root,
                tags=[str(value) for value in item.get("tags", [])],
                usage_context=[str(value) for value in item.get("usage_context", [])],
                aliases=[str(value) for value in item.get("aliases", [])],
                key_concepts=[str(value) for value in item.get("key_concepts", [])],
                keywords=[str(value) for value in item.get("keywords", [])],
                related_objects=[str(value) for value in item.get("related_objects", [])],
                related_fields=[str(value) for value in item.get("related_fields", [])],
                related_config_objects=[str(value) for value in item.get("related_config_objects", [])],
                related_metadata=[str(value) for value in item.get("related_metadata", [])],
                related_processes=[str(value) for value in item.get("related_processes", [])],
                integration_points=[str(value) for value in item.get("integration_points", [])],
                dependencies=[str(value) for value in item.get("dependencies", [])],
                business_rules=[str(value) for value in item.get("business_rules", [])],
            )
        )
    return imported


def _load_manifest(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    data: dict[str, Any] = {"files": []}
    current_file: dict[str, Any] | None = None
    current_list_key: str | None = None
    for raw in lines:
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()
        if content == "files:":
            current_list_key = None
            continue
        if content.startswith("- ") and indent <= 2:
            key, value = _split_key_value(content[2:])
            current_file = {key: _parse_scalar(value)}
            data["files"].append(current_file)
            current_list_key = None
            continue
        if current_file is not None and indent >= 4:
            if content.startswith("- "):
                if current_list_key:
                    current_file.setdefault(current_list_key, []).append(_parse_scalar(content[2:].strip()))
                continue
            key, value = _split_key_value(content)
            if value == "":
                current_file[key] = []
                current_list_key = key
            else:
                current_file[key] = _parse_scalar(value)
                current_list_key = None
            continue
        key, value = _split_key_value(content)
        data[key] = _parse_scalar(value)
        current_list_key = None
    return data


def _knowledge_note(
    title: str,
    domain: str,
    source_file: str,
    source_checksum: str,
    owner: str,
    status: str,
    confidence: str,
    related_objects: list[str],
    related_config_objects: list[str],
    related_processes: list[str],
    extracted_text: str,
    parse_result: dict[str, Any],
    semantic: dict[str, Any],
    sensitive_warnings: list[str],
    part: int,
    part_count: int,
    anchor: str,
) -> str:
    now = datetime.now(timezone.utc).date().isoformat()
    source_format = str(parse_result.get("format") or parse_result.get("source_format") or "")
    warnings = list(parse_result.get("warnings") or []) + sensitive_warnings + list(semantic.get("quality_warnings") or [])
    related_objects_all = sorted(set([item for item in (semantic.get("related_objects") or []) + related_objects if str(item).strip()]))
    related_processes_all = sorted(set([item for item in (semantic.get("related_processes") or []) + related_processes if str(item).strip()]))
    lines = [
        "---",
        f"title: {json.dumps(title)}",
        f"domain: {json.dumps(domain)}",
        'source_type: "internal_knowledge"',
        f"purpose: {json.dumps(str(semantic.get('purpose') or ''))}",
        f"source_file: {json.dumps(source_file)}",
        f"source_format: {json.dumps(source_format)}",
        f"source_checksum: {json.dumps(source_checksum)}",
        f"owner: {json.dumps(owner)}",
        f"status: {json.dumps(status)}",
        f"confidence: {json.dumps(confidence)}",
        f"last_reviewed: {json.dumps(now)}",
        "applies_to:",
        '  - "KimbleOne/Kantata"',
        "usage_context:",
        *_yaml_list_lines(semantic.get("usage_context") or []),
        "tags:",
        *_yaml_list_lines(semantic.get("tags") or []),
        "aliases:",
        *_yaml_list_lines(semantic.get("aliases") or []),
        "key_concepts:",
        *_yaml_list_lines(semantic.get("key_concepts") or []),
        "related_objects:",
        *_yaml_list_lines(related_objects_all),
        "related_fields:",
        *_yaml_list_lines(semantic.get("related_fields") or []),
        "related_config_objects:",
        *_yaml_list_lines(related_config_objects),
        "related_metadata:",
        *_yaml_list_lines(semantic.get("related_metadata") or []),
        "related_processes:",
        *_yaml_list_lines(related_processes_all),
        "integration_points:",
        *_yaml_list_lines(semantic.get("integration_points") or []),
        "dependencies:",
        *_yaml_list_lines(semantic.get("dependencies") or []),
        "business_rules:",
        *_yaml_list_lines(semantic.get("business_rules") or []),
        "keywords:",
        *_yaml_list_lines(semantic.get("keywords") or []),
        "---",
        "",
        "# Summary",
        "",
        str(semantic.get("summary") or "Draft knowledge note generated from source content; human review is required."),
        "",
        "# Purpose",
        "",
        str(semantic.get("purpose") or "Support AI retrieval and developer review from a controlled source file."),
        "",
        "# Source",
        "",
        f"- Source file: `{source_file}`",
        f"- Source format: `{source_format}`",
        f"- Source checksum: `{source_checksum}`",
        f"- Parse status: `{parse_result.get('parse_status', '')}`",
        f"- Anchor: `{anchor}`",
        f"- Chunk: {part} of {part_count}",
        f"- Imported at: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "# Key Concepts",
        "",
        *_bullet_lines(semantic.get("key_concepts") or []),
        "",
        "# Salesforce References",
        "",
        "## Objects",
        "",
        *_bullet_lines(related_objects_all),
        "",
        "## Fields",
        "",
        *_bullet_lines(semantic.get("related_fields") or []),
        "",
        "## Apex And Metadata",
        "",
        *_fact_bullets(semantic),
        "",
        "# Automation Logic",
        "",
        "## Flow Steps",
        "",
        *_bullet_lines(semantic.get("flow_steps") or []),
        "",
        "## Validation Rules",
        "",
        *_bullet_lines(semantic.get("validation_rules") or []),
        "",
        "# Business Rules",
        "",
        *_bullet_lines(semantic.get("business_rules") or []),
        "",
        "# Integration Points",
        "",
        *_bullet_lines(semantic.get("integration_points") or []),
        "",
        "# Dependencies",
        "",
        *_bullet_lines(semantic.get("dependencies") or []),
        "",
        "# Usage Context",
        "",
        *_bullet_lines(semantic.get("usage_context") or []),
        "",
        "# Search Terms",
        "",
        "## Keywords",
        "",
        *_bullet_lines(semantic.get("keywords") or []),
        "",
        "## Aliases",
        "",
        *_bullet_lines(semantic.get("aliases") or []),
        "",
        "# Extracted Content",
        "",
        "> This section is capped source evidence for review, not reviewed knowledge.",
        "",
        extracted_text or "[No text extracted.]",
        "",
        "# Review Notes",
        "",
        f"- Content checksum: `{_checksum(extracted_text)}`",
        "- Extracted facts are deterministic and require human validation.",
        "- Keep `status: draft` and `confidence: low` until reviewed against source material, schema, config records, tests, or human confirmation.",
        "",
        "# Review Required",
        "",
        "- Confirm all claims against source material and current Salesforce schema/config evidence.",
        "- Keep `status: draft` and `confidence: low` until reviewed.",
        "- Remove or further redact any sensitive values before committing curated notes.",
        "- Add related Salesforce objects, config objects, processes, and open questions.",
        "",
        "# Suggested Manual Curation Checklist",
        "",
        "- [ ] Source file path is correct.",
        "- [ ] Owner is correct.",
        "- [ ] Confidence is justified.",
        "- [ ] Related objects/config/processes are populated where known.",
        "- [ ] No unsupported claims about managed package internals are present.",
        "- [ ] No secrets, credentials, raw data dumps, or uncontrolled exports are present.",
        "",
        "# Parse Warnings",
        "",
    ]
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- None")
    lines.extend(["", "# Open Questions", "", "- What facts from this imported note are confirmed by current schema, config records, tests, or human review?", ""])
    return "\n".join(lines)


def _write_report(batch: str, imported: list[dict[str, Any]], dry_run: bool) -> list[Path]:
    out_dir = Path(".ai/outputs/knowledge-import")
    if dry_run:
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = out_dir / f"{batch or timestamp}.knowledge-import"
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "imported": imported,
    }
    json_path = Path(f"{base}.json")
    md_path = Path(f"{base}.md")
    json_path.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_lines = ["# Knowledge Import Report", "", f"- Generated at: `{report['generated_at']}`", f"- Imported sources: {len(imported)}", ""]
    for item in imported:
        md_lines.extend([
            f"## {item.get('title')}",
            "",
            f"- Source: `{item.get('source')}`",
            f"- Outputs: {', '.join(f'`{path}`' for path in item.get('outputs', []))}",
            f"- Parse status: `{item.get('parse_status')}`",
            f"- Warnings: {', '.join(item.get('warnings', [])) or 'none'}",
            "",
        ])
    md_path.write_text("\n".join(md_lines).rstrip() + "\n", encoding="utf-8")
    return [md_path, json_path]


def _resolve_out_dir(out_dir: Path, domain: str, repo_root: Path) -> Path:
    target = out_dir
    if not target.is_absolute():
        target = repo_root / target
    if target.name == "domains":
        target = target / _slug(domain)
    return target


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:index]
    return line


def _split_key_value(content: str) -> tuple[str, str]:
    if ":" not in content:
        return content.strip(), ""
    key, value = content.split(":", 1)
    return key.strip(), value.strip()


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
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _yaml_list_lines(values: list[str]) -> list[str]:
    return [f"  - {json.dumps(str(value))}" for value in values if str(value).strip()]


def _bullet_lines(values: list[str]) -> list[str]:
    clean = [str(value).strip() for value in values if str(value).strip()]
    return [f"- {value}" for value in clean] if clean else ["- None detected."]


def _fact_bullets(semantic: dict[str, Any]) -> list[str]:
    values = []
    for label, key in [
        ("Apex class/service", "apex_classes"),
        ("Apex method", "apex_methods"),
        ("Apex trigger", "apex_triggers"),
        ("Flow", "flow_names"),
        ("Metadata", "related_metadata"),
    ]:
        for value in semantic.get(key) or []:
            values.append(f"{label}: {value} (`detected`, confidence `low`)")
    return _bullet_lines(values)


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip().lower()).strip("-")
    return slug or "knowledge-note"


def _checksum(text: str) -> str:
    return hashlib.sha256(normalize_whitespace(text).encode("utf-8")).hexdigest()


def _batch_name(manifest: str | None) -> str:
    if manifest:
        return Path(manifest).stem
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


if __name__ == "__main__":
    raise SystemExit(main())
