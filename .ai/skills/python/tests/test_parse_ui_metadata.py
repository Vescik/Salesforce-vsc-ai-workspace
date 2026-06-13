from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_workspace.parsers.parse_flexipage import parse_flexipage_file
from ai_workspace.parsers.parse_layout import parse_layout_file


class ParseUiMetadataTests(unittest.TestCase):
    def test_flexipage_component_visibility_and_field_references(self) -> None:
        flexipage_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <FlexiPage xmlns="http://soap.sforce.com/2006/04/metadata">
          <masterLabel>Account Record Page</masterLabel>
          <sobjectType>Account</sobjectType>
          <type>RecordPage</type>
          <flexiPageRegions>
            <name>main</name>
            <type>Region</type>
            <itemInstances>
              <componentInstance>
                <componentName>c:accountHealthPanel</componentName>
                <componentInstanceProperties>
                  <name>fieldName</name>
                  <value>Account.Health_Score__c</value>
                </componentInstanceProperties>
                <visibilityRule>
                  <criteria>
                    <leftValue>Account.Type</leftValue>
                  </criteria>
                </visibilityRule>
              </componentInstance>
            </itemInstances>
          </flexiPageRegions>
        </FlexiPage>
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Account_Record_Page.flexipage-meta.xml"
            path.write_text(flexipage_xml, encoding="utf-8")
            parsed = parse_flexipage_file(path)

        self.assertEqual(parsed["full_name"], "Account_Record_Page")
        self.assertEqual(parsed["details"]["sobject_type"], "Account")
        self.assertIn("Account", parsed["references"]["objects"])
        self.assertIn("Account.Health_Score__c", parsed["references"]["fields"])
        self.assertIn("Account.Type", parsed["references"]["fields"])
        self.assertIn("accountHealthPanel", parsed["references"]["lwc_components"])
        self.assertIn("custom_ui_component_candidate", parsed["risk_flags"])
        self.assertIn("dynamic_visibility_candidate", parsed["risk_flags"])
        self.assertEqual(parsed["parse_status"], "ok")

    def test_layout_fields_actions_and_related_lists(self) -> None:
        layout_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <Layout xmlns="http://soap.sforce.com/2006/04/metadata">
          <layoutSections>
            <label>Details</label>
            <layoutColumns>
              <layoutItems>
                <field>Name</field>
              </layoutItems>
              <layoutItems>
                <field>Health_Score__c</field>
              </layoutItems>
            </layoutColumns>
          </layoutSections>
          <customButtons>Refresh_Health</customButtons>
          <quickActionList>
            <quickActionListItems>
              <quickActionName>Account.NewContact</quickActionName>
            </quickActionListItems>
          </quickActionList>
          <relatedLists>
            <relatedList>Contacts</relatedList>
            <fields>Contact.Name</fields>
          </relatedLists>
        </Layout>
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Account-Account Layout.layout-meta.xml"
            path.write_text(layout_xml, encoding="utf-8")
            parsed = parse_layout_file(path)

        self.assertEqual(parsed["full_name"], "Account-Account Layout")
        self.assertEqual(parsed["details"]["object"], "Account")
        self.assertIn("Account", parsed["references"]["objects"])
        self.assertIn("Account.Name", parsed["references"]["fields"])
        self.assertIn("Account.Health_Score__c", parsed["references"]["fields"])
        self.assertIn("custom_button_candidate", parsed["risk_flags"])
        self.assertIn("quick_action_candidate", parsed["risk_flags"])
        self.assertIn("related_list_candidate", parsed["risk_flags"])
        self.assertEqual(parsed["parse_status"], "ok")


if __name__ == "__main__":
    unittest.main()
