# Quickstart

1. Install prerequisites:
   - Python 3.11+
   - Git
   - Salesforce CLI `sf`
   - VS Code with GitHub Copilot access
   - Azure DevOps access for read-only Work Item retrieval

2. Set up local config:

```bash
make setup
make configure
```

`make configure` runs interactively and sets your Salesforce org alias, Azure DevOps organization, and Knowledge Base repository URL. It also automatically updates `.vscode/mcp.json` with your ADO organization — no manual placeholder editing required.

**Windows:** Use `.\scripts\workspace.ps1 configure` instead of `make configure`.

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
