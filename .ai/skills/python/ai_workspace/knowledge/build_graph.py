"""Build a cross-reference graph from local knowledge + metadata + work items.

Inputs (each is optional; missing inputs reduce the graph but do not fail)::

    .ai/context/index/knowledge-cards.jsonl
    .ai/context/index/metadata-knowledge-cards.jsonl
    .ai/context/index/sobject-cards.jsonl
    .ai/context/index/field-cards.jsonl
    .ai/context/index/config-record-cards.jsonl
    .ai/context/work-items/*/ado-work-item.json
    .ai/context/work-items/*/relevant-knowledge.yaml

Output (local-only, never synced upstream)::

    .ai/context/index/knowledge-graph.json

Edges per node are capped at 200; nodes whose neighborhoods would exceed the cap
are recorded in ``telemetry.overflow_nodes`` so the cap can be revisited.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from ai_workspace.security.redactor import load_simple_yaml
from ai_workspace.utils.io import ensure_parent_dir


ADJACENCY_CAP = 200


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the knowledge cross-reference graph.")
    parser.add_argument("--knowledge-root", default=".ai/knowledge")
    parser.add_argument("--index-dir", default=".ai/context/index")
    parser.add_argument("--work-items-dir", default=".ai/context/work-items")
    parser.add_argument("--out", default=".ai/context/index/knowledge-graph.json")
    parser.add_argument("--adjacency-cap", type=int, default=ADJACENCY_CAP)
    args = parser.parse_args(argv)

    knowledge_root = Path(args.knowledge_root)
    index_dir = Path(args.index_dir)
    work_items_dir = Path(args.work_items_dir)
    out_path = Path(args.out)

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []

    note_cards = _read_jsonl(index_dir / "knowledge-cards.jsonl")
    metadata_cards = _read_jsonl(index_dir / "metadata-knowledge-cards.jsonl")
    sobject_cards = _read_jsonl(index_dir / "sobject-cards.jsonl")
    field_cards = _read_jsonl(index_dir / "field-cards.jsonl")

    _add_note_nodes(nodes, note_cards)
    _add_metadata_nodes(nodes, metadata_cards)
    _add_object_nodes(nodes, sobject_cards, note_cards, metadata_cards)
    _add_field_nodes(nodes, field_cards)
    _add_process_nodes(nodes, knowledge_root)
    _add_adr_nodes(nodes, note_cards)
    _add_work_item_nodes(nodes, work_items_dir)

    _add_note_edges(edges, note_cards)
    _add_metadata_edges(edges, metadata_cards)
    _add_adr_edges(edges, note_cards)
    _add_work_item_edges(edges, work_items_dir)

    capped_edges, overflow = _cap_adjacency(edges, args.adjacency_cap)
    graph = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "node_count": len(nodes),
        "edge_count": len(capped_edges),
        "nodes": sorted(nodes.values(), key=lambda n: (n["type"], n["id"])),
        "edges": sorted(capped_edges, key=lambda e: (e["type"], e["source"], e["target"])),
        "telemetry": {
            "adjacency_cap": args.adjacency_cap,
            "overflow_nodes": sorted(overflow),
            "by_node_type": _count_by(nodes.values(), "type"),
            "by_edge_type": _count_by(capped_edges, "type"),
        },
    }
    ensure_parent_dir(out_path)
    out_path.write_text(json.dumps(graph, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Wrote knowledge graph to {out_path}")
    print(f"Nodes: {len(nodes)}, edges: {len(capped_edges)} (overflow nodes: {len(overflow)})")
    return 0


# ---------- node construction ----------


def _add_note_nodes(nodes: dict[str, dict[str, Any]], note_cards: list[dict[str, Any]]) -> None:
    for card in note_cards:
        slug = _slug_from_path(card.get("path"), fallback=str(card.get("title") or ""))
        if not slug:
            continue
        node_id = f"note:{slug}"
        nodes.setdefault(node_id, {
            "id": node_id,
            "type": "note",
            "label": str(card.get("title") or slug),
            "domain": str(card.get("domain") or ""),
            "path": str(card.get("path") or ""),
            "status": str(card.get("status") or ""),
            "confidence": str(card.get("confidence") or ""),
        })


def _add_metadata_nodes(nodes: dict[str, dict[str, Any]], metadata_cards: list[dict[str, Any]]) -> None:
    for card in metadata_cards:
        api_name = str(card.get("api_name") or "")
        metadata_type = str(card.get("metadata_type") or "metadata")
        if not api_name:
            continue
        node_id = f"metadata_component:{metadata_type}:{api_name}"
        nodes.setdefault(node_id, {
            "id": node_id,
            "type": "metadata_component",
            "metadata_type": metadata_type,
            "label": api_name,
            "path": str(card.get("path") or ""),
        })


def _add_object_nodes(
    nodes: dict[str, dict[str, Any]],
    sobject_cards: list[dict[str, Any]],
    note_cards: list[dict[str, Any]],
    metadata_cards: list[dict[str, Any]],
) -> None:
    seen: set[str] = set()
    for card in sobject_cards:
        api = str(card.get("api_name") or "")
        if not api:
            continue
        seen.add(api)
        node_id = f"object:{api}"
        nodes.setdefault(node_id, {
            "id": node_id,
            "type": "object",
            "label": api,
            "namespace": str(card.get("namespace") or ""),
        })
    # Synthesize stub object nodes for objects referenced by notes / metadata when the schema index is empty.
    referenced: set[str] = set()
    for card in note_cards:
        for value in card.get("related_objects") or []:
            if str(value).strip():
                referenced.add(str(value).strip())
    for card in metadata_cards:
        for value in (card.get("references") or {}).get("objects", []):
            if str(value).strip():
                referenced.add(str(value).strip())
    for api in referenced - seen:
        node_id = f"object:{api}"
        nodes.setdefault(node_id, {
            "id": node_id,
            "type": "object",
            "label": api,
            "namespace": "",
            "source": "referenced_only",
        })


def _add_field_nodes(nodes: dict[str, dict[str, Any]], field_cards: list[dict[str, Any]]) -> None:
    for card in field_cards:
        api_obj = str(card.get("object_api_name") or "")
        api_field = str(card.get("field_api_name") or "")
        if not api_obj or not api_field:
            continue
        node_id = f"field:{api_obj}.{api_field}"
        nodes.setdefault(node_id, {
            "id": node_id,
            "type": "field",
            "label": f"{api_obj}.{api_field}",
            "data_type": str(card.get("data_type") or ""),
        })


def _add_process_nodes(nodes: dict[str, dict[str, Any]], knowledge_root: Path) -> None:
    process_dir = knowledge_root / "process-maps"
    if not process_dir.exists():
        return
    for path in sorted(process_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        slug = path.stem.lower()
        node_id = f"process:{slug}"
        nodes.setdefault(node_id, {
            "id": node_id,
            "type": "process",
            "label": path.stem.replace("-", " ").title(),
            "path": _display_path(path),
        })


def _add_adr_nodes(nodes: dict[str, dict[str, Any]], note_cards: list[dict[str, Any]]) -> None:
    for card in note_cards:
        if str(card.get("source_type") or "").lower() != "decision":
            continue
        slug = _slug_from_path(card.get("path"), fallback=str(card.get("title") or ""))
        if not slug:
            continue
        node_id = f"adr:{slug}"
        nodes.setdefault(node_id, {
            "id": node_id,
            "type": "adr",
            "label": str(card.get("title") or slug),
            "path": str(card.get("path") or ""),
            "status": str(card.get("status") or ""),
        })


def _add_work_item_nodes(nodes: dict[str, dict[str, Any]], work_items_dir: Path) -> None:
    if not work_items_dir.exists():
        return
    for wi_dir in sorted(work_items_dir.iterdir()):
        if not wi_dir.is_dir():
            continue
        ado_path = wi_dir / "ado-work-item.json"
        if not ado_path.exists():
            continue
        try:
            payload = json.loads(ado_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        wi_id = wi_dir.name
        node_id = f"work_item:{wi_id}"
        nodes.setdefault(node_id, {
            "id": node_id,
            "type": "work_item",
            "label": str(payload.get("title") or wi_id),
            "path": _display_path(wi_dir),
        })


# ---------- edge construction ----------


def _add_note_edges(edges: list[dict[str, str]], note_cards: list[dict[str, Any]]) -> None:
    for card in note_cards:
        note_slug = _slug_from_path(card.get("path"), fallback=str(card.get("title") or ""))
        if not note_slug:
            continue
        source_id = f"note:{note_slug}"
        for value in card.get("related_objects") or []:
            value = str(value).strip()
            if value:
                edges.append({"source": source_id, "target": f"object:{value}", "type": "mentions"})
        for value in card.get("related_processes") or []:
            slug = _slug(str(value))
            if slug:
                edges.append({"source": source_id, "target": f"process:{slug}", "type": "mentions"})
        source_file = str(card.get("source_file") or "").strip()
        if source_file:
            edges.append({"source": source_id, "target": f"file:{source_file}", "type": "derived_from"})


def _add_metadata_edges(edges: list[dict[str, str]], metadata_cards: list[dict[str, Any]]) -> None:
    for card in metadata_cards:
        api_name = str(card.get("api_name") or "")
        metadata_type = str(card.get("metadata_type") or "metadata")
        if not api_name:
            continue
        source_id = f"metadata_component:{metadata_type}:{api_name}"
        refs = card.get("references") or {}
        for value in refs.get("objects", []):
            value = str(value).strip()
            if value:
                edges.append({"source": source_id, "target": f"object:{value}", "type": "impacts"})
        for value in refs.get("fields", []):
            value = str(value).strip()
            if value and "." in value:
                edges.append({"source": source_id, "target": f"field:{value}", "type": "impacts"})


def _add_adr_edges(edges: list[dict[str, str]], note_cards: list[dict[str, Any]]) -> None:
    # Notes in the same domain as an ADR get a `decided_by` edge to that ADR.
    adrs_by_domain: dict[str, list[str]] = {}
    for card in note_cards:
        if str(card.get("source_type") or "").lower() != "decision":
            continue
        slug = _slug_from_path(card.get("path"), fallback=str(card.get("title") or ""))
        if slug:
            adrs_by_domain.setdefault(str(card.get("domain") or "general"), []).append(slug)
    for card in note_cards:
        if str(card.get("source_type") or "").lower() == "decision":
            continue
        domain = str(card.get("domain") or "general")
        note_slug = _slug_from_path(card.get("path"), fallback=str(card.get("title") or ""))
        if not note_slug:
            continue
        for adr_slug in adrs_by_domain.get(domain, []):
            edges.append({"source": f"note:{note_slug}", "target": f"adr:{adr_slug}", "type": "decided_by"})


def _add_work_item_edges(edges: list[dict[str, str]], work_items_dir: Path) -> None:
    if not work_items_dir.exists():
        return
    for wi_dir in sorted(work_items_dir.iterdir()):
        if not wi_dir.is_dir():
            continue
        ado_path = wi_dir / "ado-work-item.json"
        if not ado_path.exists():
            continue
        wi_id = wi_dir.name
        source_id = f"work_item:{wi_id}"
        rk_path = wi_dir / "relevant-knowledge.yaml"
        if rk_path.exists():
            try:
                payload = load_simple_yaml(str(rk_path))
            except Exception:  # noqa: BLE001
                payload = None
            if isinstance(payload, dict):
                entries = payload.get("knowledge") if isinstance(payload.get("knowledge"), list) else []
                for entry in entries or []:
                    if not isinstance(entry, dict):
                        continue
                    slug = _slug_from_path(entry.get("path"), fallback=str(entry.get("title") or ""))
                    if slug:
                        edges.append({"source": source_id, "target": f"note:{slug}", "type": "cites"})


# ---------- helpers ----------


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                loaded = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(loaded, dict):
                records.append(loaded)
    return records


def _cap_adjacency(edges: list[dict[str, str]], cap: int) -> tuple[list[dict[str, str]], set[str]]:
    """Cap outgoing edges per node and record which nodes overflowed."""

    seen_edges: set[tuple[str, str, str]] = set()
    out_counts: dict[str, int] = {}
    overflow: set[str] = set()
    capped: list[dict[str, str]] = []
    for edge in edges:
        key = (edge["source"], edge["target"], edge["type"])
        if key in seen_edges:
            continue
        seen_edges.add(key)
        count = out_counts.get(edge["source"], 0)
        if count >= cap:
            overflow.add(edge["source"])
            continue
        out_counts[edge["source"]] = count + 1
        capped.append(edge)
    return capped, overflow


def _count_by(items: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _slug_from_path(path_value: Any, fallback: str = "") -> str:
    if isinstance(path_value, str) and path_value.strip():
        return Path(path_value).stem.lower()
    return _slug(fallback)


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip().lower()).strip("-")


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except (FileNotFoundError, ValueError):
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
