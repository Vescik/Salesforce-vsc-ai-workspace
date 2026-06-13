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

Before using `/fetch-us`, update the `YOUR_ADO_ORG` placeholder in `.vscode/mcp.json` or your local VS Code MCP settings. `/fetch-us` writes normalized local Work Item artifacts only.

Optional Knowledge Base sync:

```bash
make knowledge-sync-dry-run KB_REPO=<repo-url-or-local-path>
make knowledge-sync KB_REPO=<repo-url-or-local-path>
make knowledge-index
```

This workspace does not deploy metadata, apply configuration records, write to Salesforce, or use external LLM APIs.
