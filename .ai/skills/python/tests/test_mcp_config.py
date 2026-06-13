from __future__ import annotations

import json
import unittest
from pathlib import Path


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "AGENTS.md").exists():
            return candidate
    raise RuntimeError("Could not locate repository root")


class MCPConfigTests(unittest.TestCase):
    def test_vscode_mcp_json_includes_salesforce_and_ado_servers(self) -> None:
        mcp_path = _repo_root() / ".vscode" / "mcp.json"
        config = json.loads(mcp_path.read_text(encoding="utf-8"))

        servers = config.get("servers")
        self.assertIsInstance(servers, dict)
        self.assertIn("salesforce-context", servers)
        self.assertIn("ado-remote-mcp", servers)

        ado = servers["ado-remote-mcp"]
        self.assertEqual(ado.get("type"), "http")
        self.assertEqual(ado.get("url"), "https://mcp.dev.azure.com/YOUR_ADO_ORG")


if __name__ == "__main__":
    unittest.main()
