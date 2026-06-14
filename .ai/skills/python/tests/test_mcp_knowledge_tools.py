from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_workspace.mcp.salesforce_context_mcp import SalesforceContextServer


class McpKnowledgeToolsTests(unittest.TestCase):
    def test_knowledge_search_filters_by_semantic_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            index_dir = repo_root / ".ai" / "context" / "index"
            context_root = repo_root / ".ai" / "context"
            knowledge_root = repo_root / ".ai" / "knowledge" / "domains" / "billing"
            index_dir.mkdir(parents=True)
            knowledge_root.mkdir(parents=True)
            records = [
                {
                    "title": "Invoice Approval",
                    "domain": "billing",
                    "path": ".ai/knowledge/domains/billing/invoice-approval.md",
                    "summary": "Invoice approval rules.",
                    "keywords": ["invoice", "approval"],
                    "usage_context": ["Solution Design"],
                    "related_objects": ["Invoice__c"],
                    "related_fields": ["Invoice__c.Status__c"],
                    "status": "draft",
                    "confidence": "low",
                },
                {
                    "title": "Timesheets",
                    "domain": "delivery",
                    "path": ".ai/knowledge/domains/billing/timesheets.md",
                    "summary": "Timesheet process.",
                    "keywords": ["timesheet"],
                    "usage_context": ["Testing"],
                    "related_objects": ["TimeEntry__c"],
                    "status": "draft",
                    "confidence": "low",
                },
            ]
            (index_dir / "knowledge-cards.jsonl").write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
            server = SalesforceContextServer(repo_root, index_dir, context_root)

            result = server.knowledge_search("invoice approval", "billing", "Solution Design", "Invoice__c", "Status__c", None, "draft", "low", 5)

        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["title"], "Invoice Approval")


if __name__ == "__main__":
    unittest.main()
