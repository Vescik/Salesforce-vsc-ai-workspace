# Copilot AI Workspace Python Tools

## Purpose

This folder contains deterministic local Python tools for the Copilot-only Salesforce AI Workspace. The tools prepare curated repository, schema, configuration, and Work Item context for GitHub Copilot prompts and human review.

## No External LLM APIs

These tools do not call OpenAI, Anthropic, LangChain, or any external model API. They only prepare local context artifacts for GitHub Copilot and human review.

## Commands

Run from the repository root:

```bash
make setup
make configure
make doctor
make first-run
make ai-index-repo
make ai-index-schema ORG=IntDev
make ai-index-config ORG=IntDev
make ai-index-all ORG=IntDev
make knowledge-sync-dry-run KB_REPO=<git-url-or-local-path>
make knowledge-sync KB_REPO=<git-url-or-local-path>
make knowledge-index
make knowledge-import KNOWLEDGE_SOURCE=.ai/knowledge/imports/example.txt KNOWLEDGE_DOMAIN=general KNOWLEDGE_TITLE="Example Knowledge Note"
make knowledge-search QUERY="invoice approval"
make ai-context WORK_ITEM=KIM-1234 QUERY="invoice approval"
make wiki-dry-run WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo>
make wiki-prepare-branch WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo>
make wiki-push-approved WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo> WIKI_APPROVAL_NOTE="Approved by <reviewer/date>"
make ai-context-example
```

Developer checks:

```bash
make ai-check-python
make test
make smoke
make ai-list-outputs WORK_ITEM=EXAMPLE-WI
```

The Makefile sets `PYTHONPATH=.ai/skills/python` for all Python tool commands and prefers `python3.11` when available. `ai-index-schema` and `ai-index-config` require Salesforce CLI authentication to the selected org.

## OOTB Setup

Employee setup is handled by the configuration package:

```bash
make setup
make configure
make doctor
make first-run
```

Direct wrapper commands are also available:

```bash
python scripts/setup.py
python scripts/configure.py
python scripts/doctor.py
```

Local configuration lives at `.ai/config/workspace.local.json` and is ignored by Git. Committed examples live at `.ai/config/workspace.example.json` and `.ai/config/workspace.local.json.example`.

The setup and doctor tools are local-only. They do not log in to Salesforce automatically, deploy metadata, apply configuration records, write to Salesforce, call ADO, call external model APIs, or store Salesforce credentials.

Azure DevOps Work Item retrieval is handled through VS Code MCP and the approved `ado-remote-mcp` server. `make configure` can store the local organization/project names in ignored workspace config, but it must not store ADO tokens, PATs, passwords, or employee credentials. Replace the committed `YOUR_ADO_ORG` placeholder in local VS Code MCP configuration before using `/fetch-us <WORK_ITEM_ID>`.

## Quick Reference

Local-only commands that never require Salesforce org authentication:

```bash
make help
make setup
make configure
make doctor
make first-run
make ai-check-python
make ai-index-repo
make knowledge-sync-dry-run KB_REPO=<git-url-or-local-path>
make knowledge-sync KB_REPO=<git-url-or-local-path>
make knowledge-index
make knowledge-search QUERY="invoice approval"
make ai-context WORK_ITEM=KIM-1234 QUERY="invoice approval"
make knowledge-import KNOWLEDGE_SOURCE=.ai/knowledge/imports/example.txt KNOWLEDGE_DOMAIN=general KNOWLEDGE_TITLE="Example Knowledge Note"
make wiki-dry-run WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo>
make config-impact WORK_ITEM=KIM-1234
make config-pack-skeleton WORK_ITEM=KIM-1234
make wi-precheck WORK_ITEM=KIM-1234 BASE_REF=HEAD~1
make wi-precheck-strict WORK_ITEM=KIM-1234 BASE_REF=origin/main
make mcp-salesforce-context
make mcp-smoke-test
make test
make smoke
```

Commands that require Salesforce CLI org authentication:

