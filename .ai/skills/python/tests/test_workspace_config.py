from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_workspace.configuration.workspace_config import (
    DEFAULT_CONFIG,
    ensure_required_dirs,
    get_salesforce_alias,
    load_workspace_config,
    validate_workspace_config,
)


class WorkspaceConfigTests(unittest.TestCase):
    def test_load_config_and_env_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
            config_path = repo_root / ".ai" / "config" / "workspace.local.json"
            config_path.parent.mkdir(parents=True)
            config = json.loads(json.dumps(DEFAULT_CONFIG))
            config["salesforce"]["default_dev_org_alias"] = "Original"
            config["knowledge_base"]["branch"] = "main"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with patch.dict(
                os.environ,
                {
                    "AI_WORKSPACE_ROOT": str(repo_root),
                    "SF_DEV_ORG_ALIAS": "IntDevLocal",
                    "KB_REPO": "git@example.com:company/kb.git",
                    "KB_BRANCH": "develop",
                    "ADO_ORG": "example-org",
                    "ADO_PROJECT": "Example Project",
                    "AZURE_WIKI_REPO": "git@example.com:project/wiki.git",
                    "AZURE_WIKI_BRANCH": "wikiMain",
                    "AZURE_WIKI_VENDOR_DIR": ".ai/vendor/custom-wiki",
                },
                clear=False,
            ):
                loaded = load_workspace_config(config_path)

        self.assertEqual(get_salesforce_alias(loaded), "IntDevLocal")
        self.assertTrue(loaded["knowledge_base"]["enabled"])
        self.assertEqual(loaded["knowledge_base"]["repo_url"], "git@example.com:company/kb.git")
        self.assertEqual(loaded["knowledge_base"]["branch"], "develop")
        self.assertTrue(loaded["azure_devops"]["enabled"])
        self.assertEqual(loaded["azure_devops"]["organization"], "example-org")
        self.assertEqual(loaded["azure_devops"]["default_project"], "Example Project")
        self.assertEqual(loaded["azure_devops"]["mcp_server_name"], "ado-remote-mcp")
        self.assertTrue(loaded["azure_wiki"]["enabled"])
        self.assertEqual(loaded["azure_wiki"]["repo_url"], "git@example.com:project/wiki.git")
        self.assertEqual(loaded["azure_wiki"]["branch"], "wikiMain")
        self.assertEqual(loaded["azure_wiki"]["vendor_dir"], ".ai/vendor/custom-wiki")

    def test_ensure_required_dirs_creates_expected_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
            with patch.dict(os.environ, {"AI_WORKSPACE_ROOT": str(repo_root)}, clear=False):
                config = load_workspace_config(repo_root / ".ai" / "config" / "missing.json")
                created = ensure_required_dirs(config)

            self.assertIn(".ai/context/index", created)
            self.assertTrue((repo_root / ".ai" / "context" / "index").is_dir())
            self.assertTrue((repo_root / "docs" / "qa-how-to-test").is_dir())

    def test_forbidden_security_flags_are_errors(self) -> None:
        config = json.loads(json.dumps(DEFAULT_CONFIG))
        config["security"]["allow_salesforce_writes"] = True

        errors, _warnings = validate_workspace_config(config)

        self.assertTrue(any("allow_salesforce_writes" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
