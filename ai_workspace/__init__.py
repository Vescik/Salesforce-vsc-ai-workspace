"""Import shim for the local AI workspace tools.

The implementation package lives under ``.ai/skills/python`` so it can remain
with the rest of the AI workspace assets. This shim lets the documented command
``python -m ai_workspace...`` run from the repository root without installing a
package or adding dependencies.
"""

from pathlib import Path

_IMPLEMENTATION_PACKAGE = (
    Path(__file__).resolve().parent.parent
    / ".ai"
    / "skills"
    / "python"
    / "ai_workspace"
)

__path__ = [str(_IMPLEMENTATION_PACKAGE)]
