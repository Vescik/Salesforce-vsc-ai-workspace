# Troubleshooting

## Setup Issues

Run:

```bash
make doctor
```

If setup folders are missing:

```bash
make setup
```

## Python Version

The workspace expects Python 3.11+.

Check:

```bash
python3 --version
```

If imports fail, run through Makefile so `PYTHONPATH=.ai/skills/python` is set.

## Salesforce CLI Missing

Check:

```bash
sf --version
```

Install Salesforce CLI and restart the terminal. Commands such as `ai-index-schema` and `ai-index-config` require `sf`.

## Salesforce Auth Missing

Authenticate:

```bash
sf org login web --alias IntDev
```

Doctor strict can check auth:

```bash
make doctor-strict
```

## Knowledge Base Repo Access

Symptoms:

- `knowledge-sync` cannot clone.
- Permission denied.
- Wrong branch.

Checks:

```bash
git ls-remote <kb-repo-url>
make knowledge-sync-dry-run KB_REPO=<kb-repo-url> KB_BRANCH=main
```

Fixes:

- Confirm SSH keys or HTTPS credentials.
- Confirm repo URL.
- Confirm branch.
- Confirm team access.

## Azure Wiki Access

Symptoms:

- Wiki dry run cannot clone.
- Prepare branch fails.
- Push approved branch fails.

Checks:

```bash
git ls-remote <wiki-repo-url>
make wiki-dry-run WORK_ITEM=KIM-1234 WIKI_TITLE="Test" WIKI_SOURCE=docs/architecture/README.md AZURE_WIKI_REPO=<wiki-repo-url>
```

Push requires explicit approval note and local push enablement.

## MCP Not Starting

Check `.vscode/mcp.json`.

For local context MCP:

```bash
make mcp-smoke-test
```

Common causes:

- Python not found by VS Code.
- `PYTHONPATH` missing.
- `.ai/context` indexes not generated yet.
- Azure DevOps org placeholder still set to `YOUR_ADO_ORG`.

## VS Code Tasks Cannot Find Python

Run terminal commands from the repository root. If VS Code uses a different shell, configure the workspace terminal or run Makefile targets manually.

## PDF Export Not Available

Run:

```bash
make docs-export-pdf
```

If no local PDF tool is found, follow `docs/workspace/pdf/README.md`.

## Context Pack Missing Knowledge

Run:

```bash
make knowledge-index
make ai-context WORK_ITEM=<WORK_ITEM> QUERY="<topic>"
```

Check that `.ai/context/index/knowledge-cards.jsonl` exists and that KB notes have matching keywords.

## Config Index Empty

Config indexing reads only enabled registry entries:

```bash
config/data-promotion/config-object-registry.yaml
```

Check:

- Salesforce CLI auth.
- Registry object enabled flag.
- Org alias.
- Object visibility.

## GitHub Actions Failing

Common causes:

- Missing validation secrets for manual Salesforce validation.
- Work Item ID not found in PR title or branch.
- Hardcoded Salesforce ID candidate.
- Raw/export data file committed.

Run locally:

```bash
make ai-check-python
make test
make wi-precheck WORK_ITEM=<WORK_ITEM> BASE_REF=origin/main
```

## Unexpected Generated Files

Use:

```bash
git status --short
git check-ignore -v <path>
```

Generated outputs under `.ai/outputs/`, context indexes, local vendor clones, and local config should remain ignored.
