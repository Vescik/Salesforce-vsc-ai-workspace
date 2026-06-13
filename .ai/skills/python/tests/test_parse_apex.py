from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_workspace.parsers.parse_apex import parse_apex_file


ID_15 = "001" + "ABCdefGHIjkL"


class ParseApexTests(unittest.TestCase):
    def test_apex_class_risk_and_reference_extraction(self) -> None:
        apex = """
        public with sharing class InvoiceController {
            public void saveIt() {
                List<Account> accounts = [SELECT Id, Name FROM Account WHERE Name = 'Acme'];
                Custom_Config__c config = Custom_Config__c.getInstance('Default');
                String fieldRef = Custom_Config__c.Setting__c;
                String recordId = '""" + ID_15 + """';
                update accounts;
                HttpRequest request = new HttpRequest();
            }
        }
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "InvoiceController.cls"
            path.write_text(apex, encoding="utf-8")
            parsed = parse_apex_file(path)

        self.assertEqual(parsed["full_name"], "InvoiceController")
        self.assertEqual(parsed["details"]["sharing"], "with sharing")
        self.assertIn("Account", parsed["references"]["objects"])
        self.assertIn("Custom_Config__c", parsed["references"]["objects"])
        self.assertIn("Custom_Config__c.Setting__c", parsed["references"]["fields"])
        self.assertIn("dml_detected", parsed["risk_flags"])
        self.assertIn("callout_detected", parsed["risk_flags"])
        self.assertIn("hardcoded_salesforce_id_candidate", parsed["risk_flags"])
        self.assertEqual(parsed["parse_status"], "ok")

    def test_sharing_not_declared_for_class(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "NoSharing.cls"
            path.write_text("public class NoSharing {}", encoding="utf-8")
            parsed = parse_apex_file(path)

        self.assertIn("sharing_not_declared", parsed["risk_flags"])


if __name__ == "__main__":
    unittest.main()
