# Quickstart

## Prerequisites

- Python 3.11+
- Git
- Salesforce CLI `sf`
- VS Code with GitHub Copilot access
- Azure DevOps access for read-only Work Item retrieval

---

## Step 1 — Clone and install the package

```bash
git clone <repo-url> && cd <repo-folder>
pip install -e .
```

`pip install -e .` registers the `ai_workspace` package (zero external dependencies). It is also run automatically by `setup`.

---

## Step 2 — Set up local config

```bash
make setup
make configure
```

`configure` is interactive. It sets:
- Salesforce org alias (default: `IntDev`)
- Azure DevOps organization → auto-updates `.vscode/mcp.json`
- Knowledge Base repository URL (optional)

---

## Step 3 — Authenticate Salesforce

```bash
sf org login web --alias IntDev
```

---

## Step 4 — Check the workspace

```bash
make doctor
```

---

## Step 5 — Build first local context

```bash
make ai-index-repo
make knowledge-index
make ai-context WORK_ITEM=EXAMPLE-WI QUERY="example"
```

Then open VS Code, open Copilot Chat, and type `/fetch-us EXAMPLE-WI` to begin.

---

## Optional — Knowledge Base sync

```bash
make knowledge-sync-dry-run KB_REPO=<repo-url-or-local-path>
make knowledge-sync KB_REPO=<repo-url-or-local-path>
make knowledge-index
```

---

> This workspace does not deploy metadata, apply configuration records, write to Salesforce, or use external LLM APIs.
>
> **All commands also available as VS Code Tasks:** `Ctrl+Shift+P` → `Tasks: Run Task`
