from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_workspace.wiki.wiki_publisher import publish_wiki


class WikiPublisherSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        if not shutil.which("git"):
            self.skipTest("git is required for local wiki publisher tests")

    def test_dry_run_writes_preview_and_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._make_workspace_and_wiki(Path(temp_dir))
            args = self._args(paths, dry_run=True, module="invoicing_billing")

            with patch.dict(os.environ, {"AI_WORKSPACE_ROOT": str(paths["workspace"])}, clear=False):
                report = publish_wiki(args)

            self.assertEqual(report["status"], "DRY_RUN")
            self.assertEqual(report["target_wiki_path"], "/Invoicing/Invoice-Approval-Routing.md")
            self.assertTrue((paths["workspace"] / ".ai" / "outputs" / "wiki" / "preview" / "Invoicing" / "Invoice-Approval-Routing.md").exists())
            self.assertTrue((paths["workspace"] / ".ai" / "outputs" / "wiki" / "KIM-1234.wiki-publication-report.md").exists())

    def test_push_without_approval_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._make_workspace_and_wiki(Path(temp_dir), push_enabled=True)
            args = self._args(paths, prepare_branch=True, push=True, approved=False)

            with patch.dict(os.environ, {"AI_WORKSPACE_ROOT": str(paths["workspace"])}, clear=False):
                report = publish_wiki(args)

            self.assertEqual(report["status"], "BLOCKED")
            self.assertTrue(any("--push is blocked" in warning for warning in report["warnings"]))

    def test_push_is_blocked_when_local_config_disables_push(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._make_workspace_and_wiki(Path(temp_dir), push_enabled=False)
            args = self._args(paths, prepare_branch=True, push=True, approved=True, approval_note="QA approval")

            with patch.dict(os.environ, {"AI_WORKSPACE_ROOT": str(paths["workspace"])}, clear=False):
                report = publish_wiki(args)

            self.assertEqual(report["status"], "BLOCKED")
            self.assertTrue(any("push_enabled is false" in warning for warning in report["warnings"]))

    def test_default_branch_draft_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._make_workspace_and_wiki(Path(temp_dir), push_enabled=True)
            args = self._args(paths, prepare_branch=True, push=True, approved=True, approval_note="QA approval", draft_branch="main")

            with patch.dict(os.environ, {"AI_WORKSPACE_ROOT": str(paths["workspace"])}, clear=False):
                report = publish_wiki(args)

            self.assertEqual(report["status"], "BLOCKED")
            self.assertTrue(any("matches the wiki default/base branch" in warning for warning in report["warnings"]))

    def test_existing_page_produces_review_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = self._make_workspace_and_wiki(Path(temp_dir))
            args = self._args(paths, dry_run=True, target_path="/Invoicing/Overview.md")

            with patch.dict(os.environ, {"AI_WORKSPACE_ROOT": str(paths["workspace"])}, clear=False):
                report = publish_wiki(args)

            self.assertEqual(report["status"], "DRY_RUN")
            self.assertTrue(any("already exists" in warning for warning in report["warnings"]))
            self.assertTrue(report["existing_diff"])

    @staticmethod
    def _make_workspace_and_wiki(root: Path, push_enabled: bool = False) -> dict[str, Path]:
        workspace = root / "workspace"
        wiki = root / "fake-azure-wiki"
        workspace.mkdir()
        wiki.mkdir()
        (workspace / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
        (workspace / ".ai" / "config").mkdir(parents=True)
        (workspace / ".ai" / "wiki").mkdir(parents=True)
        (workspace / "docs" / "architecture").mkdir(parents=True)
        (workspace / "docs" / "architecture" / "KIM-1234.md").write_text(
            "# Invoice Approval Routing\n\nFunctional behavior for invoice approval and billing validation.\n",
            encoding="utf-8",
        )
        (workspace / ".ai" / "config" / "workspace.local.json").write_text(
            '{"version": 1, "azure_wiki": {"enabled": true, "branch": "main", "vendor_dir": ".ai/vendor/azure-wiki", "default_draft_branch_prefix": "docs/ai-wiki", "require_human_approval": true, "allow_direct_push_to_default_branch": false, "push_enabled": '
            + ("true" if push_enabled else "false")
            + "}}\n",
            encoding="utf-8",
        )
        (workspace / ".ai" / "wiki" / "wiki-publish-policy.yaml").write_text(
            "version: 1\n"
            "approval:\n"
            "  require_human_approval: true\n"
            "  allowed_publish_modes:\n"
            "    - \"dry_run\"\n"
            "    - \"prepare_branch\"\n"
            "    - \"push_branch_after_approval\"\n"
            "source_documents:\n"
            "  allowed_roots:\n"
            "    - \"docs/architecture\"\n"
            "  blocked_roots:\n"
            "    - \".ai/vendor\"\n"
            "wiki:\n"
            "  update_order_files: true\n"
            "safety:\n"
            "  scan_for_secrets: true\n"
            "  fail_on_secret_like_values: true\n"
            "  require_source_artifact_references: true\n",
            encoding="utf-8",
        )
        (workspace / ".ai" / "wiki" / "module-map.yaml").write_text(
            "version: 1\n"
            "modules:\n"
            "  invoicing_billing:\n"
            "    display_name: \"Invoicing / Billing\"\n"
            "    candidate_paths:\n"
            "      - \"/Invoicing\"\n"
            "    keywords:\n"
            "      - \"invoice\"\n"
            "      - \"billing\"\n"
            "fallback:\n"
            "  proposed_root: \"/_Proposed\"\n"
            "  unclassified_root: \"/_Unclassified\"\n",
            encoding="utf-8",
        )

        (wiki / "Invoicing").mkdir()
        (wiki / "Home.md").write_text("# Home\n", encoding="utf-8")
        (wiki / "Invoicing" / "Overview.md").write_text("# Invoicing\n\nExisting invoice approval docs.\n", encoding="utf-8")
        (wiki / "Invoicing" / ".order").write_text("Overview\n", encoding="utf-8")
        subprocess.run(["git", "init", "-b", "main"], cwd=wiki, check=True, text=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=wiki, check=True, text=True, capture_output=True)
        subprocess.run(
            ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.invalid", "commit", "-m", "Initial fake wiki"],
            cwd=wiki,
            check=True,
            text=True,
            capture_output=True,
        )
        return {"workspace": workspace, "wiki": wiki}

    @staticmethod
    def _args(
        paths: dict[str, Path],
        dry_run: bool = False,
        prepare_branch: bool = False,
        push: bool = False,
        approved: bool = False,
        approval_note: str = "",
        draft_branch: str = "",
        module: str = "",
        target_path: str = "",
    ) -> argparse.Namespace:
        workspace = paths["workspace"]
        return argparse.Namespace(
            work_item="KIM-1234",
            title="Invoice Approval Routing",
            source=["docs/architecture/KIM-1234.md"],
            repo_url=str(paths["wiki"]),
            branch="main",
            vendor_dir=str(workspace / ".ai" / "vendor" / "azure-wiki"),
            module=module,
            target_path=target_path,
            dry_run=dry_run,
            prepare_branch=prepare_branch,
            push=push,
            approved=approved,
            approval_note=approval_note,
            draft_branch=draft_branch,
            out_dir=str(workspace / ".ai" / "outputs" / "wiki"),
            config=str(workspace / ".ai" / "config" / "workspace.local.json"),
            policy=str(workspace / ".ai" / "wiki" / "wiki-publish-policy.yaml"),
            module_map=str(workspace / ".ai" / "wiki" / "module-map.yaml"),
        )


if __name__ == "__main__":
    unittest.main()
