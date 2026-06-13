from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_workspace.knowledge.knowledge_search import results_to_markdown, search_knowledge


class KnowledgeSearchTests(unittest.TestCase):
    def test_search_finds_relevant_knowledge_card(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "knowledge-cards.jsonl"
            records = [
                {
                    "card_type": "knowledge_note",
                    "title": "Invoice Approval",
                    "domain": "billing",
                    "path": ".ai/knowledge/domains/billing/invoice-approval.md",
                    "summary": "Explains invoice approval routing.",
                    "content_excerpt": "Long body content that should not be printed by CLI markdown.",
                    "keywords": ["invoice", "approval"],
                    "risk_flags": [],
                },
                {
                    "card_type": "knowledge_note",
                    "title": "Timesheets",
                    "domain": "delivery",
                    "path": ".ai/knowledge/domains/delivery/timesheets.md",
                    "summary": "Timesheet process notes.",
                    "keywords": ["timesheet"],
                    "risk_flags": [],
                },
            ]
            index_path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

            results = search_knowledge("invoice approval", index_path, top_k=5)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Invoice Approval")

    def test_markdown_results_do_not_print_full_excerpt(self) -> None:
        markdown = results_to_markdown(
            "invoice",
            [
                {
                    "title": "Invoice Approval",
                    "domain": "billing",
                    "path": ".ai/knowledge/domains/billing/invoice-approval.md",
                    "summary": "Short summary",
                    "content_excerpt": "Long body content that should not appear",
                    "risk_flags": ["draft_status"],
                    "score": 10,
                }
            ],
        )

        self.assertIn("# Knowledge Search Results", markdown)
        self.assertIn("Invoice Approval", markdown)
        self.assertIn("draft_status", markdown)
        self.assertNotIn("Long body content", markdown)


if __name__ == "__main__":
    unittest.main()
