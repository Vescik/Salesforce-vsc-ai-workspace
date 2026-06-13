from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_workspace.wiki.wiki_scanner import scan_wiki


class WikiScannerTests(unittest.TestCase):
    def test_scan_wiki_indexes_pages_headings_and_order_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            wiki = Path(temp_dir)
            (wiki / "Invoicing").mkdir()
            (wiki / "Home.md").write_text("# Home\n\nWelcome.\n", encoding="utf-8")
            (wiki / "Invoicing" / "Overview.md").write_text(
                "# Invoicing\n\n## Invoice Approval\n\nExisting invoicing documentation.\n",
                encoding="utf-8",
            )
            (wiki / "Invoicing" / ".order").write_text("Overview\n", encoding="utf-8")

            index = scan_wiki(wiki)

        paths = {page["path"] for page in index["pages"]}
        self.assertIn("/Home", paths)
        self.assertIn("/Invoicing/Overview", paths)
        invoicing = next(page for page in index["pages"] if page["path"] == "/Invoicing/Overview")
        self.assertEqual(invoicing["title"], "Invoicing")
        self.assertIn("Invoice Approval", invoicing["headings"])
        self.assertEqual(invoicing["order_position"], 1)
        self.assertIn("/Invoicing", {folder["path"] for folder in index["folders"]})


if __name__ == "__main__":
    unittest.main()
