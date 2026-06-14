from __future__ import annotations

import unittest
from pathlib import Path


VALID_PROMPT_MODES = {"agent", "ask", "edit"}


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "AGENTS.md").exists():
            return candidate
    raise RuntimeError("Could not locate repository root")


def _front_matter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    values: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            return values
        if not stripped or stripped.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


class PromptInventoryTests(unittest.TestCase):
    def test_agents_have_required_front_matter(self) -> None:
        repo_root = _repo_root()
        agent_paths = sorted((repo_root / ".github" / "agents").glob("*.agent.md"))

        self.assertGreater(len(agent_paths), 0)
        for agent_path in agent_paths:
            with self.subTest(agent=agent_path.name):
                front_matter = _front_matter(agent_path)
                self.assertTrue(front_matter.get("name"), "agent front matter must include name")
                self.assertTrue(front_matter.get("description"), "agent front matter must include description")

    def test_prompts_have_names_and_valid_agent_references(self) -> None:
        repo_root = _repo_root()
        prompt_paths = sorted((repo_root / ".github" / "prompts").glob("*.prompt.md"))
        agent_names = {
            path.name.removesuffix(".agent.md") for path in (repo_root / ".github" / "agents").glob("*.agent.md")
        }

        self.assertGreater(len(prompt_paths), 0)
        self.assertGreater(len(agent_names), 0)
        for prompt_path in prompt_paths:
            expected_name = prompt_path.name.removesuffix(".prompt.md")
            with self.subTest(prompt=prompt_path.name):
                front_matter = _front_matter(prompt_path)
                self.assertEqual(front_matter.get("name"), expected_name)
                self.assertTrue(front_matter.get("description"), "prompt front matter must include description")
                self.assertIn("agent", front_matter, "prompt front matter must include agent")
                self.assertIn(front_matter["agent"], agent_names)
                if "mode" in front_matter:
                    self.assertIn(front_matter["mode"], VALID_PROMPT_MODES)

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
