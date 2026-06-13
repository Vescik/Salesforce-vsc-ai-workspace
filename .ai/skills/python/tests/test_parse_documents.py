from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_workspace.knowledge.parse_documents import chunk_text, extract_text


class ParseDocumentsTests(unittest.TestCase):
    def test_txt_and_markdown_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            txt = root / "note.txt"
            md = root / "note.md"
            txt.write_text("Alpha\n\nBeta", encoding="utf-8")
            md.write_text("# Heading\n\nMarkdown body", encoding="utf-8")

            txt_result = extract_text(txt)
            md_result = extract_text(md)

        self.assertEqual(txt_result["source_format"], "txt")
        self.assertEqual(txt_result["parse_status"], "ok")
        self.assertIn("Alpha", txt_result["text"])
        self.assertEqual(md_result["source_format"], "markdown")
        self.assertIn("Markdown body", md_result["text"])

    def test_xml_json_and_csv_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            xml = root / "note.xml"
            js = root / "note.json"
            csv = root / "note.csv"
            xml.write_text("<root><name>Invoice</name></root>", encoding="utf-8")
            js.write_text('{"name": "Invoice", "items": [{"status": "draft"}]}', encoding="utf-8")
            csv.write_text("name,status\nInvoice,draft\n", encoding="utf-8")

            xml_result = extract_text(xml)
            json_result = extract_text(js)
            csv_result = extract_text(csv)

        self.assertIn("name: Invoice", xml_result["text"])
        self.assertIn("name: Invoice", json_result["text"])
        self.assertIn("Headers: name, status", csv_result["text"])
        self.assertIn("Row 1: name=Invoice", csv_result["text"])

    def test_chunking_with_overlap(self) -> None:
        chunks = chunk_text("0123456789" * 10, max_chars=25, overlap=5)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(chunks[1].startswith(chunks[0][-5:]))


if __name__ == "__main__":
    unittest.main()
