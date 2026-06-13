# Copilot-only Salesforce AI Workspace

This repository contains deterministic local tooling and Copilot instructions for Salesforce development on top of the closed KimbleOne/Kantata managed package.

## Salesforce AI Workspace

This is a Copilot-only Salesforce AI Workspace for solution design, context indexing, documentation, QA support, prechecks, config impact review, and release readiness.

This is not:

- a deployment agent
- a config apply tool
- a replacement for DevOps Center
- an external LLM integration
- a source of truth for managed package internals

The workspace assists, validates, and documents. It does not deploy metadata, apply configuration records, write to Salesforce, call external model APIs, or assume KimbleOne/Kantata managed package internals.

## Quick Start For Employees

1. Clone the Salesforce project repository.

2. Install prerequisites:

- Python 3.11+
- Git
- Salesforce CLI `sf`
- VS Code
- GitHub Copilot access
- Azure DevOps access for Work Item read-only retrieval through VS Code MCP

3. Run setup:

```bash
make setup
```

4. Configure local values:

```bash
make configure
```

5. Authenticate Salesforce:

```bash
sf org login web --alias IntDev
```

6. Run doctor:

```bash
make doctor
```

7. Build the local repo index:

```bash
make ai-index-repo
```

8. Fetch Work Item context:

```text
/fetch-us EXAMPLE-WI
```

9. Optionally sync and index the Knowledge Base:

```bash
make knowledge-sync KB_REPO=<repo-url-or-local-path>
make knowledge-index
```

10. Build context:

```bash
make ai-context WORK_ITEM=EXAMPLE-WI QUERY="example"
```

## Platform Notes

macOS/Linux:

```bash
./scripts/setup.sh
./scripts/doctor.sh
```

Windows PowerShell:

```powershell
.\scripts\setup.ps1
.\scripts\doctor.ps1
```

If `make` is not installed on Windows, use:

```powershell
python scripts/setup.py
python scripts/configure.py
python scripts/doctor.py
```

## Configuration

Committed examples:

- `.ai/config/workspace.example.json`
- `.ai/config/workspace.local.json.example`

Local ignored config:

- `.ai/config/workspace.local.json`

Salesforce auth is managed by Salesforce CLI. Do not store Salesforce tokens, passwords, private keys, or secrets in workspace config.

Azure DevOps Work Item fetch uses the remote `ado-remote-mcp` server in `.vscode/mcp.json`. Replace the committed `YOUR_ADO_ORG` placeholder with your Azure DevOps organization in local VS Code MCP configuration before running `/fetch-us <WORK_ITEM_ID>`. Do not store ADO PATs, OAuth tokens, passwords, or employee credentials in repository config.

## Common Commands

```bash
make help
make setup
make configure
make doctor
make first-run
make ai-index-repo
make knowledge-index
make ai-context WORK_ITEM=<WORK_ITEM_ID> QUERY="<business topic>"
make wiki-dry-run WORK_ITEM=<WORK_ITEM_ID> WIKI_TITLE="<page title>" WIKI_SOURCE=docs/architecture/<WORK_ITEM_ID>.md AZURE_WIKI_REPO=<wiki-repo>
make wiki-prepare-branch WORK_ITEM=<WORK_ITEM_ID> WIKI_TITLE="<page title>" WIKI_SOURCE=docs/architecture/<WORK_ITEM_ID>.md AZURE_WIKI_REPO=<wiki-repo>
make wi-precheck WORK_ITEM=<WORK_ITEM_ID> BASE_REF=HEAD~1
```

Commands that require Salesforce CLI org authentication:

```bash
make ai-index-schema ORG=IntDev
make ai-index-config ORG=IntDev
make ai-index-all ORG=IntDev
make doctor-strict
```

## Internal Knowledge Base

Internal managed package knowledge is maintained in a separate private Knowledge Base Git repository. This workspace syncs curated Markdown notes into `.ai/knowledge/`, keeps the local clone cache under gitignored `.ai/vendor/knowledge-base/`, and indexes selected notes into `.ai/context/index/knowledge-cards.jsonl`.