```bash
make ai-index-schema ORG=IntDev
make ai-index-config ORG=IntDev
make ai-index-all ORG=IntDev
```

MCP server usage:

```bash
make mcp-salesforce-context
```

VS Code can also start MCP servers from `.vscode/mcp.json`:

- `salesforce-context`: local read-only context server.
- `ado-remote-mcp`: remote Azure DevOps MCP server for read-only Work Item retrieval used by `/fetch-us`.

## Testing

Run unit tests from the repository root:

```bash
make test
```

Run the local smoke test:

```bash
make smoke
```

Unit tests use Python `unittest`, temporary files, and local fixtures only. They do not require Salesforce CLI, org authentication, ADO, an MCP client, network access, external model APIs, or real `force-app` metadata.

The smoke test runs Python import checks, unit tests, an example context-pack build, config impact analysis, config pack skeleton generation, and the local Work Item precheck. It does not retrieve metadata, deploy metadata, write to Salesforce, apply configuration records, or call Salesforce CLI.

## Index Files

The indexers write AI-readable local context files under `.ai/context/index/`:

- `metadata-components.jsonl`: local Salesforce metadata components from the repository.
- `sobject-cards.jsonl`: schema cards for selected Salesforce objects.
- `field-cards.jsonl`: schema cards for selected Salesforce fields.
- `relationship-cards.jsonl`: relationship cards derived from schema where available.
- `config-record-cards.jsonl`: anonymized configuration record cards from explicitly enabled registry objects.
- `knowledge-cards.jsonl`: curated internal knowledge-base note cards from `.ai/knowledge/`.

The repository metadata indexer is local-only and best-effort. It extracts richer context from Apex, Flow, LWC, FlexiPage, Layout, Permission Set, and Profile files when they are present under `force-app`. XML metadata parsing uses Python standard-library parsers and continues with warnings if one file cannot be parsed.

## Context Pack

The context pack builder writes Work Item-specific artifacts under `.ai/context/work-items/<WORK_ITEM_ID>/`:

- `ado-work-item.json`: normalized Azure DevOps Work Item fields from `/fetch-us`.
- `work-item-summary.md`: human-readable Work Item summary from `/fetch-us`.
- `acceptance-criteria.md`: normalized acceptance criteria from `/fetch-us`.
- `context-pack.md`: concise curated context pack for solution design.
- `relevant-metadata.yaml`: selected metadata references.
- `relevant-schema.yaml`: selected object, field, and relationship references.
- `relevant-config-records.yaml`: selected anonymized configuration record references.
- `relevant-knowledge.yaml`: selected internal knowledge note references.
- `context-sources.json`: traceability, input files, selected counts, and warnings.

## Internal Knowledge Base

Curated internal managed package knowledge is maintained in a separate private Knowledge Base Git repository. That external repo is the source of truth; `.ai/knowledge/` is the synchronized local copy used by this Salesforce AI Workspace.

Sync preview:

```bash
make knowledge-sync-dry-run KB_REPO=<git-url-or-local-path>
```

Sync curated notes into `.ai/knowledge/`:

```bash
make knowledge-sync KB_REPO=<git-url-or-local-path>
```

The local clone cache lives under gitignored `.ai/vendor/knowledge-base/`. The sync tool copies curated Markdown notes according to `.ai/knowledge/sync-policy.yaml`, skips raw `imports/` and `archive/` content by default, writes `.ai/knowledge/sync-state.json`, and creates reports under `.ai/outputs/knowledge-sync/`.

Import a local source file into draft markdown notes:

```bash
make knowledge-import KNOWLEDGE_SOURCE=.ai/knowledge/imports/example.txt KNOWLEDGE_DOMAIN=general KNOWLEDGE_TITLE="Example Knowledge Note"
```

Build the knowledge index:

```bash
make knowledge-index
```

This creates `.ai/context/index/knowledge-cards.jsonl` and `.ai/context/index/knowledge-index-summary.json`.

