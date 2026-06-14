# Troubleshooting Runbook

> Platform note: this branch uses the Windows PowerShell command surface. Run all commands from the repository root unless a step says otherwise.

## Purpose

Use this runbook to diagnose common setup, Knowledge Base, Azure Wiki, MCP, documentation, and CI issues without changing Salesforce data, deploying metadata, applying configuration records, or exposing sensitive information.

## When To Use

Use this runbook when a workspace command fails, a generated artifact is missing, VS Code/Copilot cannot find context, or a local validation result needs triage.

Do not use this runbook to bypass human approval gates, force-push docs, apply configuration records, or repair production data.

## Inputs

Collect these before troubleshooting:

- Command that failed.
- Full terminal error text, with secrets redacted.
- Current branch and `git status --short`.
- Work Item ID, if relevant.
- Expected output path.
- Whether the command needs Git, Salesforce CLI, Azure DevOps MCP, or local-only context.

## Preconditions

1. Run from repository root.
2. Do not paste or commit secrets, tokens, logs with customer data, raw exports, or Salesforce record IDs.
3. Confirm Python can start:

```powershell
python --version
```

4. Prefer wrapper commands because they set local paths consistently:

```powershell
.\scripts\workspace.ps1 help
```

## Operator Steps

### 1. Classify The Failure

| Symptom | Go to |
| --- | --- |
| Setup, Python, or missing folders | Setup And Python |
| Salesforce CLI or org auth | Salesforce CLI And Auth |
| Knowledge sync/create/search | Knowledge Base |
| Azure Wiki dry run, branch, or push | Azure Wiki |
| MCP server or Copilot context | MCP And Context |
| VS Code task failure | VS Code Tasks |
| Docs export or docs validation | Documentation Pack |
| GitHub Actions failure | GitHub Actions |
| Unexpected generated files | Generated Files |

### 2. Setup And Python

Checks:

```powershell
python --version
.\scripts\workspace.ps1 doctor
```

Safe fixes:

```powershell
.\scripts\workspace.ps1 setup
.\scripts\workspace.ps1 configure
```

Expected outputs:

- Doctor report under `.ai/outputs/doctor/`.
- Ignored local config under `.ai/config/workspace.local.json` when configured.

Escalate when Python is not 3.11+, wrapper scripts cannot start, or local config paths are unclear.

### 3. Salesforce CLI And Auth

Checks:

```powershell
sf --version
sf org list
.\scripts\workspace.ps1 doctor-strict
```

Safe fixes:

```powershell
sf org login web --alias IntDev
```

Expected outputs:

- `doctor-strict` confirms optional Salesforce auth when required.
- Schema/config index commands can read the configured org alias.

Escalate when the org alias is wrong, the user lacks org access, or schema/config reads fail for permission reasons.

### 4. Knowledge Base

Symptoms:

- `knowledge-sync` cannot clone.
- `knowledge-create` generates low-value notes.
- `knowledge-validate` reports blocking findings.
- `knowledge-search` misses expected notes.
- Context packs omit expected knowledge.

Checks:

```powershell
git ls-remote "<configured-kb-repo-url>"
.\scripts\workspace.ps1 knowledge-sync-dry-run
.\scripts\workspace.ps1 knowledge-validate
.\scripts\workspace.ps1 knowledge-index
.\scripts\workspace.ps1 knowledge-search -Query "<topic>"
```

Safe fixes:

- Confirm Git credentials, repo URL, branch, and team access.
- Review `.ai/outputs/knowledge-sync/knowledge-sync.md`.
- Review `.ai/outputs/knowledge-import/validation-report.md`.
- Add or correct note purpose, aliases, key concepts, related objects, related fields, and keywords.
- Re-run `knowledge-index`, `knowledge-graph`, and `ai-context`.

Expected outputs:

- `.ai/knowledge/`
- `.ai/context/index/knowledge-cards.jsonl`
- `.ai/context/index/knowledge-graph.json`
- `.ai/context/work-items/<WORK_ITEM>/context-pack.md`

Escalate when validation finds possible secrets, raw exports, unsupported managed-package claims, or conflicts with schema/config/tests/human facts.

### 5. Azure Wiki

Symptoms:

- Wiki dry run cannot clone.
- Placement is wrong.
- Prepare branch fails.
- Push approved branch is blocked.

Checks:

```powershell
git ls-remote "<configured-wiki-repo-url>"
.\scripts\workspace.ps1 wiki-dry-run -WorkItem KIM-1234 -WikiTitle "Test" -WikiSource "docs/architecture/README.md"
```

Safe fixes:

- Confirm wiki repo URL, branch, and Git credentials.
- Review `.ai/outputs/wiki/<WORK_ITEM>.wiki-placement.md`.
- Add `-WikiModule` or `-WikiTargetPath` for explicit placement.
- For push only, add `-WikiApprovalNote` and local `azure_wiki.push_enabled=true`.

