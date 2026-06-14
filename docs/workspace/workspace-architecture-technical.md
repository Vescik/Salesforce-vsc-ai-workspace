# Technical Architecture

Audience: Salesforce developers, DevSecOps engineers, maintainers, and architects.

## Architecture Overview

The workspace is a file-based, Copilot-only assistant layer inside a Salesforce DX repository. It combines prompt files, custom agents, local standard-library Python tools, the Windows PowerShell command surface, VS Code tasks, MCP configuration, and GitHub validation workflows.

The system is intentionally local-first. It writes indexes and reports to repository folders, avoids external LLM APIs, and keeps Salesforce writes out of scope.

## Technology Stack

- Salesforce DX project structure and Salesforce CLI `sf`.
- VS Code with GitHub Copilot.
- GitHub Actions for validation guardrails.
- Python 3.11+ standard-library tools.
- Windows PowerShell command layer through `scripts/workspace.ps1`.
- MCP for read-only local context and configured Azure DevOps Work Item access.
- Knowledge Base sync from a separate Git repository.
- Azure DevOps Wiki Git workflow for draft documentation publication.

## Repository Structure

| Path | Purpose |
| --- | --- |
| `.github/agents/` | Custom Copilot agents. |
| `.github/prompts/` | Slash-command prompt files. |
| `.github/workflows/` | Validation workflows. |
| `.vscode/` | VS Code tasks, settings, MCP config. |
| `.ai/config/` | Example config and local config docs. |
| `.ai/setup/` | First-run and troubleshooting docs. |
| `.ai/skills/python/` | Local deterministic Python tools and tests. |
| `.ai/context/index/` | Generated JSONL context indexes. |
| `.ai/context/work-items/` | Work Item context packs and local artifacts. |
| `.ai/knowledge/` | Curated Knowledge Base notes synced into the workspace. |
| `.ai/deployment/` | Deployment runbooks, gates, and environment placeholders. |
| `.ai/wiki/` | Azure Wiki publication policy, module map, and page template. |
| `config/data-promotion/` | Config object registry, masking policy, and config rules. |
| `docs/` | Architecture, QA, and workspace documentation. |
| `specs/` | Proposed and approved solution design artifacts. |

## Implemented Data Flow

1. Work Item content becomes local artifacts under `.ai/context/work-items/<WORK_ITEM>/`.
2. `.\scripts\workspace.ps1 ai-index-repo` scans local metadata and writes `metadata-components.jsonl`.
3. Optional `.\scripts\workspace.ps1 ai-index-schema -Org ...` reads Salesforce schema with Salesforce CLI.
4. Optional `.\scripts\workspace.ps1 ai-index-config -Org ...` reads only enabled config registry objects and masks output.
5. `.\scripts\workspace.ps1 knowledge-sync` syncs curated notes from the configured external Knowledge Base repo.
6. `.\scripts\workspace.ps1 knowledge-index` writes `knowledge-cards.jsonl`.
7. `.\scripts\workspace.ps1 ai-context` builds a context pack for Copilot prompts.
8. Prompt files produce solution design, review, documentation, QA, and release readiness drafts.
9. `.\scripts\workspace.ps1 wi-precheck` runs local checks against changed files and Work Item artifacts.
10. Azure Wiki tools can prepare draft documentation branches after human review.

## Indexes

| Index | Producer | Notes |
| --- | --- | --- |
| `metadata-components.jsonl` | `index_repo_metadata.py` | Local repo metadata only. |
| `sobject-cards.jsonl` | `index_org_schema.py` | Requires Salesforce CLI auth. |
| `field-cards.jsonl` | `index_org_schema.py` | Requires Salesforce CLI auth. |
| `relationship-cards.jsonl` | `index_org_schema.py` | Requires Salesforce CLI auth. |
| `config-record-cards.jsonl` | `index_config_records.py` | Requires Salesforce CLI auth and enabled registry entries. |
| `knowledge-cards.jsonl` | `index_knowledge.py` | Local curated KB notes. |

