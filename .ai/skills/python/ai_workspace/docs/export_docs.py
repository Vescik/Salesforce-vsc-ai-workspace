"""Validate workspace docs and export PDFs when local tools are available."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


DOCS_ROOT = Path("docs/workspace")
PDF_ROOT = DOCS_ROOT / "pdf"
HTML_RUNBOOK = DOCS_ROOT / "html" / "index.html"
PDF_SOURCES = [
    ("installation-guide.md", "installation-guide.pdf"),
    ("workspace-overview-nontechnical.md", "workspace-overview-nontechnical.pdf"),
    ("workspace-architecture-technical.md", "workspace-architecture-technical.pdf"),
    ("agents-prompts-skills-mcp-reference.md", "agents-prompts-skills-mcp-reference.pdf"),
    ("developer-process-runbook.md", "developer-process-runbook.pdf"),
    ("knowledge-base-runbook.md", "knowledge-base-runbook.pdf"),
    ("azure-wiki-publication-runbook.md", "azure-wiki-publication-runbook.pdf"),
    ("troubleshooting.md", "troubleshooting.pdf"),
    ("runbook-2.0-quality-checklist.md", "runbook-2.0-quality-checklist.pdf"),
]
REQUIRED_DOCS = [
    "README.md",
    "installation-guide.md",
    "workspace-overview-nontechnical.md",
    "workspace-architecture-technical.md",
    "agents-prompts-skills-mcp-reference.md",
    "developer-process-runbook.md",
    "knowledge-base-runbook.md",
    "azure-wiki-publication-runbook.md",
    "runbook-2.0-quality-checklist.md",
    "security-and-governance.md",
    "troubleshooting.md",
    "appendix-command-reference.md",
    "html/index.html",
    "html/assets/styles.css",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate docs package and export PDFs if local tools exist.")
    parser.add_argument("--check", action="store_true", help="Only validate that required documentation files exist.")
    args = parser.parse_args(argv)

    missing = [path for path in REQUIRED_DOCS if not (DOCS_ROOT / path).exists()]
    if missing:
        for path in missing:
            print(f"ERROR: missing docs/workspace/{path}", file=sys.stderr)
        return 1

    PDF_ROOT.mkdir(parents=True, exist_ok=True)
    if args.check:
        print(f"Workspace docs package found at {DOCS_ROOT.as_posix()}")
        print(f"HTML runbook: {HTML_RUNBOOK.as_posix()}")
        return 0

    pandoc = shutil.which("pandoc")
    if pandoc:
        return _export_with_pandoc(pandoc)

    _write_manual_pdf_readme()
    print("PDF export tools not found. Wrote manual PDF export instructions.")
    print("Checked for: pandoc, weasyprint, wkhtmltopdf.")
    return 0


def _export_with_pandoc(pandoc: str) -> int:
    failures: list[str] = []
    for source_name, output_name in PDF_SOURCES:
        source = DOCS_ROOT / source_name
        output = PDF_ROOT / output_name
        command = [pandoc, source.as_posix(), "-o", output.as_posix()]
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        if result.returncode:
            failures.append(f"{source_name}: {result.stderr.strip() or result.stdout.strip()}")
        else:
            print(f"Wrote {output.as_posix()}")

    if failures:
        _write_manual_pdf_readme()
        for failure in failures:
            print(f"WARNING: {failure}", file=sys.stderr)
        return 0
    return 0


def _write_manual_pdf_readme() -> None:
    PDF_ROOT.mkdir(parents=True, exist_ok=True)
    (PDF_ROOT / "README.md").write_text(
        """# PDF Export Instructions

No local PDF export tool was detected when `.\scripts\workspace.ps1 docs-export-pdf` was run.

Manual options:

- Install Pandoc and a PDF engine, then run `.\scripts\workspace.ps1 docs-export-pdf`.
- Use a VS Code Markdown PDF extension on the Markdown files in `docs/workspace/`.
- Open `docs/workspace/html/index.html` in a browser and use Print to PDF.

Expected PDF outputs when tooling is available:

- `installation-guide.pdf`
- `workspace-overview-nontechnical.pdf`
- `workspace-architecture-technical.pdf`
- `agents-prompts-skills-mcp-reference.pdf`
- `developer-process-runbook.pdf`
- `knowledge-base-runbook.pdf`
- `azure-wiki-publication-runbook.pdf`
- `troubleshooting.pdf`
- `runbook-2.0-quality-checklist.pdf`
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
