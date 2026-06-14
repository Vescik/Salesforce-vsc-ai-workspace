"""Primary CLI entry point for Knowledge Base Creator 2.0.

``import_knowledge`` remains as the backward-compatible module name used by
older prompts and tasks. New command surfaces should prefer this module.
"""

from __future__ import annotations

from ai_workspace.knowledge.import_knowledge import main


if __name__ == "__main__":
    raise SystemExit(main())
