from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_workspace.search.simple_search import score_record, search_jsonl, tokenize


class SimpleSearchTests(unittest.TestCase):
    def test_tokenize_lowercases_and_splits(self) -> None:
        self.assertEqual(tokenize("Invoice-Approval Flow__c"), ["invoice", "approval", "flow__c"])

    def test_search_jsonl_returns_relevant_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "index.jsonl"
            records = [
                {"full_name": "InvoiceApprovalFlow", "summary": "Handles invoice approval routing", "parse_status": "ok"},
                {"full_name": "Unrelated", "summary": "Calendar setup", "parse_status": "ok"},
            ]
            path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

            results = search_jsonl(str(path), "invoice approval", 5)

        self.assertEqual([result["full_name"] for result in results], ["InvoiceApprovalFlow"])
        self.assertGreater(results[0]["_search_score"], 0)

    def test_exact_and_partial_match_scoring(self) -> None:
        exact = {"full_name": "Invoice Approval", "summary": "invoice approval", "parse_status": "ok"}
        partial = {"full_name": "Invoice", "summary": "invoice queue", "parse_status": "ok"}

        self.assertGreater(score_record(exact, tokenize("invoice approval")), score_record(partial, tokenize("invoice approval")))

    def test_failed_parse_status_is_penalized(self) -> None:
        ok = {"full_name": "InvoiceApproval", "summary": "invoice approval", "parse_status": "ok"}
        failed = {"full_name": "InvoiceApproval", "summary": "invoice approval", "parse_status": "failed"}

        self.assertLess(score_record(failed, tokenize("invoice approval")), score_record(ok, tokenize("invoice approval")))


if __name__ == "__main__":
    unittest.main()
