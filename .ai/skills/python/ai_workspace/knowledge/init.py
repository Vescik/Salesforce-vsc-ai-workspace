"""Initialize local knowledge-base folders."""

from __future__ import annotations

from pathlib import Path


KNOWLEDGE_DIRS = (
    ".ai/knowledge/domains",
    ".ai/knowledge/object-notes",
    ".ai/knowledge/process-maps",
    ".ai/knowledge/decisions",
    ".ai/knowledge/governance",
    ".ai/knowledge/imports",
    ".ai/knowledge/archive",
)


def ensure_knowledge_dirs(repo_root: Path | str = ".") -> list[Path]:
    """Create the baseline local knowledge-base directories."""

    root = Path(repo_root)
    created: list[Path] = []
    for relative in KNOWLEDGE_DIRS:
        path = root / relative
        path.mkdir(parents=True, exist_ok=True)
        gitkeep = path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("", encoding="utf-8")
        created.append(path)
    return created


def main() -> int:
    for path in ensure_knowledge_dirs():
        print(path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