Expected outputs:

- `.ai/outputs/wiki/<WORK_ITEM>.wiki-publication-report.md`
- Local draft branch under `.ai/vendor/azure-wiki/` for prepare-branch.

Escalate when the requested change overwrites existing wiki content, approval is missing, or the target path cannot be reviewed by the page owner.

### 6. MCP And Context

Checks:

```powershell
.\scripts\workspace.ps1 mcp-smoke-test
.\scripts\workspace.ps1 ai-index-repo
.\scripts\workspace.ps1 knowledge-index
```

Common causes:

- Python not found by VS Code.
- `.vscode/mcp.json` still contains placeholder values.
- `.ai/context` indexes have not been generated.
- Azure DevOps org placeholder is still `YOUR_ADO_ORG`.

Safe fixes:

- Run `.\scripts\workspace.ps1 configure`.
- Rebuild local indexes.
- Restart VS Code after changing MCP configuration.

Escalate when MCP exposes unexpected roots or any tool appears capable of Salesforce writes, ADO writes, deployment, or config apply.

### 7. VS Code Tasks

Checks:

```powershell
.\scripts\workspace.ps1 help
```

Safe fixes:

- Run terminal commands from the repository root.
- Confirm VS Code uses PowerShell on this branch.
- Run the matching `.\scripts\workspace.ps1` command manually to isolate task configuration from tool behavior.

Escalate when a task points to a removed command or employee-specific path.

### 8. Documentation Pack

Checks:

```powershell
.\scripts\workspace.ps1 docs-build
.\scripts\workspace.ps1 docs-export-pdf
```

Safe fixes:

- If PDF tooling is missing, follow `docs/workspace/pdf/README.md`.
- Keep docs changes in `docs/workspace/` and run docs validation again.

Expected outputs:

- Docs package validation success.
- PDFs under `docs/workspace/pdf/` when tooling exists, or manual PDF instructions when it does not.

Escalate when required docs are missing or a runbook documents an unsupported command.

### 9. GitHub Actions

Common causes:

- Missing validation secrets for optional Salesforce validate-only workflow.
- Work Item ID missing from PR title or branch.
- Hardcoded Salesforce ID candidate.
- Raw/export data file committed.
- Python import or unit test failure.

Run locally:

```powershell
.\scripts\workspace.ps1 ai-check-python
.\scripts\workspace.ps1 test
.\scripts\workspace.ps1 wi-precheck -WorkItem <WORK_ITEM> -BaseRef origin/main
```

Escalate when a CI finding involves secrets, raw data, deployment scope, or Salesforce validation credentials.

### 10. Generated Files

Checks:

```powershell
git status --short
git check-ignore -v <path>
```

Safe fixes:

- Keep ignored outputs under `.ai/outputs/`, `.ai/context/`, `.ai/vendor/`, `.ai/config/workspace.local.json`, virtualenv folders, and local Salesforce auth folders.
- Do not commit raw imports, local config, vendor clones, logs, secrets, or uncontrolled exports.

Escalate when generated files include sensitive data or tracked files changed unexpectedly.

## Expected Outputs

Troubleshooting should produce one of:

- A safe local fix and the command used.
- A report path containing the finding.
- A clear escalation note with owner, evidence, and blocked next step.

## Review Gates

Human review is required before:

- Treating draft or low-confidence knowledge as design evidence.
- Pushing Knowledge Base changes.
- Pushing Azure Wiki branches.
- Promoting Salesforce metadata through DevOps Center.
- Publishing docs derived from unreviewed Work Item or KB content.

## Troubleshooting

Use the decision tree in Operator Steps as the primary troubleshooting path. If the symptom does not match any listed category, run the general health checks and escalate with the command, error text, output path, branch, and Work Item ID:

```powershell
.\scripts\workspace.ps1 doctor
.\scripts\workspace.ps1 ai-check-python
.\scripts\workspace.ps1 test
```

## Escalation

Escalate with:

- Command run.
- Error text with secrets redacted.
- Output/report path.
- Work Item ID.
- Current branch.
- Human decision needed.

Escalate immediately if there is possible secret exposure, raw customer data, unsupported managed-package claims, Salesforce write risk, ADO write risk, or config apply risk.

## Safety Boundaries

- Do not run destructive Git commands unless explicitly requested.
- Do not commit local config, credentials, raw imports, logs, dumps, or vendor clones.
- Do not use external model APIs.
- Do not deploy Salesforce metadata from this workspace.
- Do not write Salesforce data.
- Do not apply configuration records.
- Do not bypass DevOps Center or human approval gates.

## Maintenance

- Update this runbook when command names, output paths, or approval gates change.
- Add new symptoms when a failure repeats more than once.
- Keep troubleshooting examples Windows-first on this branch.
- Validate with `.\scripts\workspace.ps1 docs-build` after edits.
