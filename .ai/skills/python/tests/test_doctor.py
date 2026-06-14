from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_workspace.configuration.doctor import run_doctor
from ai_workspace.configuration.workspace_config import DEFAULT_CONFIG


class DoctorTests(unittest.TestCase):
    def test_doctor_warns_when_salesforce_cli_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._make_repo(repo_root)
            config_path = repo_root / ".ai" / "config" / "workspace.local.json"
            config_path.write_text(json.dumps(DEFAULT_CONFIG), encoding="utf-8")

            def fake_which(command: str) -> str | None:
                if command == "sf":
                    return None
                if command == "git":
                    return "/usr/bin/git"
                return None

            with patch.dict(os.environ, {"AI_WORKSPACE_ROOT": str(repo_root)}, clear=False), patch(
                "ai_workspace.configuration.doctor.shutil.which", side_effect=fake_which
            ):
                report = run_doctor(config_path=config_path)

        self.assertEqual(report["summary"]["status"], "PASS_WITH_WARNINGS")
        self.assertTrue(any(check["category"] == "salesforce_cli" and check["status"] == "WARN" for check in report["checks"]))

    def test_doctor_fails_for_forbidden_security_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._make_repo(repo_root)
            config = json.loads(json.dumps(DEFAULT_CONFIG))
            config["security"]["allow_config_apply"] = True
            config_path = repo_root / ".ai" / "config" / "workspace.local.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with patch.dict(os.environ, {"AI_WORKSPACE_ROOT": str(repo_root)}, clear=False), patch(
                "ai_workspace.configuration.doctor.shutil.which", return_value="/usr/bin/tool"
            ):
                report = run_doctor(config_path=config_path)

        self.assertEqual(report["summary"]["status"], "FAIL")
        self.assertTrue(any("allow_config_apply" in check["name"] for check in report["checks"]))

    def test_doctor_warns_when_ado_org_placeholder_remains(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._make_repo(repo_root)
            (repo_root / ".vscode" / "mcp.json").write_text(
                json.dumps(
                    {
                        "servers": {
                            "salesforce-context": {"type": "stdio", "command": "python", "args": []},
                            "ado-remote-mcp": {"type": "http", "url": "https://mcp.dev.azure.com/YOUR_ADO_ORG"},
                        }
                    }
                ),
                encoding="utf-8",
            )
            config_path = repo_root / ".ai" / "config" / "workspace.local.json"
            config_path.write_text(json.dumps(DEFAULT_CONFIG), encoding="utf-8")

            with patch.dict(os.environ, {"AI_WORKSPACE_ROOT": str(repo_root)}, clear=False), patch(
                "ai_workspace.configuration.doctor.shutil.which", return_value="/usr/bin/tool"
            ):
                report = run_doctor(config_path=config_path)

        self.assertEqual(report["summary"]["status"], "PASS_WITH_WARNINGS")
        self.assertTrue(
            any(
                check["category"] == "azure_devops"
                and check["name"] == "Azure DevOps organization"
                and check["status"] == "WARN"
                for check in report["checks"]
            )
        )

    @staticmethod
    def _make_repo(repo_root: Path) -> None:
        for relative in (
            ".ai/config",
            ".ai/context/index",
            ".ai/context/work-items",
            ".ai/outputs",
            ".ai/knowledge",
            ".vscode",
            ".github",
            "specs/proposed",
            "specs/approved",
            "docs/architecture",
            "docs/qa-how-to-test",
        ):
            (repo_root / relative).mkdir(parents=True, exist_ok=True)
        (repo_root / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
        (repo_root / "scripts").mkdir(parents=True, exist_ok=True)
        (repo_root / "scripts" / "workspace.ps1").write_text("param([string]$Target)\n", encoding="utf-8")
        (repo_root / ".vscode" / "tasks.json").write_text("{}", encoding="utf-8")
        (repo_root / ".github" / "copilot-instructions.md").write_text("# Instructions\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
