from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_workspace.knowledge.import_knowledge import import_source


class ImportKnowledgeTests(unittest.TestCase):
    def test_import_source_creates_draft_markdown_note(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            source = repo_root / ".ai" / "knowledge" / "imports" / "example.txt"
            source.parent.mkdir(parents=True)
            source.write_text("Example imported knowledge with email test@example.com.", encoding="utf-8")
            out_dir = repo_root / ".ai" / "knowledge" / "domains"

            records = import_source(
                source=source,
                domain="general",
                title="Example Knowledge Note",
                owner="Salesforce Platform Team",
                confidence="low",
                status="draft",
                out_dir=out_dir,
                max_chars=200_000,
                chunk_size=6000,
                overwrite=False,
                dry_run=False,
                repo_root=repo_root,
            )

            note = repo_root / records[0]["outputs"][0]
            note_exists = note.exists()
            text = note.read_text(encoding="utf-8")

        self.assertTrue(note_exists)
        self.assertIn('status: "draft"', text)
        self.assertIn('confidence: "low"', text)
        self.assertIn("[REDACTED_EMAIL]", text)
        self.assertIn("Review Required", text)
        self.assertEqual(records[0]["parse_status"], "ok")


if __name__ == "__main__":
    unittest.main()
