# Installation Guide

Audience: Salesforce developers, technical consultants, and new employees setting up the Copilot-only Salesforce AI Workspace.

## Purpose

This workspace provides local, deterministic support for Salesforce work on top of the closed KimbleOne/Kantata managed package. It helps developers gather context, create solution designs, generate documentation and QA how-to-test drafts, review config impact, and run prechecks.

It does not deploy metadata, apply configuration records, write Salesforce data, replace DevOps Center, or integrate external LLM APIs.

## Prerequisites

Required:

- Git.
- Python 3.11 or newer.
- Salesforce CLI `sf`.
- VS Code.
- GitHub Copilot access.

Recommended:

- `make` for the documented commands.
- GitHub CLI `gh` for future repository publishing tasks.
- Azure DevOps access if Work Item MCP or Azure Wiki Git repos are used.
- Access to the private Knowledge Base Git repository if your team uses it.

Optional:

- Pandoc with a PDF engine, WeasyPrint, or wkhtmltopdf for local PDF export. If these are missing, the workspace still works and writes manual PDF export instructions.

Windows notes:

- If `make` is unavailable, use `python scripts/setup.py`, `python scripts/configure.py`, and `python scripts/doctor.py`.
- PowerShell wrappers exist under `scripts/`.

## Clone The Repository

```bash
git clone <main-workspace-repo-url>
cd <repo-folder>
```

Use the project repository provided by the team. Do not clone a Full Copy org export and treat it as source of truth.

## Run Setup

```bash
make setup
```

This creates local workspace folders and a local config file if needed. It does not install external model SDKs and does not call Salesforce.

## Configure Local Values

```bash
make configure
```

The ignored local config file is:

```text
.ai/config/workspace.local.json
```

Never commit this file. It can contain local org aliases and local repository URLs, but it must not contain tokens, passwords, private keys, or employee credentials.

Typical local config shape:

```json
{
  "salesforce": {
    "default_dev_org_alias": "IntDev",
    "validation_org_alias": ""
  },
  "knowledge_base": {
    "enabled": true,
    "repo_url": "git@github.com:<ORG>/<KB_REPO>.git",
    "branch": "main",
    "sync_on_setup": false
  },
  "azure_wiki": {
    "enabled": false,
    "repo_url": "",
    "branch": "main"
  }
}
```

## Authenticate Salesforce CLI

Authenticate with Salesforce CLI, not workspace config:

```bash
sf org login web --alias IntDev
```

Optional validation org aliases can be configured locally when validation-only workflows are approved. Salesforce tokens remain in Salesforce CLI local auth storage, not in this repository.

## Run Doctor

```bash
make doctor
```

Doctor checks local prerequisites, config shape, safe settings, and common workspace paths. Warnings for placeholder Azure DevOps values are expected until local setup is completed.

Strict doctor can check optional org auth and Knowledge Base readiness:

```bash
make doctor-strict
```

## Knowledge Base Setup

If your team uses the separate private Knowledge Base repository:

```bash
make knowledge-sync KB_REPO=git@github.com:<ORG>/<KB_REPO>.git
make knowledge-index
```

Use a dry run first when testing access:

```bash
make knowledge-sync-dry-run KB_REPO=git@github.com:<ORG>/<KB_REPO>.git
```

The local vendor clone lives under `.ai/vendor/knowledge-base/` and is ignored. Curated synced notes live under `.ai/knowledge/`.

## First Context Build

Build the local repository metadata index:

```bash
make ai-index-repo
```

Build a Work Item context pack:

```bash
make ai-context WORK_ITEM=EXAMPLE-WI QUERY="example"
```

For real Work Items, fetch or paste Work Item context first:

```text
/fetch-us KIM-1234
```

The `/fetch-us` prompt uses read-only Azure DevOps MCP when configured. If MCP is unavailable, paste the Work Item content and keep the same local artifact shape.

## Optional Validation

```bash
make test
make smoke
```

Commands that require Salesforce CLI auth:

```bash
make ai-index-schema ORG=IntDev
make ai-index-config ORG=IntDev
make ai-index-all ORG=IntDev
```

These commands read schema or explicitly configured config records. They do not write to Salesforce.

## VS Code Tasks

Open the command palette and run `Tasks: Run Task`. Common tasks:

- `AI Workspace: Setup`
- `AI Workspace: Configure`
- `AI Workspace: Doctor`
- `AI: Index Repo Metadata`
- `AI: Build Context Pack`
- `AI: Run Unit Tests`
- `Knowledge: Sync`
- `Knowledge: Index`
- `Docs: Build Workspace Documentation`
- `Docs: Export PDFs`
- `Docs: Open HTML Runbook`

Tasks use the same Makefile commands so behavior is consistent between terminal and VS Code.

## Troubleshooting

- Python not found: install Python 3.11+ and ensure `python3.11`, `python3`, or `python` is on PATH.
- `sf` not found: install Salesforce CLI and restart the terminal.
- Git auth issues: verify SSH keys or HTTPS credentials for the private repos.
- Knowledge Base access denied: confirm the repo URL, branch, and read permission.
- Azure Wiki access denied: confirm wiki Git URL and Git credentials.
- Make unavailable on Windows: use the Python scripts directly or install make.
- `PYTHONPATH` issues: run commands through Makefile, which sets `PYTHONPATH=.ai/skills/python`.
- PDF export unavailable: run `make docs-export-pdf` and follow `docs/workspace/pdf/README.md`.

## Security Notes

- Do not commit `.env`, `.ai/config/workspace.local.json`, `.ai/vendor/`, `.sf/`, `.sfdx/`, or raw data exports.
- Do not store Salesforce, Azure DevOps, GitHub, or Knowledge Base credentials in repository files.
- DevOps Center remains the official metadata promotion mechanism.
- This workspace does not deploy, apply config records, or write Salesforce data.
- GitHub Copilot/Codex-style tooling is the approved AI layer; external model APIs are not part of this workspace.
