from __future__ import annotations

import unittest
from pathlib import Path


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "AGENTS.md").exists():
            return candidate
    raise RuntimeError("Could not locate repository root")


class PromptInventoryTests(unittest.TestCase):
    def test_fetch_us_prompt_is_active_work_item_acquisition_step(self) -> None:
        repo_root = _repo_root()
        prompt = (repo_root / ".github" / "prompts" / "fetch-us.prompt.md").read_text(encoding="utf-8")
        inventory = (repo_root / ".ai" / "outputs" / "workspace-validation" / "prompt-inventory.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("ado-remote-mcp", prompt)
        self.assertIn("ado-work-item.json", prompt)
        self.assertIn("acceptance-criteria.md", prompt)
        self.assertIn("Do not create, update", prompt)
        self.assertIn("fetch-us", inventory)
        self.assertIn("Work Item acquisition", inventory)


if __name__ == "__main__":
    unittest.main()
