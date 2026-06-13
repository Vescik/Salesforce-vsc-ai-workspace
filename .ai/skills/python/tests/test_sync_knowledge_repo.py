from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from ai_workspace.knowledge.sync_knowledge_repo import sync_knowledge_repo


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True)


@unittest.skipIf(shutil.which("git") is None, "git is not available")
class SyncKnowledgeRepoTests(unittest.TestCase):
    def test_sync_copies_curated_markdown_and_skips_raw_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            source_repo = temp_root / "kb-source"
            source_repo.mkdir()
            self._write_source_repo(source_repo)
            _git(["init"], source_repo)
            _git(["checkout", "-B", "main"], source_repo)
            _git(["config", "user.email", "test@example.com"], source_repo)
            _git(["config", "user.name", "Test User"], source_repo)
            _git(["add", "."], source_repo)
            _git(["commit", "-m", "Initial KB"], source_repo)

            workspace = temp_root / "workspace"
            vendor_dir = workspace / ".ai" / "vendor" / "knowledge-base"
            knowledge_root = workspace / ".ai" / "knowledge"
            policy_path = knowledge_root / "sync-policy.yaml"

            report = sync_knowledge_repo(
                repo_url=str(source_repo),
                branch="main",
                vendor_dir=vendor_dir,
                knowledge_root=knowledge_root,
                policy_path=policy_path,
                dry_run=False,
                clean=False,
                allow_imports=False,
                max_file_mb=None,
                repo_root=workspace,
            )

            self.assertFalse(report["failed"])
            self.assertTrue((knowledge_root / "domains" / "general" / "example.md").exists())
            self.assertTrue((knowledge_root / "README.md").exists())
            self.assertTrue((knowledge_root / "index.yaml").exists())
            self.assertFalse((knowledge_root / "imports" / "raw.md").exists())
            self.assertFalse((knowledge_root / "archive" / "old.md").exists())
            self.assertTrue((knowledge_root / "sync-state.json").exists())
            self.assertIn("domains/general/example.md", report["copied_files"])

    def test_sync_rejects_binary_in_included_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            source_repo = temp_root / "kb-source"
            source_repo.mkdir()
            self._write_source_repo(source_repo)
            binary = source_repo / "domains" / "general" / "binary.md"
            binary.write_bytes(b"hello\x00world")
            _git(["init"], source_repo)
            _git(["checkout", "-B", "main"], source_repo)
            _git(["config", "user.email", "test@example.com"], source_repo)
            _git(["config", "user.name", "Test User"], source_repo)
            _git(["add", "."], source_repo)
            _git(["commit", "-m", "Initial KB"], source_repo)

            workspace = temp_root / "workspace"
            knowledge_root = workspace / ".ai" / "knowledge"
            report = sync_knowledge_repo(
                repo_url=str(source_repo),
                branch="main",
                vendor_dir=workspace / ".ai" / "vendor" / "knowledge-base",
                knowledge_root=knowledge_root,
                policy_path=knowledge_root / "sync-policy.yaml",
                dry_run=False,
                clean=False,
                allow_imports=False,
                max_file_mb=None,
                repo_root=workspace,
            )

            skipped = {(item["path"], item["reason"]) for item in report["skipped_files"]}
            self.assertIn(("domains/general/binary.md", "binary_file"), skipped)
            self.assertFalse((knowledge_root / "domains" / "general" / "binary.md").exists())

    @staticmethod
    def _write_source_repo(source_repo: Path) -> None:
        (source_repo / "domains" / "general").mkdir(parents=True)
        (source_repo / "imports").mkdir()
        (source_repo / "archive").mkdir()
        (source_repo / "README.md").write_text("# Knowledge Base\n", encoding="utf-8")
        (source_repo / "index.yaml").write_text("version: 1\n", encoding="utf-8")
        (source_repo / "domains" / "general" / "example.md").write_text(
            """---
title: "Example"
domain: "general"
owner: "Salesforce Platform Team"
status: "approved"
confidence: "medium"
last_reviewed: "2026-01-01"
keywords:
  - "invoice"
---

# Example

Curated knowledge note.
""",
            encoding="utf-8",
        )
        (source_repo / "imports" / "raw.md").write_text("Raw import should not sync.\n", encoding="utf-8")
        (source_repo / "archive" / "old.md").write_text("Archived note should not sync.\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
