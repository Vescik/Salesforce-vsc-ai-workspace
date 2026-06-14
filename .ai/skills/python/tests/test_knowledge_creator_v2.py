from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_workspace.knowledge.converters import dispatch
from ai_workspace.knowledge.import_knowledge import import_source
from ai_workspace.knowledge.index_knowledge import build_knowledge_index
from ai_workspace.knowledge.knowledge_search import search_knowledge


class KnowledgeCreatorV2Tests(unittest.TestCase):
    def test_converters_cover_target_source_formats(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "note.md").write_text("# Invoice Approval\n\nUses Invoice__c.Status__c.", encoding="utf-8")
            (root / "note.txt").write_text("Invoice Approval\n\nApex class InvoiceService handles approval.", encoding="utf-8")
            (root / "records.csv").write_text("Name,Object,Field\nApproval,Invoice__c,Status__c\n", encoding="utf-8")
            (root / "flow.flow-meta.xml").write_text(
                """<Flow>
  <fullName>Invoice_Approval_Flow</fullName>
  <processType>Flow</processType>
  <decisions><name>Check_Amount</name></decisions>
  <assignments><name>Set_Status</name></assignments>
  <actionCalls><name>Notify_Finance</name><actionName>SendEmail</actionName></actionCalls>
</Flow>""",
                encoding="utf-8",
            )
            (root / "fake.pdf").write_bytes(b"%PDF-1.4\nnot a real pdf\n")

            md = dispatch(root / "note.md")
            txt = dispatch(root / "note.txt")
            csv_doc = dispatch(root / "records.csv")
            flow = dispatch(root / "flow.flow-meta.xml")
            pdf = dispatch(root / "fake.pdf")

        self.assertEqual(md["format"], "md")
        self.assertEqual(txt["format"], "txt")
        self.assertEqual(csv_doc["format"], "csv")
        self.assertEqual(flow["format"], "xml")
        self.assertEqual(pdf["format"], "pdf")
        self.assertGreaterEqual(len(csv_doc["tables"]), 1)
        self.assertIn("raw_xml", flow["metadata"])

    def test_source_to_note_to_index_to_search_uses_v2_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            source = repo_root / ".ai" / "knowledge" / "imports" / "Invoice__c.object-meta.xml"
            source.parent.mkdir(parents=True)
            source.write_text(
                """<CustomObject>
  <fullName>Invoice__c</fullName>
  <label>Invoice</label>
  <fields><fullName>Status__c</fullName><label>Status</label></fields>
  <validationRules>
    <fullName>Status_Required</fullName>
    <errorConditionFormula>ISBLANK(Status__c)</errorConditionFormula>
  </validationRules>
</CustomObject>""",
                encoding="utf-8",
            )
            records = import_source(
                source=source,
                domain="billing",
                title="Invoice Object Rules",
                owner="Salesforce Platform Team",
                confidence="low",
                status="draft",
                out_dir=repo_root / ".ai" / "knowledge" / "domains",
                max_chars=200_000,
                chunk_size=6000,
                overwrite=False,
                dry_run=False,
                repo_root=repo_root,
            )
            note_path = repo_root / records[0]["outputs"][0]
            note_text = note_path.read_text(encoding="utf-8")
            cards = build_knowledge_index(repo_root / ".ai" / "knowledge")
            index_path = repo_root / ".ai" / "context" / "index" / "knowledge-cards.jsonl"
            index_path.parent.mkdir(parents=True)
            index_path.write_text("\n".join(__import__("json").dumps(card) for card in cards) + "\n", encoding="utf-8")
            results = search_knowledge("Status Required", index_path, object_api_name="Invoice__c")

        self.assertIn("source_checksum:", note_text)
        self.assertIn("related_fields:", note_text)
        self.assertIn("Status__c", note_text)
        self.assertEqual(cards[0]["source_format"], "xml")
        self.assertIn("Invoice__c", cards[0]["related_objects"])
        self.assertTrue(results)
        self.assertTrue(str(results[0]["title"]).startswith("Invoice Object Rules"))

    def test_apex_and_flow_references_are_extracted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            source = repo_root / ".ai" / "knowledge" / "imports" / "apex-flow.txt"
            source.parent.mkdir(parents=True)
            source.write_text(
                """public class InvoiceService {
  public static void approveInvoice(Invoice__c invoice) {}
}
trigger InvoiceTrigger on Invoice__c (before insert) {}
Flow: Invoice Approval Flow
Decision: Check Amount
Assignment: Set Status
Must reject invoices without Invoice__c.Status__c.""",
                encoding="utf-8",
            )
            records = import_source(
                source=source,
                domain="billing",
                title="Invoice Automation",
                owner="Salesforce Platform Team",
                confidence="low",
                status="draft",
                out_dir=repo_root / ".ai" / "knowledge" / "domains",
                max_chars=200_000,
                chunk_size=6000,
                overwrite=False,
                dry_run=False,
                repo_root=repo_root,
            )
            note_text = (repo_root / records[0]["outputs"][0]).read_text(encoding="utf-8")

        self.assertIn("InvoiceService", note_text)
        self.assertIn("approveInvoice", note_text)
        self.assertIn("InvoiceTrigger", note_text)
        self.assertIn("Invoice Approval Flow", note_text)
        self.assertIn("Must reject invoices", note_text)


if __name__ == "__main__":
    unittest.main()
