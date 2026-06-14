"""Minimal read-only MCP server for local Salesforce AI context.

This module intentionally avoids external dependencies. It implements the small
JSON-RPC-over-stdio subset needed for MCP clients to list and call tools:
``initialize``, ``tools/list``, and ``tools/call``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from ai_workspace.search.simple_search import search_jsonl


MAX_CONTENT_CHARS = 50_000
WORK_ITEM_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
OBJECT_API_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

ALLOWED_ROOTS = (
    ".ai/context",
    ".ai/knowledge",
    ".ai/outputs",
    "specs",
    "docs",
    "config/data-promotion",
    "config/kimbleone-packs",
)

INDEX_FILES = {
    "metadata": "metadata-components.jsonl",
    "sobjects": "sobject-cards.jsonl",
    "fields": "field-cards.jsonl",
    "relationships": "relationship-cards.jsonl",
    "config_records": "config-record-cards.jsonl",
    "knowledge": "knowledge-cards.jsonl",
}


class SalesforceContextServer:
    """Read-only local context tool implementation."""

    def __init__(self, repo_root: Path, index_dir: Path, context_root: Path, debug: bool = False) -> None:
        self.repo_root = repo_root.resolve()
        self.index_dir = self._resolve_allowed(index_dir)
        self.context_root = self._resolve_allowed(context_root)
        self.debug = debug

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "search_context":
            return self.search_context(str(arguments.get("query", "")), _int_arg(arguments, "top_k", 10))
        if name == "get_work_item_context":
            return self.get_work_item_context(str(arguments.get("work_item_id", "")))
        if name == "get_object_card":
            return self.get_object_card(str(arguments.get("object_api_name", "")))
        if name == "get_related_metadata":
            return self.get_related_metadata(str(arguments.get("query", "")), _int_arg(arguments, "top_k", 10))
        if name == "get_related_config_records":
            return self.get_related_config_records(str(arguments.get("query", "")), _int_arg(arguments, "top_k", 10))
        if name == "get_related_knowledge":
            return self.get_related_knowledge(str(arguments.get("query", "")), _int_arg(arguments, "top_k", 10))
        if name == "get_knowledge_note":
            return self.get_knowledge_note(str(arguments.get("path", "")))
        if name == "get_solution_design":
            return self.get_solution_design(str(arguments.get("work_item_id", "")))
        if name == "get_config_impact":
            return self.get_config_impact(str(arguments.get("work_item_id", "")))
        if name == "list_knowledge_domain":
            return self.list_knowledge_domain(
                str(arguments.get("domain", "")),
                _int_arg(arguments, "limit", 50),
            )
        if name == "rebuild_knowledge_index":
            return self.rebuild_knowledge_index()
        if name == "build_context_pack":
            return self.build_context_pack(
                str(arguments.get("work_item_id", "")),
                str(arguments.get("query", "")),
            )
        if name == "knowledge_search":
            return self.knowledge_search(
                str(arguments.get("query", "")),
                str(arguments.get("domain") or "") or None,
                str(arguments.get("related_object") or "") or None,
                _int_arg(arguments, "k", 10),
            )
        if name == "knowledge_graph_neighbors":
            return self.knowledge_graph_neighbors(
                str(arguments.get("node_id", "")),
                _int_arg(arguments, "depth", 1),
            )
        if name == "knowledge_get":
            return self.knowledge_get(str(arguments.get("slug", "")))
        raise ValueError(f"Unknown tool: {name}")

    def search_context(self, query: str, top_k: int = 10) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        for source_type, filename in INDEX_FILES.items():
            path = self._index_file(filename)
            if not path.exists():
                continue
            for record in search_jsonl(str(path), query, max(top_k, 1)):
                results.append(_concise_record(source_type, record))
        results.sort(key=lambda item: (-float(item.get("score", 0)), str(item.get("name") or item.get("record_key") or item.get("path") or "")))
        return {
            "query": query,
            "results": results[: max(top_k, 1)],
            "warnings": [] if results else ["No matching local context records were found."],
        }

    def get_work_item_context(self, work_item_id: str) -> dict[str, Any]:
        self._validate_work_item(work_item_id)
        base = self._safe_path(f".ai/context/work-items/{work_item_id}")
        files = [
            "work-item-summary.md",
            "acceptance-criteria.md",
            "context-pack.md",
            "relevant-metadata.yaml",
            "relevant-schema.yaml",
            "relevant-config-records.yaml",
            "relevant-knowledge.yaml",
            "config-impact.yaml",
        ]
        content: dict[str, Any] = {}
        warnings: list[str] = []
        for filename in files:
            path = base / filename
            if path.exists() and path.is_file():
                content[filename] = _read_limited(path, self.repo_root)
            else:
                warnings.append(f"Missing Work Item context file: {path.relative_to(self.repo_root).as_posix()}")
        return {"work_item_id": work_item_id, "content": content, "warnings": warnings}

    def get_object_card(self, object_api_name: str) -> dict[str, Any]:
        if not OBJECT_API_RE.fullmatch(object_api_name):
            raise ValueError("object_api_name must be a Salesforce API name")
        object_card = None
        for record in _read_jsonl(self._index_file(INDEX_FILES["sobjects"])):
            if str(record.get("api_name") or "") == object_api_name:
                object_card = _concise_record("sobjects", record)
                break
        fields = [
            _concise_record("fields", record)
            for record in _read_jsonl(self._index_file(INDEX_FILES["fields"]))
            if str(record.get("object_api_name") or "") == object_api_name
        ]
        relationships = []
        for record in _read_jsonl(self._index_file(INDEX_FILES["relationships"])):
            to_objects = record.get("to_objects") if isinstance(record.get("to_objects"), list) else []
            if str(record.get("from_object") or "") == object_api_name or object_api_name in [str(item) for item in to_objects]:
                relationships.append(_concise_record("relationships", record))
        return {
            "object_api_name": object_api_name,
            "object_card": object_card,
            "fields": fields[:100],
            "relationships": relationships[:100],
            "warnings": [] if object_card else [f"No exact object card found for {object_api_name}."],
        }

    def get_related_metadata(self, query: str, top_k: int = 10) -> dict[str, Any]:
        path = self._index_file(INDEX_FILES["metadata"])
        records = [_concise_record("metadata", record) for record in search_jsonl(str(path), query, max(top_k, 1))] if path.exists() else []
        return {"query": query, "results": records, "warnings": [] if path.exists() else [f"Missing metadata index: {path.as_posix()}"]}

    def get_related_config_records(self, query: str, top_k: int = 10) -> dict[str, Any]:
        path = self._index_file(INDEX_FILES["config_records"])
        records = [_concise_record("config_records", record) for record in search_jsonl(str(path), query, max(top_k, 1))] if path.exists() else []
        return {"query": query, "results": records, "warnings": [] if path.exists() else [f"Missing config record index: {path.as_posix()}"]}

    def get_related_knowledge(self, query: str, top_k: int = 10) -> dict[str, Any]:
        path = self._index_file(INDEX_FILES["knowledge"])
        records = [_concise_record("knowledge", record) for record in search_jsonl(str(path), query, max(top_k, 1))] if path.exists() else []
        return {"query": query, "results": records, "warnings": [] if path.exists() else [f"Missing knowledge index: {path.as_posix()}"]}

    def get_knowledge_note(self, path: str) -> dict[str, Any]:
        if not path or "\x00" in path:
            raise ValueError("path is required")
        note_path = safe_path_join(self.repo_root, path, (".ai/knowledge",))
        if not note_path.exists() or not note_path.is_file():
            raise ValueError(f"Knowledge note not found: {path}")
        if note_path.suffix.lower() != ".md":
            raise ValueError("Only markdown knowledge notes can be read")
        relative = note_path.relative_to(self.repo_root)
        if "imports" in relative.parts or "archive" in relative.parts:
            raise ValueError("Raw imports and archived knowledge files are not exposed through MCP")
        return {
            "path": relative.as_posix(),
            "content": _read_limited(note_path, self.repo_root, limit=MAX_CONTENT_CHARS),
            "warnings": [],
        }

    def rebuild_knowledge_index(self) -> dict[str, Any]:
        from ai_workspace.knowledge.index_knowledge import build_knowledge_index
        from ai_workspace.utils.io import write_jsonl
        knowledge_root = (self.repo_root / ".ai" / "knowledge").resolve()
        out_path = self._index_file(INDEX_FILES["knowledge"])
        records = build_knowledge_index(knowledge_root)
        write_jsonl(out_path, records)
        return {
            "indexed_cards": len(records),
            "out": out_path.relative_to(self.repo_root).as_posix(),
            "warnings": [] if records else ["No knowledge notes found under .ai/knowledge/"],
        }

    def build_context_pack(self, work_item_id: str, query: str) -> dict[str, Any]:
        self._validate_work_item(work_item_id)
        if not query or not query.strip():
            raise ValueError("query is required")
        from ai_workspace.indexers.build_context_pack import main as build_main
        work_item_dir = safe_path_join(
            self.repo_root,
            f".ai/context/work-items/{work_item_id}",
            (".ai/context",),
        )
        work_item_dir.mkdir(parents=True, exist_ok=True)
        build_main([
            "--work-item", work_item_id,
            "--query", query,
            "--index-dir", self.index_dir.as_posix(),
            "--work-item-dir", work_item_dir.as_posix(),
        ])
        out_path = work_item_dir / "context-pack.md"
        return {
            "work_item_id": work_item_id,
            "context_pack_path": out_path.relative_to(self.repo_root).as_posix(),
            "exists": out_path.exists(),
            "warnings": [],
        }

    def list_knowledge_domain(self, domain: str, limit: int = 50) -> dict[str, Any]:
        if not domain or "\x00" in domain:
            raise ValueError("domain is required")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", domain):
            raise ValueError("domain must contain only letters, digits, hyphens, and underscores")
        path = self._index_file(INDEX_FILES["knowledge"])
        records = []
        for record in _read_jsonl(path):
            if str(record.get("domain") or "").lower() == domain.lower():
                records.append(_concise_record("knowledge", record))
            if len(records) >= limit:
                break
        return {
            "domain": domain,
            "count": len(records),
            "records": records,
            "warnings": [] if path.exists() else [f"Missing knowledge index: {path.as_posix()}"],
        }

    def get_solution_design(self, work_item_id: str) -> dict[str, Any]:
        self._validate_work_item(work_item_id)
        candidates = [
            self._safe_path(f"specs/approved/{work_item_id}.solution-design.md"),
            self._safe_path(f"specs/proposed/{work_item_id}.solution-design.md"),
        ]
        for path in candidates:
            if path.exists() and path.is_file():
                return {
                    "work_item_id": work_item_id,
                    "path": path.relative_to(self.repo_root).as_posix(),
                    "content": _read_limited(path, self.repo_root),
                    "warnings": [],
                }
        return {
            "work_item_id": work_item_id,
            "content": "",
            "warnings": [f"No approved or proposed solution design found for {work_item_id}."],
        }

    def knowledge_search(
        self,
        query: str,
        domain: str | None,
        related_object: str | None,
        k: int,
    ) -> dict[str, Any]:
        """BM25-ranked search over the knowledge index with optional filters."""

        if not query or not query.strip():
            raise ValueError("query is required")
        if domain is not None and not re.fullmatch(r"[A-Za-z0-9_-]+", domain):
            raise ValueError("domain must contain only letters, digits, hyphens, and underscores")
        if related_object is not None and not OBJECT_API_RE.fullmatch(related_object):
            raise ValueError("related_object must be a Salesforce API name")
        path = self._index_file(INDEX_FILES["knowledge"])
        if not path.exists():
            return {"query": query, "results": [], "warnings": [f"Missing knowledge index: {path.as_posix()}"]}
        # Over-fetch then filter; BM25 over the full corpus + post-filter keeps relevance accurate.
        raw = search_jsonl(str(path), query, max(k * 4, k), mode="bm25")
        filtered: list[dict[str, Any]] = []
        for record in raw:
            if domain and str(record.get("domain") or "").lower() != domain.lower():
                continue
            if related_object:
                related = [str(item) for item in (record.get("related_objects") or [])]
                if related_object not in related:
                    continue
            filtered.append(_concise_record("knowledge", record))
            if len(filtered) >= k:
                break
        return {
            "query": query,
            "domain": domain,
            "related_object": related_object,
            "results": filtered,
            "warnings": [] if filtered else ["No matching knowledge records under the given filters."],
        }

    def knowledge_graph_neighbors(self, node_id: str, depth: int) -> dict[str, Any]:
        """BFS through the knowledge graph from ``node_id`` up to ``depth`` (cap 3)."""

        if not node_id or "\x00" in node_id:
            raise ValueError("node_id is required")
        if not re.fullmatch(r"[A-Za-z0-9_:.\\-]+", node_id):
            raise ValueError("node_id contains unsupported characters")
        depth = max(1, min(int(depth or 1), 3))
        graph_path = self._index_file("knowledge-graph.json")
        if not graph_path.exists():
            return {"node_id": node_id, "warnings": [f"Missing knowledge graph: {graph_path.as_posix()}"]}
        try:
            graph = json.loads(graph_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return {"node_id": node_id, "warnings": [f"Could not read graph: {exc}"]}
        nodes_by_id = {str(n.get("id")): n for n in graph.get("nodes") or []}
        if node_id not in nodes_by_id:
            return {"node_id": node_id, "warnings": [f"Node not found in graph: {node_id}"]}
        adjacency: dict[str, list[dict[str, str]]] = {}
        for edge in graph.get("edges") or []:
            adjacency.setdefault(str(edge.get("source")), []).append(dict(edge))
            adjacency.setdefault(str(edge.get("target")), []).append({
                "source": str(edge.get("target")),
                "target": str(edge.get("source")),
                "type": str(edge.get("type")) + "_inverse",
            })

        frontier = {node_id}
        visited = {node_id}
        collected_edges: list[dict[str, str]] = []
        for _ in range(depth):
            next_frontier: set[str] = set()
            for current in frontier:
                for edge in adjacency.get(current, []):
                    collected_edges.append(edge)
                    target = edge["target"]
                    if target not in visited and target in nodes_by_id:
                        visited.add(target)
                        next_frontier.add(target)
            frontier = next_frontier
            if not frontier:
                break

        return {
            "node_id": node_id,
            "depth": depth,
            "nodes": [nodes_by_id[n] for n in sorted(visited)],
            "edges": collected_edges,
            "warnings": [],
        }

    def knowledge_get(self, slug: str) -> dict[str, Any]:
        """Resolve a knowledge note by slug via the index YAML and read its content."""

        if not slug or "\x00" in slug:
            raise ValueError("slug is required")
        if not re.fullmatch(r"[A-Za-z0-9_.\\-]+", slug):
            raise ValueError("slug contains unsupported characters")
        path = self._resolve_slug(slug)
        if path is None:
            return {"slug": slug, "warnings": [f"Slug not found in index: {slug}"]}
        return self.get_knowledge_note(path)

    def _resolve_slug(self, slug: str) -> str | None:
        index_yaml = self._index_file("knowledge-index-files.yaml")
        if not index_yaml.exists():
            return None
        # The simple YAML loader does not support inline mappings in lists, which is
        # the shape emitted by index_knowledge --emit-index-yaml. Parse with a
        # targeted regex scan instead — the format is machine-generated and stable.
        try:
            text = index_yaml.read_text(encoding="utf-8")
        except OSError:
            return None
        pattern = re.compile(r"^\s*-\s+slug:\s+\"([^\"]+)\"\s*$", re.MULTILINE)
        path_pattern = re.compile(r"^\s+path:\s+\"([^\"]+)\"\s*$", re.MULTILINE)
        for match in pattern.finditer(text):
            if match.group(1) != slug:
                continue
            tail = text[match.end():]
            path_match = path_pattern.search(tail.split("\n      - slug:")[0])
            if path_match:
                return path_match.group(1)
        return None

    def get_config_impact(self, work_item_id: str) -> dict[str, Any]:
        self._validate_work_item(work_item_id)
        paths = [
            self._safe_path(f".ai/context/work-items/{work_item_id}/config-impact.yaml"),
            self._safe_path(f".ai/outputs/config-impact/{work_item_id}.config-impact.md"),
        ]
        content: dict[str, Any] = {}
        warnings: list[str] = []
        for path in paths:
            key = path.relative_to(self.repo_root).as_posix()
            if path.exists() and path.is_file():
                content[key] = _read_limited(path, self.repo_root)
            else:
                warnings.append(f"Missing config impact artifact: {key}")
        return {"work_item_id": work_item_id, "content": content, "warnings": warnings}

    def _index_file(self, filename: str) -> Path:
        path = (self.index_dir / filename).resolve()
        path.relative_to(self.index_dir)
        return path

    def _safe_path(self, relative_path: str) -> Path:
        return safe_path_join(self.repo_root, relative_path, ALLOWED_ROOTS)

    def _resolve_allowed(self, path: Path) -> Path:
        candidate = path if path.is_absolute() else self.repo_root / path
        candidate = candidate.resolve()
        candidate.relative_to(self.repo_root)
        if not any(_is_relative_to(candidate, (self.repo_root / root).resolve()) for root in ALLOWED_ROOTS):
            raise ValueError(f"Path is outside allowed MCP roots: {path}")
        return candidate

    @staticmethod
    def _validate_work_item(work_item_id: str) -> None:
        if not WORK_ITEM_RE.fullmatch(work_item_id):
            raise ValueError("work_item_id contains unsupported characters")


def safe_path_join(repo_root: Path, relative_path: str, allowed_roots: tuple[str, ...]) -> Path:
    """Resolve a relative path and ensure it stays under approved local roots."""

    root = repo_root.resolve()
    candidate = (root / relative_path).resolve()
    candidate.relative_to(root)
    allowed = [(root / allowed_root).resolve() for allowed_root in allowed_roots]
    if not any(_is_relative_to(candidate, allowed_root) for allowed_root in allowed):
        raise ValueError(f"Path is outside allowed roots: {relative_path}")
    return candidate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only local Salesforce context MCP server.")
    parser.add_argument("--index-dir", default=".ai/context/index")
    parser.add_argument("--context-root", default=".ai/context")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)

    server = SalesforceContextServer(
        repo_root=Path(args.repo_root),
        index_dir=Path(args.index_dir),
        context_root=Path(args.context_root),
        debug=args.debug,
    )
    return run_json_rpc(server)


def run_json_rpc(server: SalesforceContextServer) -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(server, request)
        except Exception as exc:  # noqa: BLE001 - server must always reply JSON.
            response = _error_response(None, -32603, str(exc))
        if response is not None:
            print(json.dumps(response, ensure_ascii=True, sort_keys=True), flush=True)
    return 0


def handle_request(server: SalesforceContextServer, request: dict[str, Any]) -> dict[str, Any] | None:
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}
    if method == "initialize":
        return _result_response(
            request_id,
            {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "salesforce-context", "version": "0.1.0"},
                "capabilities": {"tools": {}},
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return _result_response(request_id, {"tools": _tool_definitions()})
    if method == "tools/call":
        name = str(params.get("name") or "")
        arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        try:
            result = server.call_tool(name, arguments)
            return _result_response(
                request_id,
                {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True)}]},
            )
        except Exception as exc:  # noqa: BLE001
            return _result_response(
                request_id,
                {
                    "isError": True,
                    "content": [{"type": "text", "text": str(exc)}],
                },
            )
    return _error_response(request_id, -32601, f"Method not found: {method}")


def _tool_definitions() -> list[dict[str, Any]]:
    return [
        _tool("search_context", "Search all local Salesforce context indexes.", {"query": "string", "top_k": "integer"}, ["query"]),
        _tool("get_work_item_context", "Read local Work Item context artifacts.", {"work_item_id": "string"}, ["work_item_id"]),
        _tool("get_object_card", "Read an object schema card with related fields and relationships.", {"object_api_name": "string"}, ["object_api_name"]),
        _tool("get_related_metadata", "Search local metadata component index.", {"query": "string", "top_k": "integer"}, ["query"]),
        _tool("get_related_config_records", "Search local anonymized config record cards.", {"query": "string", "top_k": "integer"}, ["query"]),
        _tool("get_related_knowledge", "Search local internal knowledge cards.", {"query": "string", "top_k": "integer"}, ["query"]),
        _tool("get_knowledge_note", "Read one capped markdown note under .ai/knowledge.", {"path": "string"}, ["path"]),
        _tool("get_solution_design", "Read approved or proposed solution design for a Work Item.", {"work_item_id": "string"}, ["work_item_id"]),
        _tool("get_config_impact", "Read local config impact artifacts for a Work Item.", {"work_item_id": "string"}, ["work_item_id"]),
        _tool("list_knowledge_domain", "List all knowledge cards indexed under a specific domain (e.g. 'billing', 'time-expense').", {"domain": "string", "limit": "integer"}, ["domain"]),
        _tool("rebuild_knowledge_index", "Rebuild the local knowledge card index from .ai/knowledge/ notes. Call this after importing or editing knowledge notes.", {}, []),
        _tool("build_context_pack", "Build a Work Item context pack by searching all local indexes. Writes context-pack.md and relevant-*.yaml under .ai/context/work-items/<id>/.", {"work_item_id": "string", "query": "string"}, ["work_item_id", "query"]),
        _tool("knowledge_search", "BM25 search over local knowledge cards with optional domain and related_object filters.", {"query": "string", "domain": "string", "related_object": "string", "k": "integer"}, ["query"]),
        _tool("knowledge_graph_neighbors", "BFS through the local knowledge graph (depth 1-3) from a node id like 'note:invoice-approval-process' or 'object:kmbi__Invoice__c'.", {"node_id": "string", "depth": "integer"}, ["node_id"]),
        _tool("knowledge_get", "Resolve a knowledge note by slug via the local index and return its content.", {"slug": "string"}, ["slug"]),
    ]


def _tool(name: str, description: str, properties: dict[str, str], required: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": {
                prop: {"type": prop_type}
                for prop, prop_type in properties.items()
            },
            "required": required,
        },
    }


def _concise_record(source_type: str, record: dict[str, Any]) -> dict[str, Any]:
    score = record.get("_search_score")
    if source_type == "metadata":
        return _with_score(
            {
                "source_type": source_type,
                "component_type": record.get("component_type"),
                "name": record.get("full_name"),
                "path": record.get("path"),
                "summary": record.get("summary"),
                "references": record.get("references"),
                "risk_flags": record.get("risk_flags"),
            },
            score,
        )
    if source_type == "sobjects":
        return _with_score(
            {
                "source_type": source_type,
                "api_name": record.get("api_name"),
                "label": record.get("label"),
                "namespace": record.get("namespace"),
                "field_count": record.get("field_count"),
                "relationship_count": record.get("relationship_count"),
                "summary": record.get("summary"),
            },
            score,
        )
    if source_type == "fields":
        return _with_score(
            {
                "source_type": source_type,
                "object_api_name": record.get("object_api_name"),
                "field_api_name": record.get("field_api_name"),
                "label": record.get("label"),
                "data_type": record.get("data_type"),
                "reference_to": record.get("reference_to"),
                "summary": record.get("summary"),
            },
            score,
        )
    if source_type == "relationships":
        return _with_score(
            {
                "source_type": source_type,
                "from_object": record.get("from_object"),
                "field_api_name": record.get("field_api_name"),
                "to_objects": record.get("to_objects"),
                "relationship_name": record.get("relationship_name"),
                "summary": record.get("summary"),
            },
            score,
        )
    if source_type == "config_records":
        return _with_score(
            {
                "source_type": source_type,
                "object_api_name": record.get("object_api_name"),
                "record_key": record.get("record_key"),
                "category": record.get("category"),
                "ai_visibility": record.get("ai_visibility"),
                "summary": record.get("summary"),
                "references": record.get("references"),
                "checksum": record.get("checksum"),
            },
            score,
        )
    if source_type == "knowledge":
        return _with_score(
            {
                "source_type": source_type,
                "title": record.get("title"),
                "domain": record.get("domain"),
                "path": record.get("path"),
                "source_file": record.get("source_file"),
                "confidence": record.get("confidence"),
                "status": record.get("status"),
                "last_reviewed": record.get("last_reviewed"),
                "summary": record.get("summary"),
                "risk_flags": record.get("risk_flags"),
            },
            score,
        )
    return _with_score({"source_type": source_type, "summary": record.get("summary")}, score)


def _with_score(record: dict[str, Any], score: Any) -> dict[str, Any]:
    if score is not None:
        record["score"] = score
    return {key: value for key, value in record.items() if value not in (None, "", [], {})}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
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


def _read_limited(path: Path, repo_root: Path, limit: int = MAX_CONTENT_CHARS) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    truncated = len(text) > limit
    if truncated:
        text = text[:limit] + "\n...[TRUNCATED]"
    try:
        display_path = path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        display_path = path.name
    return {
        "path": display_path,
        "text": text,
        "truncated": truncated,
    }


def _int_arg(arguments: dict[str, Any], key: str, default: int) -> int:
    try:
        value = int(arguments.get(key, default))
    except (TypeError, ValueError):
        return default
    return max(1, min(value, 50))


def _result_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error_response(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
