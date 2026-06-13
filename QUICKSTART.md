# Quickstart

1. Install prerequisites:
   - Python 3.11+
   - Git
   - Salesforce CLI `sf`
   - VS Code with GitHub Copilot access
   - Azure DevOps access for read-only Work Item retrieval

2. Install the workspace package and set up local config:

```bash
pip install -e .
make setup
make configure
```

- `pip install -e .` registers the `ai_workspace` package in your Python environment (zero external dependencies — no downloads). This makes all commands work without manually setting `PYTHONPATH`.
- `make setup` creates the required directories and config file.
- `make configure` sets your Salesforce org alias, Azure DevOps organization, and Knowledge Base URL, and auto-updates `.vscode/mcp.json`.

**Windows (PowerShell):**
```powershell
pip install -e .
.\scripts\workspace.ps1 setup
.\scripts\workspace.ps1 configure
```

> ℹ️ `make setup` and `.\scripts\workspace.ps1 setup` run `pip install -e .` automatically — if you use these commands you don't need to run pip manually.

3. Authenticate Salesforce:

```bash
sf org login web --alias IntDev
```

4. Check the workspace:

```bash
make doctor
```

5. Build first local context:

```bash
make ai-index-repo
/fetch-us EXAMPLE-WI
make knowledge-index
make ai-context WORK_ITEM=EXAMPLE-WI QUERY="example"
```

`/fetch-us` writes normalized local Work Item artifacts only. The Azure DevOps MCP connection uses the organization set in step 2.

Optional Knowledge Base sync:

```bash
make knowledge-sync-dry-run KB_REPO=<repo-url-or-local-path>
make knowledge-sync KB_REPO=<repo-url-or-local-path>
make knowledge-index
```

This workspace does not deploy metadata, apply configuration records, write to Salesforce, or use external LLM APIs.
