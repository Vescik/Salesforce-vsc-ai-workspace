"""Import local source documents into curated draft knowledge notes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_workspace.knowledge.parse_documents import chunk_text, extract_text, normalize_whitespace


DEFAULT_OWNER = "Salesforce Platform Team"
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SECRET_HINT_RE = re.compile(
    r"(?i)(api[_-]?key|client[_-]?secret|password|passwd|token|bearer\s+[A-Za-z0-9._~+/=-]{12,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import local documents into draft knowledge notes.")
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
    related_objects: list[str] | None = None,
    related_config_objects: list[str] | None = None,
    related_processes: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Import one source file into one or more markdown notes."""

    source = source.resolve()
    result = extract_text(source, max_chars=max_chars)
    text = str(result.get("text") or "")
    sensitive_warnings = detect_sensitive_content(text)
    redacted_text = redact_sensitive_content(text)
    chunks = chunk_text(redacted_text, max_chars=chunk_size, overlap=500) or [""]
    target_dir = _resolve_out_dir(out_dir, domain, repo_root)
    source_rel = _repo_relative(source, repo_root)
    slug = _slug(title)
    outputs: list[str] = []
    records: list[dict[str, Any]] = []

    for index, part in enumerate(chunks, start=1):
        suffix = "" if len(chunks) == 1 else f".part-{index:03d}"
        target = target_dir / f"{slug}{suffix}.md"
        if target.exists() and not overwrite and not dry_run:
            raise FileExistsError(f"Knowledge note already exists: {target}")
        note_text = _knowledge_note(
            title=title if len(chunks) == 1 else f"{title} (Part {index})",
            domain=domain,
            source_file=source_rel,
            owner=owner,
            status=status,
            confidence=confidence,
            tags=tags or [],
            related_objects=related_objects or [],
            related_config_objects=related_config_objects or [],
            related_processes=related_processes or [],
            extracted_text=part,
            parse_result=result,
            sensitive_warnings=sensitive_warnings,
            part=index,
            part_count=len(chunks),
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
                "warnings": list(result.get("warnings") or []) + sensitive_warnings,
                "dry_run": dry_run,
            }
        )

    if records:
        records[0]["outputs"] = outputs
    return records[:1]


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
                related_objects=[str(value) for value in item.get("related_objects", [])],
                related_config_objects=[str(value) for value in item.get("related_config_objects", [])],
                related_processes=[str(value) for value in item.get("related_processes", [])],
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
    owner: str,
    status: str,
    confidence: str,
    tags: list[str],
    related_objects: list[str],
    related_config_objects: list[str],
    related_processes: list[str],
    extracted_text: str,
    parse_result: dict[str, Any],
    sensitive_warnings: list[str],
    part: int,
    part_count: int,
) -> str:
    now = datetime.now(timezone.utc).date().isoformat()
    keywords = sorted(set(tags + [domain, "managed-package"]))
    warnings = list(parse_result.get("warnings") or []) + sensitive_warnings
    lines = [
        "---",
        f"title: {json.dumps(title)}",
        f"domain: {json.dumps(domain)}",
        'source_type: "internal_knowledge"',
        f"source_file: {json.dumps(source_file)}",
        f"owner: {json.dumps(owner)}",
        f"status: {json.dumps(status)}",
        f"confidence: {json.dumps(confidence)}",
        f"last_reviewed: {json.dumps(now)}",
        "applies_to:",
        '  - "KimbleOne/Kantata"',
        "related_objects:",
        *_yaml_list_lines(related_objects),
        "related_config_objects:",
        *_yaml_list_lines(related_config_objects),
        "related_processes:",
        *_yaml_list_lines(related_processes),
        "keywords:",
        *_yaml_list_lines(keywords),
        "---",
        "",
        "# Summary",
        "",
        "Deterministic import from source document. This is not a semantic summary and requires human review.",
        "",
        "# Extracted Content",
        "",
        extracted_text or "[No text extracted.]",
        "",
        "# Import Metadata",
        "",
        f"- Source file: `{source_file}`",
        f"- Source format: `{parse_result.get('source_format', '')}`",
        f"- Parse status: `{parse_result.get('parse_status', '')}`",
        f"- Chunk: {part} of {part_count}",
        f"- Content checksum: `{_checksum(extracted_text)}`",
        f"- Imported at: `{datetime.now(timezone.utc).isoformat()}`",
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
    return [f"  - {json.dumps(value)}" for value in values] if values else ["  - \"\""]


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
