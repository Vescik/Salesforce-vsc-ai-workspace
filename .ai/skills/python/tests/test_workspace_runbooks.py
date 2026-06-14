from __future__ import annotations

import unittest
from pathlib import Path


RUNBOOK_REQUIRED_HEADINGS = (
    "## Purpose",
    "## When To Use",
    "## Inputs",
    "## Preconditions",
    "## Operator Steps",
    "## Expected Outputs",
    "## Review Gates",
    "## Troubleshooting",
    "## Escalation",
    "## Safety Boundaries",
    "## Maintenance",
)

OPERATOR_RUNBOOKS = (
    "developer-process-runbook.md",
    "knowledge-base-runbook.md",
    "azure-wiki-publication-runbook.md",
    "troubleshooting.md",
)

FORBIDDEN_DOC_SNIPPETS = (
    "sf project deploy start",
    "sf data update record",
    "sf data delete record",
    "sf data upsert",
    "allow_salesforce_writes: true",
    "allow_config_apply: true",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "LANGCHAIN_API_KEY",
)


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "AGENTS.md").exists():
            return candidate
    raise RuntimeError("Could not locate repository root")


class WorkspaceRunbookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = _repo_root()
        self.docs_root = self.repo_root / "docs" / "workspace"

    def test_operator_runbooks_follow_runbook_2_standard(self) -> None:
        for name in OPERATOR_RUNBOOKS:
            with self.subTest(runbook=name):
                text = (self.docs_root / name).read_text(encoding="utf-8")
                for heading in RUNBOOK_REQUIRED_HEADINGS:
                    self.assertIn(heading, text)
                self.assertIn(".\\scripts\\workspace.ps1", text)
                lower_text = text.lower()
                self.assertIn("expected output", lower_text)
                self.assertIn("human", lower_text)
                self.assertIn("external model apis", lower_text)

    def test_runbook_quality_checklist_is_packaged(self) -> None:
        checklist = (self.docs_root / "runbook-2.0-quality-checklist.md").read_text(encoding="utf-8")
        for heading in ("## Required Sections", "## Command Standard", "## Review Checklist", "## Maintenance"):
            self.assertIn(heading, checklist)
        self.assertIn("Windows PowerShell commands first", checklist)

    def test_workspace_docs_do_not_document_forbidden_actions(self) -> None:
        for path in sorted(self.docs_root.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            with self.subTest(doc=path.name):
                for snippet in FORBIDDEN_DOC_SNIPPETS:
                    self.assertNotIn(snippet, text)

    def test_pdf_export_includes_operator_runbooks(self) -> None:
        export_module = (
            self.repo_root / ".ai" / "skills" / "python" / "ai_workspace" / "docs" / "export_docs.py"
        ).read_text(encoding="utf-8")
        for name in (
            "developer-process-runbook.pdf",
            "knowledge-base-runbook.pdf",
            "azure-wiki-publication-runbook.pdf",
            "troubleshooting.pdf",
            "runbook-2.0-quality-checklist.pdf",
        ):
            with self.subTest(pdf=name):
                self.assertIn(name, export_module)


if __name__ == "__main__":
    unittest.main()
