from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

from ai_workspace.parsers.parse_flow import parse_flow_file


class ParseFlowTests(unittest.TestCase):
    def test_flow_name_process_type_and_references(self) -> None:
        flow_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <Flow xmlns="http://soap.sforce.com/2006/04/metadata">
          <processType>RecordTriggeredFlow</processType>
          <start>
            <object>Account</object>
            <recordTriggerType>CreateAndUpdate</recordTriggerType>
            <triggerType>RecordAfterSave</triggerType>
            <filters>
              <field>Status__c</field>
              <operator>EqualTo</operator>
            </filters>
          </start>
          <decisions>
            <name>Check_Amount</name>
            <rules>
              <name>High_Value</name>
              <conditions>
                <leftValueReference>$Record.Amount__c</leftValueReference>
              </conditions>
            </rules>
          </decisions>
          <assignments>
            <name>Set_Status</name>
            <assignmentItems>
              <assignToReference>$Record.Status__c</assignToReference>
            </assignmentItems>
          </assignments>
          <textTemplates>
            <text>Account.Name and Invoice__c.Amount__c</text>
          </textTemplates>
          <actionCalls>
            <name>RunApex</name>
            <actionType>apex</actionType>
            <actionName>InvoiceAction.run</actionName>
            <faultConnector>
              <targetReference>Handle_Fault</targetReference>
            </faultConnector>
          </actionCalls>
          <recordUpdates>
            <name>Update_Invoice</name>
            <object>Invoice__c</object>
            <inputAssignments>
              <field>Status__c</field>
            </inputAssignments>
          </recordUpdates>
          <subflows>
            <name>Run_Child</name>
            <flowName>Child_Flow</flowName>
          </subflows>
        </Flow>
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Invoice_Flow.flow-meta.xml"
            path.write_text(flow_xml, encoding="utf-8")
            parsed = parse_flow_file(path)

        self.assertEqual(parsed["full_name"], "Invoice_Flow")
        self.assertEqual(parsed["details"]["process_type"], "RecordTriggeredFlow")
        self.assertEqual(parsed["details"]["start_object"], "Account")
        self.assertEqual(parsed["details"]["start"]["trigger_type"], "RecordAfterSave")
        self.assertEqual(parsed["details"]["start"]["record_trigger_type"], "CreateAndUpdate")
        self.assertEqual(parsed["details"]["decisions"][0]["name"], "Check_Amount")
        self.assertEqual(parsed["details"]["assignments"][0]["name"], "Set_Status")
        self.assertEqual(parsed["details"]["record_operations"][0]["operation_type"], "recordUpdates")
        self.assertEqual(parsed["details"]["fault_paths"][0]["target"], "Handle_Fault")
        self.assertIn("Account", parsed["references"]["objects"])
        self.assertIn("Invoice__c", parsed["references"]["objects"])
        self.assertIn("Account.Status__c", parsed["references"]["fields"])
        self.assertIn("Invoice__c.Amount__c", parsed["references"]["fields"])
        self.assertIn("Invoice__c.Status__c", parsed["references"]["fields"])
        self.assertIn("InvoiceAction", parsed["references"]["apex_classes"])
        self.assertIn("Child_Flow", parsed["references"]["flows"])
        self.assertIn("record_triggered_flow_candidate", parsed["risk_flags"])
        self.assertIn("apex_action_candidate", parsed["risk_flags"])
        self.assertIn("record_operation_candidate", parsed["risk_flags"])
        self.assertEqual(parsed["parse_status"], "ok")

    def test_partial_parse_status_on_utf8_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Partial.flow-meta.xml"
            path.write_bytes(b"<Flow><processType>AutoLaunchedFlow</processType><description>\xff</description></Flow>")
            with redirect_stderr(StringIO()):
                parsed = parse_flow_file(path)

        self.assertEqual(parsed["full_name"], "Partial")
        self.assertIn(parsed["parse_status"], {"ok", "partial"})
        self.assertEqual(parsed["parse_status"], "partial")


if __name__ == "__main__":
    unittest.main()