Indexes are AI context helpers, not source of truth.

## Context Pack Design

Context packs combine Work Item text, local metadata hits, optional schema/config hits, and Knowledge Base cards. They are written under `.ai/context/work-items/<WORK_ITEM>/context-pack.md`.

The context pack is designed for repeatable prompt input. It should not contain raw data dumps, secrets, or unreviewed exports.

## Config Impact Design

`.\scripts\workspace.ps1 config-impact` reads Work Item context and available config cards to produce `.ai/context/work-items/<WORK_ITEM>/config-impact.yaml` and a Markdown report under `.ai/outputs/config-impact/`.

`.\scripts\workspace.ps1 config-pack-skeleton` can create a review skeleton under `config/kimbleone-packs/<WORK_ITEM>/`. This is not a config apply tool and does not write Salesforce data.

## Knowledge Base Architecture

The Knowledge Base is intended to live in a separate private Git repository. The workspace syncs curated notes into `.ai/knowledge/` and indexes them into `knowledge-cards.jsonl`.

Knowledge Base notes support reasoning, but do not override source-of-truth systems. Draft or stale notes require human validation.

## Azure Wiki Publication Architecture

Azure Wiki support is Git-based and draft-first:

1. Scan a local wiki clone.
2. Choose a placement using module and page rules.
3. Generate a dry-run preview.
4. Require human review.
5. Prepare a draft branch.
6. Push only when explicit approval and local push enablement are present.

The tool does not auto-merge, does not push to the default branch, and does not publish without review.

## MCP Architecture

`.vscode/mcp.json` currently defines:

- `salesforce-context`: local stdio MCP server backed by `.ai/context` indexes. It is read-only.
- `ado-remote-mcp`: HTTP MCP endpoint for Azure DevOps Work Item retrieval. `.\scripts\workspace.ps1 configure` updates the local URL from the configured Azure DevOps organization.

The local MCP server reads only configured context/index paths and exposes context discovery tools. It does not deploy, write Salesforce data, or access arbitrary filesystem roots.

## GitHub Actions

Implemented workflows:

- `validate-work-item.yml`: runs local import and Work Item precheck on pull requests.
- `validate-no-salesforce-ids.yml`: scans for hardcoded Salesforce IDs and raw/export data.
- `salesforce-validate.yml`: optional validate-only Salesforce metadata check when secrets are configured.

The validation workflow uses `sf project deploy validate`; it is validation-only and does not deploy.

## DevOps Center Boundaries

DevOps Center remains the official Salesforce metadata promotion mechanism. Work Item branches are expected to be managed through DevOps Center. This workspace may prepare context, reports, and documentation, but it does not replace DevOps Center.

## Security Model

- GitHub Copilot/Codex-style tooling is the approved AI layer.
- No OpenAI, Anthropic, Gemini, LangChain, or LangGraph integrations are implemented.
- Salesforce auth is handled by Salesforce CLI.
- Local config and vendor clones are ignored.
- MCP access is read-only for local context.
- Config apply and Salesforce writes are not implemented.
- Generated outputs and raw imports are excluded from commits by default.

## Extension Points

Implemented foundations can support later phases:

- Read-only ADO MCP enrichment after org/project setup.
- Salesforce `MetadataComponentDependency` enrichment if approved and scoped.
- Config external key validation and config delta dry-run.
- Wiki PR automation after governance approval.
- Enhanced parsers and local dependency graph generation.

These are not all implemented today; planned items must be labeled as planned until code exists.

## Known Limitations

- Parsing is best-effort and local-first.
- Schema/config indexing requires Salesforce CLI auth.
- Azure DevOps organization remains a local setup value.
- PDF export depends on local PDF tooling.
- Managed package internals remain unavailable.
- Generated reports inform human decisions; they do not approve designs, deployments, config moves, or releases.
