from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_workspace.knowledge.validate_knowledge import validate_file


class ValidateKnowledgeTests(unittest.TestCase):
    def _schema(self) -> dict:
        return json.loads(Path(".ai/templates/schemas/knowledge-note.schema.json").read_text(encoding="utf-8"))

    def test_v2_quality_warnings_do_not_block_valid_draft(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / ".ai" / "knowledge"
            note = root / "domains" / "general" / "example.md"
            note.parent.mkdir(parents=True)
            note.write_text(
                """---
title: "Example"
domain: "general"
source_type: "internal_knowledge"
purpose: ""
source_file: ".ai/knowledge/imports/example.txt"
source_format: "txt"
source_checksum: "abc"
owner: "Salesforce Platform Team"
status: "draft"
confidence: "low"
last_reviewed: "2026-06-14"
applies_to:
  - "KimbleOne/Kantata"
usage_context:
  - "Documentation"
keywords:
---

# Summary

Body.

# Source

# Search Terms

# Review Notes
""",
                encoding="utf-8",
            )
            findings = validate_file(note, root, self._schema(), 180, set(), set())

        self.assertIn("knowledge_quality", {finding["type"] for finding in findings})
        self.assertNotIn("blocking", {finding["severity"] for finding in findings})

    def test_salesforce_id_in_body_blocks_non_governance_note(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / ".ai" / "knowledge"
            note = root / "domains" / "general" / "bad.md"
            note.parent.mkdir(parents=True)
            note.write_text(
                """---
title: "Bad"
domain: "general"
source_type: "internal_knowledge"
owner: "Salesforce Platform Team"
status: "draft"
confidence: "low"
last_reviewed: "2026-06-14"
---

# Summary

Do not store 001000000000000AAA in knowledge.
""",
                encoding="utf-8",
            )
            findings = validate_file(note, root, self._schema(), 180, set(), set())

        self.assertIn("prohibited_class", {finding["type"] for finding in findings})
        self.assertIn("blocking", {finding["severity"] for finding in findings})


if __name__ == "__main__":
    unittest.main()
