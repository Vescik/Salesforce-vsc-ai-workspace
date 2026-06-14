from __future__ import annotations

import unittest
from pathlib import Path


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "AGENTS.md").exists():
            return candidate
    raise RuntimeError("Could not locate repository root")


class WindowsWrapperConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = _repo_root()
        self.script = (self.repo_root / "scripts" / "workspace.ps1").read_text(encoding="utf-8")

    def test_configure_uses_selected_workspace_config_path(self) -> None:
        self.assertIn('"scripts/configure.py" `', self.script)
        self.assertIn("--config $WorkspaceConfig", self.script)

    def test_config_env_defaults_feed_kb_and_wiki_commands(self) -> None:
        for snippet in (
            '$KbRepo = Resolve-Setting $KbRepo "KB_REPO" @("knowledge_base", "repo_url") ""',
            '$KbBranch = Resolve-Setting $KbBranch "KB_BRANCH" @("knowledge_base", "branch") "main"',
            '$KbVendorDir = Resolve-Setting $KbVendorDir "" @("paths", "knowledge_vendor_dir") ".ai/vendor/knowledge-base"',
            '$KnowledgeRoot = Resolve-Setting $KnowledgeRoot "" @("paths", "knowledge_root") ".ai/knowledge"',
            '$AzureWikiRepo = Resolve-Setting $AzureWikiRepo "AZURE_WIKI_REPO" @("azure_wiki", "repo_url") ""',
            '$AzureWikiBranch = Resolve-Setting $AzureWikiBranch "AZURE_WIKI_BRANCH" @("azure_wiki", "branch") "main"',
            '$AzureWikiVendorDir = Resolve-Setting $AzureWikiVendorDir "AZURE_WIKI_VENDOR_DIR" @("azure_wiki", "vendor_dir") ".ai/vendor/azure-wiki"',
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, self.script)

    def test_examples_do_not_hardcode_repository_urls(self) -> None:
        self.assertNotIn("https://github.com/Vescik/Salesforce-knowledge-base.git", self.script)
        self.assertNotIn("https://dev.azure.com/ORG/PROJECT/_git/PROJECT.wiki", self.script)


if __name__ == "__main__":
    unittest.main()
