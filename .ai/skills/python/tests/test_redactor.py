from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_workspace.security.redactor import load_simple_yaml, mask_record, mask_value


POLICY = {
    "default_action": "allow_anonymized",
    "blocked_fields": ["Id", "OwnerId", "SystemModstamp"],
    "field_name_rules": {
        "redact": [".*Email.*", ".*Phone.*", ".*Token.*"],
        "bucketize": [".*Amount.*", ".*Rate.*"],
        "summarize": [".*Description.*"],
    },
    "limits": {"max_string_length": 10},
}
ID_15 = "001" + "ABCdefGHIjkL"
USER_ID_15 = "005" + "ABCdefGHIjkL"


class RedactorTests(unittest.TestCase):
    def test_blocked_fields_removed_from_record(self) -> None:
        masked = mask_record({"Id": ID_15, "Name": "Config", "OwnerId": USER_ID_15}, POLICY)

        self.assertEqual(masked, {"Name": "Config"})

    def test_email_phone_and_token_fields_redacted(self) -> None:
        self.assertEqual(mask_value("ContactEmail__c", "person@example.com", POLICY), "[REDACTED]")
        self.assertEqual(mask_value("SupportPhone__c", "+1 555 0100", POLICY), "[REDACTED]")
        self.assertEqual(mask_value("ApiToken__c", "secret-token", POLICY), "[REDACTED]")

    def test_amount_and_rate_fields_bucketized(self) -> None:
        self.assertEqual(mask_value("Amount__c", 250, POLICY), "101-1000")
        self.assertEqual(mask_value("Rate__c", 0.5, POLICY), "[BUCKETIZED]")

    def test_long_text_truncated(self) -> None:
        self.assertEqual(mask_value("Description__c", "abcdefghijklmnopqrstuvwxyz", POLICY), "abcdefghij...[TRUNCATED]")

    def test_simple_yaml_accepts_indented_empty_list_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config-impact.yaml"
            path.write_text("target_environments:\n  []\nrisks:\n  - Review config sidecar.\n", encoding="utf-8")

            loaded = load_simple_yaml(str(path))

        self.assertEqual(loaded["target_environments"], [])
        self.assertEqual(loaded["risks"], ["Review config sidecar."])


if __name__ == "__main__":
    unittest.main()