Search indexed knowledge cards:

```bash
make knowledge-search QUERY="invoice approval"
```

Context packs use the generated knowledge cards to add a `Relevant Internal Knowledge` section and `.ai/context/work-items/<WORK_ITEM_ID>/relevant-knowledge.yaml`. Selected KB notes are supporting evidence only; draft, low-confidence, stale, or conflicting notes require human validation.

PDF extraction is optional for legacy local imports. If neither `pypdf` nor `PyPDF2` is installed, PDF import reports a clear error. The importer does not use OCR, does not call external services, and does not call any LLM for summarization. Imported notes default to `status: draft` and `confidence: low` and require human review.

## Azure Wiki Draft Publication

The Azure Wiki tools prepare draft Markdown updates for an Azure DevOps Wiki Git repository. They are local/deterministic and use Git only; they do not call Azure DevOps REST APIs, deploy Salesforce metadata, apply configuration records, write Salesforce data, or use external LLM APIs.

Commands:

```bash
make wiki-dry-run WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo>
make wiki-prepare-branch WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo>
make wiki-push-approved WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo> WIKI_APPROVAL_NOTE="Approved by <reviewer/date>"
make wiki-scan AZURE_WIKI_VENDOR_DIR=.ai/vendor/azure-wiki
```

Workflow:

1. Run `wiki-dry-run` first.
2. Review `.ai/outputs/wiki/<WORK_ITEM_ID>.wiki-placement.md` and the preview page.
3. Run `wiki-prepare-branch` only after placement review.
4. Set local `azure_wiki.push_enabled=true`, then run `wiki-push-approved` only after explicit human approval.
5. Create/review/merge the Azure DevOps PR manually outside this tool.

Safety gates:

- Wiki repo URL is configured locally or passed as `AZURE_WIKI_REPO`.
- Existing wiki structure is scanned before target placement.
- Existing pages are not overwritten without warning, diff evidence, and approval.
- Push requires local `azure_wiki.push_enabled=true`, `--approved` through the Makefile target, and `WIKI_APPROVAL_NOTE`.
- Approved push only pushes a feature branch.
- Direct push to the wiki default branch and auto-merge are not implemented.
- Git credentials come from the user's Git credential manager; tokens are not stored in repo config.

## Work Item Precheck

Run local prechecks before committing or opening a PR:

```bash
make wi-precheck WORK_ITEM=KIM-1234 BASE_REF=HEAD~1
make wi-precheck-strict WORK_ITEM=KIM-1234 BASE_REF=origin/main
```

The precheck is local-only. It does not deploy, retrieve metadata, call Salesforce, call ADO, or use external model APIs.

It checks:

- changed files against `.ai/context/work-items/<WORK_ITEM_ID>/metadata-scope.yaml` when present
- Salesforce ID candidates in changed files
- raw/exported data risk and likely secrets
- required artifacts such as `context-pack.md`, solution design, and QA how-to-test documentation

Outputs:

```text
.ai/outputs/precheck/<WORK_ITEM_ID>.precheck.md
.ai/outputs/precheck/<WORK_ITEM_ID>.precheck.json
```

## GitHub Actions Gates

The repository includes deterministic pull request gates:

- `validate-work-item.yml` runs the local Work Item precheck on PRs. It infers a Work Item ID from the PR title or branch using the generic `[A-Z]+-[0-9]+` pattern and falls back to `EXAMPLE-WI` with a warning.
- `validate-no-salesforce-ids.yml` runs the existing precheck as a focused security gate for hardcoded Salesforce ID candidates and raw/export data risk.
- `salesforce-validate.yml` runs Salesforce metadata validation only. It uses `sf project deploy validate` with `manifest/package.xml` and does not deploy metadata.

Salesforce validation requires these GitHub secrets when enabled by the team:

- `SF_JWT_KEY`
- `SF_CLIENT_ID`
- `SF_USERNAME`
- `SF_LOGIN_URL`
- `SF_VALIDATE_ORG_ALIAS`

