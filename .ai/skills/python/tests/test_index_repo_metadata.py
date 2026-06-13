from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_workspace.indexers.index_repo_metadata import build_index


class IndexRepoMetadataTests(unittest.TestCase):
    def test_indexer_uses_richer_xml_parsers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            flexipage_dir = repo_root / "force-app" / "main" / "default" / "flexipages"
            permissionset_dir = repo_root / "force-app" / "main" / "default" / "permissionsets"
            flexipage_dir.mkdir(parents=True)
            permissionset_dir.mkdir(parents=True)
            (flexipage_dir / "Account_Record_Page.flexipage-meta.xml").write_text(
                """<FlexiPage xmlns="http://soap.sforce.com/2006/04/metadata">
                  <sobjectType>Account</sobjectType>
                  <type>RecordPage</type>
                </FlexiPage>
                """,
                encoding="utf-8",
            )
            (permissionset_dir / "Invoice.permissionset-meta.xml").write_text(
                """<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
                  <fieldPermissions>
                    <field>Invoice__c.Amount__c</field>
                    <readable>true</readable>
                  </fieldPermissions>
                </PermissionSet>
                """,
                encoding="utf-8",
            )

            records = build_index(repo_root)

        by_type = {record["component_type"]: record for record in records}
        self.assertEqual(by_type["FlexiPage"]["details"]["sobject_type"], "Account")
        self.assertIn("flexipage_metadata", by_type["FlexiPage"]["risk_flags"])
        self.assertIn("Invoice__c.Amount__c", by_type["PermissionSet"]["references"]["fields"])
        self.assertIn("field_level_security_permissions", by_type["PermissionSet"]["risk_flags"])


if __name__ == "__main__":
    unittest.main()
