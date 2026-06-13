from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from ai_workspace.config.config_diff import main


class ConfigDiffTests(unittest.TestCase):
    def test_added_removed_changed_and_unchanged_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.jsonl"
            target = root / "target.jsonl"
            markdown_out = root / "diff.md"
            json_out = root / "diff.json"
            source_records = [
                {"record_key": "added", "checksum": "a1"},
                {"record_key": "changed", "checksum": "new"},
                {"record_key": "same", "checksum": "same"},
            ]
            target_records = [
                {"record_key": "removed", "checksum": "r1"},
                {"record_key": "changed", "checksum": "old"},
                {"record_key": "same", "checksum": "same"},
            ]
            source.write_text("\n".join(json.dumps(record) for record in source_records) + "\n", encoding="utf-8")
            target.write_text("\n".join(json.dumps(record) for record in target_records) + "\n", encoding="utf-8")

            with redirect_stdout(StringIO()):
                exit_code = main([
                    "--source",
                    str(source),
                    "--target",
                    str(target),
                    "--out",
                    str(markdown_out),
                    "--json-out",
                    str(json_out),
                ])
            diff = json.loads(json_out.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(diff["added"], ["added"])
        self.assertEqual(diff["removed"], ["removed"])
        self.assertEqual(diff["changed"], ["changed"])
        self.assertEqual(diff["unchanged"], ["same"])


if __name__ == "__main__":
    unittest.main()
