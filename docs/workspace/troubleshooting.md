# Troubleshooting

## Setup Issues

Run:

```powershell
.\scripts\workspace.ps1 doctor
```

If setup folders are missing:

```powershell
.\scripts\workspace.ps1 setup
```

## Python Version

The workspace expects Python 3.11+.

Check:

```powershell
python --version
```

If imports fail, run `pip install -e .` once so PYTHONPATH is not required, or invoke through `.\scripts\workspace.ps1` which sets `PYTHONPATH=.ai/skills/python`.

## Salesforce CLI Missing

Check:

```powershell
sf --version
```

Install Salesforce CLI and restart the terminal. Commands such as `ai-index-schema` and `ai-index-config` require `sf`.

## Salesforce Auth Missing

Authenticate:

```powershell
sf org login web --alias IntDev
```

Doctor strict can check auth:

```powershell
.\scripts\workspace.ps1 doctor-strict
```

## Knowledge Base Repo Access

Symptoms:

- `knowledge-sync` cannot clone.
- Permission denied.
- Wrong branch.

Checks:

```powershell
git ls-remote <kb-repo-url>
.\scripts\workspace.ps1 knowledge-sync-dry-run -KbRepo <kb-repo-url> -KbBranch main
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

```powershell
git ls-remote <wiki-repo-url>
.\scripts\workspace.ps1 wiki-dry-run -WorkItem KIM-1234 -WikiTitle "Test" -WikiSource docs/architecture/README.md -AzureWikiRepo <wiki-repo-url>
```

Push requires explicit approval note and local push enablement.

## MCP Not Starting

Check `.vscode/mcp.json`.

For local context MCP:

```powershell
.\scripts\workspace.ps1 mcp-smoke-test
```

Common causes:

- Python not found by VS Code.
- `PYTHONPATH` missing.
- `.ai/context` indexes not generated yet.
- Azure DevOps org placeholder still set to `YOUR_ADO_ORG`.

## VS Code Tasks Cannot Find Python

Run terminal commands from the repository root. If VS Code uses a different shell, configure the workspace terminal or run `.\scripts\workspace.ps1` targets manually.

## PDF Export Not Available

Run:

```powershell
.\scripts\workspace.ps1 docs-export-pdf
```

If no local PDF tool is found, follow `docs/workspace/pdf/README.md`.

## Context Pack Missing Knowledge

Run:

```powershell
.\scripts\workspace.ps1 knowledge-index
.\scripts\workspace.ps1 ai-context -WorkItem <WORK_ITEM> -Query "<topic>"
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

```powershell
.\scripts\workspace.ps1 ai-check-python
.\scripts\workspace.ps1 test
.\scripts\workspace.ps1 wi-precheck -WorkItem <WORK_ITEM> -BaseRef origin/main
```

## Windows Path Issues

Keep repo paths short and avoid moving the workspace while VS Code tasks are running.

## Unexpected Generated Files

Use:

```bash
git status --short
git check-ignore -v <path>
```

Generated outputs under `.ai/outputs/`, context indexes, local vendor clones, and local config should remain ignored.