On pull requests, Salesforce validation skips with a warning if secrets are missing. On manual `workflow_dispatch`, missing secrets fail clearly.

## Documentation and QA Prompts

Copilot prompt files in `.github/prompts/` support draft documentation and QA artifact generation:

- `create-documentation`
- `create-how-to-test`
- `update-documentation-from-diff`
- `review-qa-how-to-test`

These prompts read existing Work Item artifacts, context packs, solution designs, precheck reports, relevant metadata/config summaries, and local Git diff when available. They do not call Salesforce, ADO, MCP servers, external model APIs, or deployment tools. Generated documentation and QA outputs are drafts requiring human review.

If `.ai/context/work-items/<WORK_ITEM_ID>/work-item-summary.md` or `acceptance-criteria.md` is missing, run `/fetch-us <WORK_ITEM_ID>` first. Documentation and QA prompts rely on normalized local Work Item artifacts instead of calling ADO directly.

## Salesforce Context MCP Server

Start the read-only local MCP server from the repository root:

```bash
make mcp-salesforce-context
```

Smoke test tool listing without VS Code:

```bash
make mcp-smoke-test
```

VS Code MCP configuration is in `.vscode/mcp.json` and registers the server as:

```text
salesforce-context
ado-remote-mcp
```

The local `salesforce-context` MCP server exposes curated local files only. It does not call Salesforce, does not deploy, does not write to Salesforce, does not apply config records, and does not use external LLM APIs.

The remote `ado-remote-mcp` server is approved only for read-only Azure DevOps Work Item retrieval through `/fetch-us`. Do not use ADO MCP write tools to create, update, assign, transition, comment on, or link Work Items.

Available tools:

- `search_context`: search local metadata, schema, relationship, and config indexes.
- `get_work_item_context`: read local Work Item context artifacts.
- `get_object_card`: read an object card with related field and relationship cards.
- `get_related_metadata`: search local metadata components.
- `get_related_config_records`: search anonymized config record cards.
- `get_related_knowledge`: search local internal knowledge cards.
- `get_knowledge_note`: read one capped markdown note under `.ai/knowledge/`.
- `get_solution_design`: read proposed or approved solution design artifacts.
- `get_config_impact`: read local config impact artifacts.

## Deployment Runbooks

Process documentation for DevOps Center promotion support is under:

```text
.ai/deployment/runbooks/
```

These runbooks describe environment mapping, local Work Item flow, pre-promote checks, config sidecar review, and Full Copy sandbox rules. They are process documentation, not executable deployment automation. They do not deploy metadata, apply configuration records, call Salesforce, or replace DevOps Center.

## Workspace Documentation Tools

The docs helper validates the workspace documentation pack and exports PDFs when supported local tools are installed:

```bash
make docs-build
make docs-export-pdf
make docs-pack
```

Implementation:

```text
ai_workspace.docs.export_docs
```

`docs-build` checks required files under `docs/workspace/`. `docs-export-pdf` detects local PDF tools such as Pandoc. If no supported tool is available, it writes manual instructions under `docs/workspace/pdf/README.md` and exits successfully.

## Safety Notes

- IntDev is a Full Copy developer org without Git and is not the source of truth.
- DevOps Center remains the official Salesforce metadata promotion mechanism.
- The repository metadata indexer reads local files only.
- The org schema indexer uses read-only `sf data query --json` schema queries.
- Config record indexing is controlled by `config/data-promotion/config-object-registry.yaml`.
- Do not enable broad transactional object indexing.
- GitHub Actions gates do not deploy metadata or apply configuration records.
- The Salesforce context MCP server reads only approved local context roots and does not expose arbitrary filesystem access.
- These Python tools do not deploy, retrieve metadata, write to Salesforce, apply config records, or invoke external model APIs.
- Azure DevOps Work Item content fetched through `/fetch-us` is local planning context, not source code, approval authority, deployment evidence, or a replacement for DevOps Center.
