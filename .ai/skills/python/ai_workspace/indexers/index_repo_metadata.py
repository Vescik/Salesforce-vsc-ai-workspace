"""Index local Salesforce metadata into AI-readable JSON Lines."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable

from ai_workspace.parsers.parse_apex import parse_apex_file
from ai_workspace.parsers.parse_flexipage import parse_flexipage_file
from ai_workspace.parsers.parse_flow import parse_flow_file
from ai_workspace.parsers.parse_layout import parse_layout_file
from ai_workspace.parsers.parse_lwc import parse_lwc_component
from ai_workspace.parsers.parse_permissions import parse_permission_set_file, parse_profile_file
from ai_workspace.utils.io import (
    empty_references,
    ensure_parent_dir,
    is_within,
    read_utf8,
    repo_relative_path,
    warn,
    write_jsonl,
)


SUPPORTED_XML_SUFFIXES = {
    ".field-meta.xml": "CustomField",
    ".flexipage-meta.xml": "FlexiPage",
    ".layout-meta.xml": "Layout",
    ".permissionset-meta.xml": "PermissionSet",
    ".profile-meta.xml": "Profile",
    ".md-meta.xml": "CustomMetadata",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Index local Salesforce metadata for Copilot AI context."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root to scan.")
    parser.add_argument("--out", required=True, help="Output JSONL path.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        print(f"ERROR: repo root does not exist or is not a directory: {repo_root}", file=sys.stderr)
        return 2

    out_path = _resolve_output_path(args.out, repo_root)
    if not is_within(out_path, repo_root):
        print(f"ERROR: output path must be inside repo root: {out_path}", file=sys.stderr)
        return 2

    force_app = repo_root / "force-app"
    if not force_app.exists():
        warn("force-app directory was not found; writing an empty metadata index")
        ensure_parent_dir(out_path)
        out_path.write_text("", encoding="utf-8")
        return 0

    records = build_index(repo_root)
    write_jsonl(out_path, records)
    print(f"Wrote {len(records)} metadata component record(s) to {out_path}")
    return 0


def build_index(repo_root: Path) -> list[dict[str, Any]]:
    """Build metadata component records from repo-root/force-app."""

    force_app = repo_root / "force-app"
    records: list[dict[str, Any]] = []
    claimed_files: set[Path] = set()
    claimed_dirs: set[Path] = set()

    for object_dir in _object_dirs(force_app, repo_root):
        claimed_dirs.add(object_dir)
        records.append(
            _base_record(
                component_type="Object",
                full_name=object_dir.name,
                path=repo_relative_path(object_dir, repo_root),
                summary=f"Salesforce object metadata folder {object_dir.name}.",
                references=_references(objects=[object_dir.name]),
                risk_flags=[],
                parse_status="ok",
            )
        )

    for lwc_dir in _lwc_component_dirs(force_app, repo_root):
        claimed_dirs.add(lwc_dir)
        parsed = parse_lwc_component(lwc_dir, repo_root)
        records.append(_record_from_parse("LWC", lwc_dir, repo_root, parsed))
        for file_path in lwc_dir.rglob("*"):
            if file_path.is_file():
                claimed_files.add(file_path.resolve())

    for file_path in _metadata_files(force_app, repo_root):
        resolved = file_path.resolve()
        if resolved in claimed_files:
            continue

        try:
            record = _record_for_file(file_path, repo_root)
            if record:
                records.append(record)
                claimed_files.add(resolved)
        except Exception as exc:  # noqa: BLE001 - indexer must continue per file.
            warn(f"Could not index {file_path}: {exc}")
            records.append(
                _base_record(
                    component_type="Unknown",
                    full_name=file_path.name,
                    path=repo_relative_path(file_path, repo_root),
                    summary="Metadata component indexing failed for this file.",
                    references=empty_references(),
                    risk_flags=["parse_failed"],
                    parse_status="failed",
                    details={"error": str(exc)},
                )
            )

    records.sort(key=lambda item: (str(item["path"]), str(item["component_type"]), str(item["full_name"])))
    return records


def _record_for_file(file_path: Path, repo_root: Path) -> dict[str, Any] | None:
    parent_name = file_path.parent.name
    name = file_path.name

    if parent_name == "classes" and name.endswith(".cls"):
        parsed = parse_apex_file(file_path)
        return _record_from_parse("ApexClass", file_path, repo_root, parsed)

    if parent_name == "triggers" and name.endswith(".trigger"):
        parsed = parse_apex_file(file_path)
        return _record_from_parse("ApexTrigger", file_path, repo_root, parsed)

    if parent_name == "flows" and name.endswith(".flow-meta.xml"):
        parsed = parse_flow_file(file_path)
        return _record_from_parse("Flow", file_path, repo_root, parsed)

    if parent_name == "fields" and name.endswith(".field-meta.xml"):
        object_name = file_path.parent.parent.name
        field_name = name.removesuffix(".field-meta.xml")
        return _xml_metadata_record(
            file_path=file_path,
            repo_root=repo_root,
            component_type="CustomField",
            full_name=f"{object_name}.{field_name}",
            summary=f"Field metadata {object_name}.{field_name}.",
            references=_references(objects=[object_name], fields=[f"{object_name}.{field_name}"]),
        )

    if parent_name == "flexipages" and name.endswith(".flexipage-meta.xml"):
        parsed = parse_flexipage_file(file_path)
        return _record_from_parse("FlexiPage", file_path, repo_root, parsed)

    if parent_name == "layouts" and name.endswith(".layout-meta.xml"):
        parsed = parse_layout_file(file_path)
        return _record_from_parse("Layout", file_path, repo_root, parsed)

    if parent_name == "permissionsets" and name.endswith(".permissionset-meta.xml"):
        parsed = parse_permission_set_file(file_path)
        return _record_from_parse("PermissionSet", file_path, repo_root, parsed)

    if parent_name == "profiles" and name.endswith(".profile-meta.xml"):
        parsed = parse_profile_file(file_path)
        return _record_from_parse("Profile", file_path, repo_root, parsed)

    if parent_name == "customMetadata" and name.endswith(".md-meta.xml"):
        full_name = name.removesuffix(".md-meta.xml")
        return _xml_metadata_record(
            file_path=file_path,
            repo_root=repo_root,
            component_type="CustomMetadata",
            full_name=full_name,
            summary=f"Custom Metadata record {full_name}.",
            references=_references(custom_metadata=[full_name]),
        )

    if name.endswith("-meta.xml"):
        return _generic_xml_metadata_record(file_path, repo_root)

    return None


def _xml_metadata_record(
    file_path: Path,
    repo_root: Path,
    component_type: str,
    full_name: str,
    summary: str,
    references: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    parse_status = "ok"
    risk_flags: list[str] = []
    details: dict[str, Any] = {}
    try:
        text, used_replacement = read_utf8(file_path)
        if used_replacement:
            parse_status = "partial"
        try:
            root = ET.fromstring(text)
            xml_full_name = _first_xml_text(root, "fullName")
            if xml_full_name:
                details["xml_full_name"] = xml_full_name
        except ET.ParseError as exc:
            warn(f"Could not parse XML metadata {file_path}: {exc}")
            parse_status = "failed"
            risk_flags.append("parse_failed")
            details["error"] = str(exc)
    except OSError as exc:
        warn(f"Could not read XML metadata {file_path}: {exc}")
        parse_status = "failed"
        risk_flags.append("parse_failed")
        details["error"] = str(exc)

    return _base_record(
        component_type=component_type,
        full_name=full_name,
        path=repo_relative_path(file_path, repo_root),
        summary=summary,
        references=references or empty_references(),
        risk_flags=risk_flags,
        parse_status=parse_status,
        details=details,
    )


def _generic_xml_metadata_record(file_path: Path, repo_root: Path) -> dict[str, Any]:
    name = file_path.name
    full_name = name.removesuffix("-meta.xml")
    component_type = _generic_component_type(file_path)
    return _xml_metadata_record(
        file_path=file_path,
        repo_root=repo_root,
        component_type=component_type,
        full_name=full_name,
        summary=f"Generic Salesforce XML metadata component {full_name}.",
    )


def _record_from_parse(
    component_type: str,
    path: Path,
    repo_root: Path,
    parsed: dict[str, Any],
) -> dict[str, Any]:
    return _base_record(
        component_type=component_type,
        full_name=str(parsed.get("full_name") or path.stem),
        path=repo_relative_path(path, repo_root),
        summary=str(parsed.get("summary") or ""),
        references=parsed.get("references") or empty_references(),
        risk_flags=list(parsed.get("risk_flags") or []),
        parse_status=str(parsed.get("parse_status") or "partial"),
        details=parsed.get("details") or {},
    )


def _base_record(
    component_type: str,
    full_name: str,
    path: str,
    summary: str,
    references: dict[str, list[str]],
    risk_flags: list[str],
    parse_status: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "component_type": component_type,
        "full_name": full_name,
        "path": path,
        "source": "repo",
        "summary": summary,
        "references": _normalize_references(references),
        "risk_flags": sorted(set(risk_flags)),
        "parse_status": parse_status,
        "details": details or {},
    }


def _references(
    objects: Iterable[str] = (),
    fields: Iterable[str] = (),
    apex_classes: Iterable[str] = (),
    flows: Iterable[str] = (),
    lwc_components: Iterable[str] = (),
    custom_metadata: Iterable[str] = (),
) -> dict[str, list[str]]:
    refs = empty_references()
    refs["objects"].extend(objects)
    refs["fields"].extend(fields)
    refs["apex_classes"].extend(apex_classes)
    refs["flows"].extend(flows)
    refs["lwc_components"].extend(lwc_components)
    refs["custom_metadata"].extend(custom_metadata)
    return _normalize_references(refs)


def _normalize_references(references: dict[str, list[str]]) -> dict[str, list[str]]:
    normalized = empty_references()
    for key in normalized:
        normalized[key] = sorted(set(value for value in references.get(key, []) if value))
    return normalized


def _metadata_files(force_app: Path, repo_root: Path) -> list[Path]:
    files = []
    for path in force_app.rglob("*"):
        if not path.is_file():
            continue
        if not is_within(path, repo_root):
            warn(f"Skipping file outside repository root: {path}")
            continue
        if _is_metadata_candidate(path):
            files.append(path)
    return sorted(files, key=lambda item: repo_relative_path(item, repo_root))


def _is_metadata_candidate(path: Path) -> bool:
    name = path.name
    return (
        name.endswith(".cls")
        or name.endswith(".trigger")
        or name.endswith("-meta.xml")
    )


def _object_dirs(force_app: Path, repo_root: Path) -> list[Path]:
    dirs = []
    for path in force_app.rglob("objects"):
        if not path.is_dir() or not is_within(path, repo_root):
            continue
        for child in path.iterdir():
            if child.is_dir() and is_within(child, repo_root):
                dirs.append(child)
    return sorted(dirs, key=lambda item: repo_relative_path(item, repo_root))


def _lwc_component_dirs(force_app: Path, repo_root: Path) -> list[Path]:
    dirs = []
    for path in force_app.rglob("lwc"):
        if not path.is_dir() or not is_within(path, repo_root):
            continue
        for child in path.iterdir():
            if child.is_dir() and is_within(child, repo_root):
                dirs.append(child)
    return sorted(dirs, key=lambda item: repo_relative_path(item, repo_root))


def _generic_component_type(path: Path) -> str:
    parent = path.parent.name
    if not parent:
        return "GenericMetadata"
    return "".join(part.capitalize() for part in parent.replace("-", "_").split("_")) or "GenericMetadata"


def _first_xml_text(root: ET.Element, tag_name: str) -> str | None:
    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1] if "}" in element.tag else element.tag
        if local_name == tag_name and element.text:
            return element.text.strip()
    return None


def _resolve_output_path(out_arg: str, repo_root: Path) -> Path:
    out = Path(out_arg)
    if out.is_absolute():
        return out.resolve()
    return (repo_root / out).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
