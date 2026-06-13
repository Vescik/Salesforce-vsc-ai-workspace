from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from ai_workspace.knowledge.push_knowledge import push_knowledge


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True)


def _make_bare_remote(path: Path) -> None:
    path.mkdir(parents=True)
    _git(["init", "--bare"], path)


def _make_vendor_clone(remote: Path, vendor_dir: Path, branch: str = "main") -> None:
    """Clone bare remote into vendor_dir and set up an initial commit."""
    vendor_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", str(remote), str(vendor_dir)],
        check=True, text=True, capture_output=True,
    )
    _git(["config", "user.email", "test@example.com"], vendor_dir)
    _git(["config", "user.name", "Test"], vendor_dir)
    # Create initial commit so the branch exists on remote
    (vendor_dir / "README.md").write_text("# KB\n")
    _git(["add", "README.md"], vendor_dir)
    _git(["commit", "-m", "init"], vendor_dir)
    _git(["push", "origin", branch], vendor_dir)


def _write_note(knowledge_root: Path, domain: str, slug: str, content: str) -> Path:
    note_dir = knowledge_root / "domains" / domain
    note_dir.mkdir(parents=True, exist_ok=True)
    note_path = note_dir / f"{slug}.md"
    note_path.write_text(content)
    return note_path


SAMPLE_NOTE = """---
title: "Test Note"
domain: "billing"
owner: "Platform Team"
status: "reviewed"
confidence: "high"
last_reviewed: "2026-06-01"
keywords:
  - "test"
---

# Summary

Test knowledge note content.
"""


@unittest.skipIf(shutil.which("git") is None, "git is not available")
class PushKnowledgeTests(unittest.TestCase):

    def test_dry_run_lists_changed_files_without_committing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote = root / "remote.git"
            vendor_dir = root / "vendor"
            knowledge_root = root / "knowledge"

            _make_bare_remote(remote)
            _make_vendor_clone(remote, vendor_dir)
            _write_note(knowledge_root, "billing", "invoice-rules", SAMPLE_NOTE)

            report = push_knowledge(
                vendor_dir=vendor_dir,
                knowledge_root=knowledge_root,
                repo_url="",
                branch="main",
                message="",
                dry_run=True,
                do_push=False,
                repo_root=root,
            )

            self.assertTrue(report["dry_run"])
            self.assertIn("domains/billing/invoice-rules.md", report["changed_files"])
            self.assertIsNone(report["commit"])
            # Vendor clone must NOT have the file (dry-run = no copy)
            self.assertFalse((vendor_dir / "domains" / "billing" / "invoice-rules.md").exists())

    def test_commit_without_push_flag_stays_local(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote = root / "remote.git"
            vendor_dir = root / "vendor"
            knowledge_root = root / "knowledge"

            _make_bare_remote(remote)
            _make_vendor_clone(remote, vendor_dir)
            _write_note(knowledge_root, "billing", "invoice-rules", SAMPLE_NOTE)

            report = push_knowledge(
                vendor_dir=vendor_dir,
                knowledge_root=knowledge_root,
                repo_url="",
                branch="main",
                message="Custom commit message",
                dry_run=False,
                do_push=False,
                repo_root=root,
            )

            self.assertFalse(report["dry_run"])
            self.assertFalse(report["pushed"])
            self.assertIsNotNone(report["commit"])
            self.assertIn("domains/billing/invoice-rules.md", report["changed_files"])
            # File must be committed in vendor clone
            self.assertTrue((vendor_dir / "domains" / "billing" / "invoice-rules.md").exists())
            # Remote (bare repo) must NOT yet have the new commit
            remote_log = subprocess.run(
                ["git", "log", "--oneline", "HEAD"],
                cwd=remote, capture_output=True, text=True,
            ).stdout
            self.assertNotIn("Custom commit message", remote_log)

    def test_push_flag_pushes_to_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote = root / "remote.git"
            vendor_dir = root / "vendor"
            knowledge_root = root / "knowledge"

            _make_bare_remote(remote)
            _make_vendor_clone(remote, vendor_dir)
            _write_note(knowledge_root, "billing", "invoice-rules", SAMPLE_NOTE)

            report = push_knowledge(
                vendor_dir=vendor_dir,
                knowledge_root=knowledge_root,
                repo_url="",
                branch="main",
                message="",
                dry_run=False,
                do_push=True,
                repo_root=root,
            )

            self.assertTrue(report["pushed"])
            self.assertIsNotNone(report["commit"])

            # Verify remote has the new commit by cloning it
            verify_dir = root / "verify"
            subprocess.run(
                ["git", "clone", str(remote), str(verify_dir)],
                check=True, capture_output=True,
            )
            self.assertTrue((verify_dir / "domains" / "billing" / "invoice-rules.md").exists())

    def test_skips_file_with_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote = root / "remote.git"
            vendor_dir = root / "vendor"
            knowledge_root = root / "knowledge"

            _make_bare_remote(remote)
            _make_vendor_clone(remote, vendor_dir)
            _write_note(
                knowledge_root, "general", "leaked",
                SAMPLE_NOTE + "\npassword=supersecret123\n",
            )

            report = push_knowledge(
                vendor_dir=vendor_dir,
                knowledge_root=knowledge_root,
                repo_url="",
                branch="main",
                message="",
                dry_run=False,
                do_push=False,
                repo_root=root,
            )

            self.assertEqual(len(report["changed_files"]), 0)
            self.assertEqual(len(report["skipped_files"]), 1)
            self.assertEqual(report["skipped_files"][0]["reason"], "possible_secret")
            self.assertTrue(len(report["warnings"]) >= 1)
            self.assertIsNone(report["commit"])

    def test_nothing_to_commit_when_files_identical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote = root / "remote.git"
            vendor_dir = root / "vendor"
            knowledge_root = root / "knowledge"

            _make_bare_remote(remote)
            _make_vendor_clone(remote, vendor_dir)

            # Write the same note to both knowledge root and vendor clone
            note_content = SAMPLE_NOTE
            _write_note(knowledge_root, "billing", "same-note", note_content)
            vendor_note = vendor_dir / "domains" / "billing" / "same-note.md"
            vendor_note.parent.mkdir(parents=True, exist_ok=True)
            vendor_note.write_text(note_content)

            report = push_knowledge(
                vendor_dir=vendor_dir,
                knowledge_root=knowledge_root,
                repo_url="",
                branch="main",
                message="",
                dry_run=False,
                do_push=False,
                repo_root=root,
            )

            self.assertEqual(report["changed_files"], [])
            self.assertIsNone(report["commit"])

    def test_vendor_clone_created_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote = root / "remote.git"
            vendor_dir = root / "vendor"  # does not exist yet
            knowledge_root = root / "knowledge"

            # Set up bare remote with an initial commit
            _make_bare_remote(remote)
            init_clone = root / "init-clone"
            _make_vendor_clone(remote, init_clone)
            # Now vendor_dir doesn't exist — pass repo_url so it gets cloned

            _write_note(knowledge_root, "general", "new-note", SAMPLE_NOTE)

            report = push_knowledge(
                vendor_dir=vendor_dir,
                knowledge_root=knowledge_root,
                repo_url=str(remote),
                branch="main",
                message="",
                dry_run=False,
                do_push=False,
                repo_root=root,
            )

            self.assertTrue(vendor_dir.exists())
            self.assertTrue((vendor_dir / ".git").exists())
            self.assertIn("domains/general/new-note.md", report["changed_files"])
