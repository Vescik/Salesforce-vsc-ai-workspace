from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_workspace.parsers.parse_permissions import parse_permission_set_file, parse_profile_file


class ParsePermissionsTests(unittest.TestCase):
    def test_permission_set_access_references_and_risk_flags(self) -> None:
        permission_set_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
          <label>Invoice Access</label>
          <objectPermissions>
            <object>Invoice__c</object>
            <allowCreate>true</allowCreate>
            <allowRead>true</allowRead>
            <allowEdit>true</allowEdit>
            <allowDelete>false</allowDelete>
            <viewAllRecords>true</viewAllRecords>
            <modifyAllRecords>false</modifyAllRecords>
          </objectPermissions>
          <fieldPermissions>
            <field>Invoice__c.Amount__c</field>
            <readable>true</readable>
            <editable>false</editable>
          </fieldPermissions>
          <classAccesses>
            <apexClass>InvoiceController</apexClass>
            <enabled>true</enabled>
          </classAccesses>
          <flowAccesses>
            <flow>Invoice_Flow</flow>
            <enabled>true</enabled>
          </flowAccesses>
          <customMetadataTypeAccesses>
            <name>Invoice_Setting__mdt</name>
            <enabled>true</enabled>
          </customMetadataTypeAccesses>
        </PermissionSet>
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Invoice_Access.permissionset-meta.xml"
            path.write_text(permission_set_xml, encoding="utf-8")
            parsed = parse_permission_set_file(path)

        self.assertEqual(parsed["full_name"], "Invoice_Access")
        self.assertIn("Invoice__c", parsed["references"]["objects"])
        self.assertIn("Invoice__c.Amount__c", parsed["references"]["fields"])
        self.assertIn("InvoiceController", parsed["references"]["apex_classes"])
        self.assertIn("Invoice_Flow", parsed["references"]["flows"])
        self.assertIn("Invoice_Setting__mdt", parsed["references"]["custom_metadata"])
        self.assertIn("object_crud_permissions", parsed["risk_flags"])
        self.assertIn("field_level_security_permissions", parsed["risk_flags"])
        self.assertIn("apex_class_access_candidate", parsed["risk_flags"])
        self.assertIn("flow_access_candidate", parsed["risk_flags"])
        self.assertIn("elevated_object_permission_candidate", parsed["risk_flags"])
        self.assertEqual(parsed["parse_status"], "ok")

    def test_profile_user_permissions_are_flagged(self) -> None:
        profile_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <Profile xmlns="http://soap.sforce.com/2006/04/metadata">
          <userPermissions>
            <name>ModifyAllData</name>
            <enabled>true</enabled>
          </userPermissions>
          <tabSettings>
            <tab>Invoice__c</tab>
            <visibility>DefaultOn</visibility>
          </tabSettings>
        </Profile>
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Admin.profile-meta.xml"
            path.write_text(profile_xml, encoding="utf-8")
            parsed = parse_profile_file(path)

        self.assertEqual(parsed["full_name"], "Admin")
        self.assertIn("Invoice__c", parsed["references"]["objects"])
        self.assertIn("profile_metadata", parsed["risk_flags"])
        self.assertIn("elevated_system_permission_candidate", parsed["risk_flags"])
        self.assertEqual(parsed["details"]["user_permissions"][0]["name"], "ModifyAllData")


if __name__ == "__main__":
    unittest.main()
