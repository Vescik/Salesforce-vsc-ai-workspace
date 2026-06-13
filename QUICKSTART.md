# Quickstart

## Prerequisites

- Python 3.11+
- Git
- Salesforce CLI `sf`
- VS Code with GitHub Copilot access
- Azure DevOps access for read-only Work Item retrieval

---

## Step 1 — Clone and install the package

```powershell
# Windows (PowerShell)
git clone <repo-url>
cd <repo-folder>
pip install -e .
```

```bash
# Mac / Linux
git clone <repo-url> && cd <repo-folder>
pip install -e .
```

`pip install -e .` registers the `ai_workspace` package (zero external dependencies). It is also run automatically by `setup`.

---

## Step 2 — Set up local config

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 setup
.\scripts\workspace.ps1 configure
```

```bash
# Mac / Linux
make setup
make configure
```

`configure` is interactive. It sets:
- Salesforce org alias (default: `IntDev`)
- Azure DevOps organization → auto-updates `.vscode/mcp.json`
- Knowledge Base repository URL (optional)

---

## Step 3 — Authenticate Salesforce

```powershell
sf org login web --alias IntDev
```

*(Same on all platforms — Salesforce CLI is cross-platform.)*

---

## Step 4 — Check the workspace

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 doctor
```

```bash
# Mac / Linux
make doctor
```

---

## Step 5 — Build first local context

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 ai-index-repo
.\scripts\workspace.ps1 knowledge-index
.\scripts\workspace.ps1 ai-context -WorkItem EXAMPLE-WI -Query "example"
```

```bash
# Mac / Linux
make ai-index-repo
make knowledge-index
make ai-context WORK_ITEM=EXAMPLE-WI QUERY="example"
```

Then open VS Code, open Copilot Chat, and type `/fetch-us EXAMPLE-WI` to begin.

---

## Optional — Knowledge Base sync

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 knowledge-sync-dry-run -KbRepo "<repo-url-or-local-path>"
.\scripts\workspace.ps1 knowledge-sync -KbRepo "<repo-url-or-local-path>"
.\scripts\workspace.ps1 knowledge-index
```

```bash
# Mac / Linux
make knowledge-sync-dry-run KB_REPO=<repo-url-or-local-path>
make knowledge-sync KB_REPO=<repo-url-or-local-path>
make knowledge-index
```

---

> This workspace does not deploy metadata, apply configuration records, write to Salesforce, or use external LLM APIs.
>
> **All commands also available as VS Code Tasks:** `Ctrl+Shift+P` → `Tasks: Run Task`
