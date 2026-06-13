from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_workspace.wiki.wiki_page_builder import build_wiki_page


POLICY = {
    "approval": {"require_human_approval": True},
    "source_documents": {
        "allowed_roots": ["docs/architecture", "docs/qa-how-to-test", "specs/proposed", ".ai/context/work-items"],
        "blocked_roots": [".ai/vendor", ".env", ".sf", ".sfdx"],
    },
    "safety": {
        "scan_for_secrets": True,
        "fail_on_secret_like_values": True,
        "require_source_artifact_references": True,
    },
}


class WikiPageBuilderTests(unittest.TestCase):
    def test_page_includes_source_artifacts_and_review_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            source = repo / "docs" / "architecture" / "KIM-1234.md"
            source.parent.mkdir(parents=True)
            source.write_text(
                "# Invoice Approval Routing\n\nFunctional behavior for Account and Invoice_Setting__mdt.\n\n## QA Notes\n\nValidate approval.",
                encoding="utf-8",
            )

            result = build_wiki_page(
                source_paths=["docs/architecture/KIM-1234.md"],
                repo_root=repo,
                policy=POLICY,
                work_item="KIM-1234",
                title="Invoice Approval Routing",
                routing_decision={"target_wiki_path": "/Invoicing/Invoice-Approval-Routing.md", "confidence": "high"},
            )

        markdown = result["markdown"]
        self.assertFalse(result["blocked"])
        self.assertIn("AI-assisted draft prepared for Azure DevOps Wiki", markdown)
        self.assertIn("docs/architecture/KIM-1234.md", markdown)
        self.assertIn("Requires human review", markdown)
        self.assertIn("Invoice_Setting__mdt", markdown)

    def test_secret_like_source_blocks_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            source = repo / "docs" / "architecture" / "KIM-1234.md"
            source.parent.mkdir(parents=True)
            source.write_text("client" + "_secret = should-not-be-here", encoding="utf-8")

            result = build_wiki_page(
                source_paths=["docs/architecture/KIM-1234.md"],
                repo_root=repo,
                policy=POLICY,
                work_item="KIM-1234",
                title="Unsafe Draft",
                routing_decision={"target_wiki_path": "/_Unclassified/Unsafe-Draft.md", "confidence": "low"},
            )

        self.assertTrue(result["blocked"])
        self.assertTrue(any("Secret-like" in warning for warning in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
