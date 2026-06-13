from __future__ import annotations

import argparse
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_workspace.configuration.bootstrap import bootstrap_workspace
from ai_workspace.configuration.workspace_config import DEFAULT_CONFIG


class BootstrapTests(unittest.TestCase):
    def test_bootstrap_creates_local_config_and_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
            template = repo_root / ".ai" / "config" / "workspace.local.json.example"
            template.parent.mkdir(parents=True)
            template.write_text(json.dumps(DEFAULT_CONFIG), encoding="utf-8")
            args = argparse.Namespace(
                config=".ai/config/workspace.local.json",
                create_local_config=True,
                overwrite_config=False,
                create_venv=False,
                install_dev_deps=False,
                skip_venv=True,
                skip_python_install=True,
                skip_knowledge_sync=True,
                non_interactive=True,
                print_next_steps=False,
            )

            with patch.dict(os.environ, {"AI_WORKSPACE_ROOT": str(repo_root)}, clear=False):
                report = bootstrap_workspace(args)

            self.assertFalse(report["errors"])
            self.assertTrue((repo_root / ".ai" / "config" / "workspace.local.json").exists())
            self.assertTrue((repo_root / ".ai" / "context" / "index").is_dir())
            self.assertTrue((repo_root / "specs" / "proposed").is_dir())


if __name__ == "__main__":
    unittest.main()
