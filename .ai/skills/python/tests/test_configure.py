from __future__ import annotations

import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from ai_workspace.configuration.workspace_config import DEFAULT_CONFIG
from scripts import configure


class ConfigureTests(unittest.TestCase):
    def test_non_interactive_configure_writes_all_oobt_values_and_patches_mcp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self._make_repo(repo_root)
            config_path = repo_root / ".ai" / "config" / "workspace.local.json"

            stdout = StringIO()
            with patch.dict(os.environ, {"AI_WORKSPACE_ROOT": str(repo_root)}, clear=False), redirect_stdout(stdout):
                result = configure.main(
                    [
                        "--config",
                        config_path.as_posix(),
                        "--non-interactive",
                        "--overwrite",
                        "--dev-org",
                        "DevSandbox",
                        "--validation-org",
                        "ValidateSandbox",
                        "--kb-repo",
                        "git@example.com:team/kb.git",
                        "--kb-branch",
                        "kb-main",
                        "--ado-org",
                        "configured-org",
                        "--ado-project",
                        "Configured Project",
                        "--azure-wiki-repo",
                        "https://dev.azure.com/org/project/_git/project.wiki",
                        "--azure-wiki-branch",
                        "wiki-main",
                        "--azure-wiki-vendor-dir",
                        ".ai/vendor/wiki-configured",
                        "--enable-wiki-push",
                    ]
                )

            output = stdout.getvalue()
            config = json.loads(config_path.read_text(encoding="utf-8"))
            mcp = json.loads((repo_root / ".vscode" / "mcp.json").read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertIn(".\\scripts\\workspace.ps1 knowledge-sync", output)
        self.assertNotIn("knowledge-sync -KbRepo", output)
        self.assertIn(".\\scripts\\workspace.ps1 wiki-dry-run", output)
        self.assertNotIn("-AzureWikiRepo", output)
        self.assertEqual(config["salesforce"]["default_dev_org_alias"], "DevSandbox")
        self.assertEqual(config["salesforce"]["validation_org_alias"], "ValidateSandbox")
        self.assertTrue(config["knowledge_base"]["enabled"])
        self.assertEqual(config["knowledge_base"]["repo_url"], "git@example.com:team/kb.git")
        self.assertEqual(config["knowledge_base"]["branch"], "kb-main")
        self.assertTrue(config["azure_devops"]["enabled"])
        self.assertEqual(config["azure_devops"]["organization"], "configured-org")
        self.assertEqual(config["azure_devops"]["default_project"], "Configured Project")
        self.assertTrue(config["azure_wiki"]["enabled"])
        self.assertEqual(config["azure_wiki"]["repo_url"], "https://dev.azure.com/org/project/_git/project.wiki")
        self.assertEqual(config["azure_wiki"]["branch"], "wiki-main")
        self.assertEqual(config["azure_wiki"]["vendor_dir"], ".ai/vendor/wiki-configured")
        self.assertTrue(config["azure_wiki"]["push_enabled"])
        self.assertEqual(mcp["servers"]["ado-remote-mcp"]["url"], "https://mcp.dev.azure.com/configured-org")
        self.assertIn("salesforce-context", mcp["servers"])

    def test_patch_mcp_json_updates_existing_org_url_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / ".vscode").mkdir(parents=True)
            mcp_path = repo_root / ".vscode" / "mcp.json"
            mcp_path.write_text(
                json.dumps(
                    {
                        "servers": {
                            "ado-remote-mcp": {"type": "http", "url": "https://mcp.dev.azure.com/old-org"},
                            "salesforce-context": {"type": "stdio", "command": "python"},
                        }
                    }
                ),
                encoding="utf-8",
            )

            configure._patch_mcp_json(repo_root, "new-org")
            first = mcp_path.read_text(encoding="utf-8")
            configure._patch_mcp_json(repo_root, "new-org")
            second = mcp_path.read_text(encoding="utf-8")
            loaded = json.loads(second)

        self.assertEqual(first, second)
        self.assertEqual(loaded["servers"]["ado-remote-mcp"]["url"], "https://mcp.dev.azure.com/new-org")
        self.assertEqual(loaded["servers"]["salesforce-context"]["command"], "python")

    @staticmethod
    def _make_repo(repo_root: Path) -> None:
        (repo_root / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
        config_dir = repo_root / ".ai" / "config"
        config_dir.mkdir(parents=True)
        (config_dir / "workspace.local.json.example").write_text(json.dumps(DEFAULT_CONFIG), encoding="utf-8")
        (repo_root / ".vscode").mkdir(parents=True)
        (repo_root / ".vscode" / "mcp.json").write_text(
            json.dumps(
                {
                    "servers": {
                        "ado-remote-mcp": {"type": "http", "url": "https://mcp.dev.azure.com/old-org"},
                        "salesforce-context": {"type": "stdio", "command": "python"},
                    }
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
