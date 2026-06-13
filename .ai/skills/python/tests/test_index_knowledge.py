from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_workspace.knowledge.index_knowledge import build_knowledge_index


class IndexKnowledgeTests(unittest.TestCase):
    def test_index_card_creation_and_risk_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / ".ai" / "knowledge"
            note = root / "domains" / "general" / "example.md"
            note.parent.mkdir(parents=True)
            note.write_text(
                """---
title: "Example"
domain: "general"
source_type: "internal_knowledge"
source_file: ".ai/knowledge/imports/example.txt"
owner: ""
status: "draft"
confidence: "low"
last_reviewed: "2020-01-01"
related_objects:
  - "Example__c"
related_config_objects:
  - "Example_Config__c"
related_processes:
  - "Example Process"
keywords:
  - "example"
---

# Summary

Example body.
""",
                encoding="utf-8",
            )

            records = build_knowledge_index(root)

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["title"], "Example")
        self.assertIn("Example__c", record["related_objects"])
        self.assertIn("draft_status", record["risk_flags"])
        self.assertIn("low_confidence", record["risk_flags"])
        self.assertIn("missing_owner", record["risk_flags"])
        self.assertIn("stale_review", record["risk_flags"])
        self.assertIn("Summary", record["headings"])

    def test_missing_front_matter_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / ".ai" / "knowledge"
            note = root / "domains" / "general" / "missing-front-matter.md"
            note.parent.mkdir(parents=True)
            note.write_text("# Missing Front Matter\n\nBody text.", encoding="utf-8")

            records = build_knowledge_index(root)

        self.assertEqual(len(records), 1)
        self.assertIn("missing_front_matter", records[0]["risk_flags"])


if __name__ == "__main__":
    unittest.main()