Use a dry run before syncing:

```bash
make knowledge-sync-dry-run KB_REPO=<repo-url-or-local-path>
```

Employees can either pass `KB_REPO` on the command line or set the ignored local config file:

```json
{
  "knowledge_base": {
    "enabled": true,
    "repo_url": "git@github.com:<ORG>/<KB_REPO>.git",
    "branch": "main",
    "sync_on_setup": false
  }
}
```

Then sync and index:

```bash
make knowledge-sync KB_REPO=<repo-url-or-local-path>
make knowledge-index
```

Context packs search the generated knowledge index and include only selected KB cards in the `Relevant Internal Knowledge` section. KB notes are supporting evidence, not global instructions; draft, low-confidence, stale, or conflicting notes require human validation.

## Azure Wiki Draft Publication

Azure DevOps Wiki publication is draft-first and human reviewed. Configure the wiki Git repository locally through `AZURE_WIKI_REPO`, `.ai/config/workspace.local.json`, or a Makefile argument. Do not store Azure DevOps PATs, tokens, or credentials in repository config.

Recommended flow:

```bash
make wiki-dry-run WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo>
make wiki-prepare-branch WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo>
make wiki-push-approved WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo> WIKI_APPROVAL_NOTE="Approved by <reviewer/date>"
```

`wiki-dry-run` inspects the wiki clone, chooses a draft target path, and writes local reports/previews under `.ai/outputs/wiki/`. `wiki-prepare-branch` creates a local draft branch and commit in `.ai/vendor/azure-wiki/`. `wiki-push-approved` requires explicit approval, `WIKI_APPROVAL_NOTE`, and local `azure_wiki.push_enabled=true`; it pushes only the feature branch. PR creation, review, merge, and final publication remain manual Azure DevOps steps.

## Documentation Pack

Workspace documentation is under `docs/workspace/`:

- installation guide
- non-technical overview
- technical architecture
- agents, prompts, skills, and MCP reference
- developer process runbook
- Knowledge Base runbook
- Azure Wiki publication runbook
- security and governance
- troubleshooting
- command reference
- offline HTML one-page runbook
- PDF export folder

Start here:

- `docs/workspace/README.md`
- `docs/workspace/html/index.html`

Regenerate or validate the docs package:

```bash
make docs-build
make docs-export-pdf
make docs-pack
```

PDF export uses local tools if available. If no supported PDF tool is installed, the workspace writes manual export instructions under `docs/workspace/pdf/README.md`.

## Work Item Flow

1. Checkout the DevOps Center Work Item branch.
2. Run `/fetch-us <WORK_ITEM_ID>` to create normalized local Work Item artifacts from read-only Azure DevOps MCP data.
3. Run `make ai-index-repo`.
4. Build context with `make ai-context WORK_ITEM=<WORK_ITEM_ID> QUERY="<business topic>"`.
5. Use Copilot prompts such as `/solution-design`, `/solution-design-review`, and `/design-to-work-packets`.
6. Implement manually and with Copilot assistance, keeping changes scoped to the Work Item and acceptance criteria.
7. Run `make config-impact WORK_ITEM=<WORK_ITEM_ID>` and `make wi-precheck WORK_ITEM=<WORK_ITEM_ID> BASE_REF=HEAD~1`.
8. Generate draft docs and QA instructions with `/create-documentation` and `/create-how-to-test`.
9. Promote Salesforce metadata through DevOps Center.

## Boundaries

- GitHub Copilot is the only approved AI execution layer.
- DevOps Center remains the official Salesforce metadata promotion mechanism.
- IntDev is a Full Copy developer/discovery org without Git and is not the source of truth.
- Config record promotion is separate from metadata promotion.
- Config apply and production writes are not implemented.
- Salesforce schema/config indexing requires `sf` CLI authentication when those commands are run.
- No external LLM API keys are required.

## Local Validation

```bash
make ai-check-python
make test
make smoke
```

`make smoke` is local-only and does not require org authentication. It may report precheck warnings when Work Item scope files are missing or example QA artifacts have not been generated yet.
