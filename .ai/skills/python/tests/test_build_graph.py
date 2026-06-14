from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_workspace.knowledge.build_graph import main as build_graph_main


class BuildGraphTests(unittest.TestCase):
    def test_graph_includes_v2_semantic_nodes_and_edges(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            index_dir = root / ".ai" / "context" / "index"
            index_dir.mkdir(parents=True)
            card = {
                "title": "Invoice Rules",
                "domain": "billing",
                "path": ".ai/knowledge/domains/billing/invoice-rules.md",
                "source_file": ".ai/knowledge/imports/invoice.xml",
                "source_format": "xml",
                "source_checksum": "abc",
                "status": "draft",
                "confidence": "low",
                "related_objects": ["Invoice__c"],
                "related_fields": ["Invoice__c.Status__c"],
                "related_metadata": ["Flow:Invoice Approval"],
                "related_processes": ["Invoice Approval"],
                "integration_points": ["REST"],
                "dependencies": ["InvoiceService"],
                "business_rules": ["Must reject invoices without status."],
            }
            (index_dir / "knowledge-cards.jsonl").write_text(json.dumps(card) + "\n", encoding="utf-8")
            out = index_dir / "knowledge-graph.json"

            code = build_graph_main([
                "--knowledge-root", str(root / ".ai" / "knowledge"),
                "--index-dir", str(index_dir),
                "--work-items-dir", str(root / ".ai" / "context" / "work-items"),
                "--out", str(out),
                "--adjacency-cap", "20",
            ])
            graph = json.loads(out.read_text(encoding="utf-8"))
            node_ids = {node["id"] for node in graph["nodes"]}
            edge_keys = {(edge["source"], edge["target"], edge["type"]) for edge in graph["edges"]}

        self.assertEqual(code, 0)
        self.assertIn("file:.ai/knowledge/imports/invoice.xml", node_ids)
        self.assertIn("field:Invoice__c.Status__c", node_ids)
        self.assertIn("metadata_component:flow:Invoice Approval", node_ids)
        self.assertIn(("note:invoice-rules", "field:Invoice__c.Status__c", "mentions"), edge_keys)
        self.assertIn(("note:invoice-rules", "file:.ai/knowledge/imports/invoice.xml", "derived_from"), edge_keys)


if __name__ == "__main__":
    unittest.main()
