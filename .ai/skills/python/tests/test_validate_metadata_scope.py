from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_workspace.deployment.validate_metadata_scope import (
    load_metadata_scope,
    validate_changed_files_against_scope,
)


class ValidateMetadataScopeTests(unittest.TestCase):
    def test_allowed_paths_allow_matching_force_app_files(self) -> None:
        findings = validate_changed_files_against_scope(
            ["force-app/main/default/classes/Allowed.cls"],
            {"allowed_paths": ["force-app/main/default/classes"]},
        )

        self.assertEqual(findings, [])

    def test_blocked_paths_produce_blocking_findings(self) -> None:
        findings = validate_changed_files_against_scope(
            ["force-app/main/default/profiles/Admin.profile-meta.xml"],
            {"blocked_paths": ["force-app/main/default/profiles"]},
        )

        self.assertEqual(findings[0]["severity"], "blocking")
        self.assertEqual(findings[0]["type"], "blocked_metadata_path")

    def test_manual_review_paths_produce_medium_findings(self) -> None:
        findings = validate_changed_files_against_scope(
            ["force-app/main/default/flows/Important.flow-meta.xml"],
            {"requires_manual_review": ["force-app/main/default/flows"]},
        )

        self.assertEqual(findings[0]["severity"], "medium")
        self.assertEqual(findings[0]["type"], "manual_review_metadata_path")

    def test_missing_scope_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            scope = load_metadata_scope(str(Path(temp_dir) / "metadata-scope.yaml"))
            findings = validate_changed_files_against_scope(["force-app/main/default/classes/Foo.cls"], scope)

        self.assertEqual(findings[0]["severity"], "medium")
        self.assertEqual(findings[0]["type"], "metadata_scope_missing")


if __name__ == "__main__":
    unittest.main()
