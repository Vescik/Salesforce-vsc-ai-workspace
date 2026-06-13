from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_workspace.security.no_salesforce_ids import (
    find_salesforce_id_candidates_in_text,
    scan_paths_for_salesforce_ids,
)


ID_15 = "001" + "ABCdefGHIjkL"
ID_18 = ID_15 + "123"


class NoSalesforceIdsTests(unittest.TestCase):
    def test_detects_15_and_18_character_salesforce_id_candidates(self) -> None:
        findings = find_salesforce_id_candidates_in_text(
            f"first {ID_15}\nsecond {ID_18}\n"
        )

        self.assertEqual([finding["line"] for finding in findings], [1, 2])
        self.assertEqual([finding["candidate"] for finding in findings], [ID_15, ID_18])

    def test_scan_paths_reports_line_number(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = root / "force-app/main/default/classes/Foo.cls"
            file_path.parent.mkdir(parents=True)
            file_path.write_text(f"String id = '{ID_15}';\n", encoding="utf-8")

            findings = scan_paths_for_salesforce_ids(["force-app/main/default/classes/Foo.cls"], str(root))

        self.assertEqual(findings[0]["path"], "force-app/main/default/classes/Foo.cls")
        self.assertEqual(findings[0]["line"], 1)
        self.assertEqual(findings[0]["severity"], "high")

    def test_binary_files_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = root / "force-app/main/default/staticresources/blob.resource"
            file_path.parent.mkdir(parents=True)
            file_path.write_bytes(b"\x00" + ID_15.encode("ascii"))

            findings = scan_paths_for_salesforce_ids(["force-app/main/default/staticresources/blob.resource"], str(root))

        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
