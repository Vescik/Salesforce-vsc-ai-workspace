# Appendix: Command Reference

Commands are defined in `scripts/workspace.ps1`. Commands marked "writes files" create or update local artifacts only unless otherwise noted.

## Setup And Config

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `.\scripts\workspace.ps1 help` | Show command list. | No | No | Safe. |
| `.\scripts\workspace.ps1 setup` | Bootstrap local workspace config/folders. | No | Yes | No Salesforce calls. |
| `.\scripts\workspace.ps1 setup-venv` | Bootstrap and create local venv. | No | Yes | Venv is ignored. |
| `.\scripts\workspace.ps1 configure` | Create/update ignored local config. | No | Yes | Do not commit local config. |
| `.\scripts\workspace.ps1 first-run` | Setup, doctor, repo index, knowledge index. | No | Yes | Local-only. |

## Doctor And Testing

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `.\scripts\workspace.ps1 doctor` | Validate local setup. | No | Yes | Writes doctor reports. |
| `.\scripts\workspace.ps1 doctor-strict` | Strict checks including optional auth/KB. | Optional | Yes | May warn/fail without auth. |
| `.\scripts\workspace.ps1 ai-check-python` | Import important modules. | No | No | Fast health check. |
| `.\scripts\workspace.ps1 test` | Run unit tests. | No | No | Standard-library unittest. |
| `.\scripts\workspace.ps1 smoke` | Run local smoke path. | No | Yes | Does not require org auth. |

## Indexing

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `.\scripts\workspace.ps1 ai-index-repo` | Index local repo metadata. | No | Yes | Reads `force-app` if present. |
| `.\scripts\workspace.ps1 ai-index-schema -Org IntDev` | Index Salesforce schema. | Yes | Yes | Read-only Salesforce CLI calls. |
| `.\scripts\workspace.ps1 ai-index-config -Org IntDev` | Index enabled config registry objects. | Yes | Yes | Read-only and masked. |
| `.\scripts\workspace.ps1 ai-index-all -Org IntDev` | Run repo, knowledge, schema, and config indexes. | Yes | Yes | Requires org auth for schema/config. |

## Knowledge

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `.\scripts\workspace.ps1 knowledge-sync-dry-run -KbRepo <repo>` | Preview KB sync. | Git repo access | Yes | Writes reports only. |
| `.\scripts\workspace.ps1 knowledge-sync -KbRepo <repo>` | Sync curated KB notes. | Git repo access | Yes | Vendor clone ignored. |
| `.\scripts\workspace.ps1 knowledge-index` | Index KB notes. | No | Yes | Writes `knowledge-cards.jsonl`. |
| `.\scripts\workspace.ps1 knowledge-create ...` | Convert controlled source to structured draft KB notes. | No | Yes | PDF/CSV/MD/TXT/XML; no raw dumps/secrets. |
| `.\scripts\workspace.ps1 knowledge-create-dry-run ...` | Preview source conversion without writing notes. | No | No | Writes no notes or reports. |
| `.\scripts\workspace.ps1 knowledge-create-manifest ...` | Create notes from manifest. | No | Yes | Uses local manifest. |
| `.\scripts\workspace.ps1 knowledge-import ...` | Backward-compatible alias for `knowledge-create`. | No | Yes | Kept for existing prompts/tasks. |
| `.\scripts\workspace.ps1 knowledge-import-manifest ...` | Backward-compatible alias for `knowledge-create-manifest`. | No | Yes | Kept for existing prompts/tasks. |
| `.\scripts\workspace.ps1 knowledge-validate` | Validate note schema, freshness, quality, secrets, and Salesforce IDs. | No | Yes | Writes validation reports. |
| `.\scripts\workspace.ps1 metadata-knowledge-index` | Build local metadata knowledge cards from `force-app`. | No | Yes | Local-only derived index. |
| `.\scripts\workspace.ps1 knowledge-index-yaml` | Emit machine-readable per-file KB index YAML. | No | Yes | Used by MCP slug lookup. |
| `.\scripts\workspace.ps1 knowledge-graph` | Build semantic KB graph. | No | Yes | Notes, source files, objects, fields, metadata, business rules. |
| `.\scripts\workspace.ps1 knowledge-search -Query "<topic>"` | Search KB cards with BM25 and semantic fields. | No | No | Optional filters via `-KnowledgeSearchFlags`. |

## Context

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `.\scripts\workspace.ps1 ai-context -WorkItem <id> -Query "<topic>"` | Build Work Item context pack. | No | Yes | Uses local indexes. |
| `.\scripts\workspace.ps1 ai-context-auto -WorkItem <id>` | Build Work Item context pack from AC keywords. | No | Yes | Extracts query terms from local Work Item artifacts. |
| `.\scripts\workspace.ps1 ai-context-example` | Build example context. | No | Yes | Example generated files are ignored. |
| `.\scripts\workspace.ps1 ai-list-outputs -WorkItem <id>` | List generated outputs. | No | No | Diagnostic. |
| `.\scripts\workspace.ps1 ai-clean-context` | Remove generated context indexes/files. | No | Yes | Deletes generated local artifacts only. |
| `.\scripts\workspace.ps1 clean-ai-generated` | Remove generated JSON/log files. | No | Yes | Local cleanup. |

## Prompt Workflow

| Prompt | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `/fetch-us <id>` | Fetch or normalize Work Item context. | ADO MCP optional | Yes | Read-only ADO MCP or pasted fallback. |
| `/solution-design <id>` | Draft solution design. | No | Draft docs | Evidence-labeled. |
| `/solution-design-review <id>` | Review design. | No | Draft review | Human approval still required. |
| `/design-to-work-packets <id>` | Create work packets. | No | Draft packets | Must map to ACs. |
| `/create-documentation <id>` | Draft docs. | No | Draft docs | Uses local artifacts. |
| `/create-how-to-test <id>` | Draft QA how-to-test. | No | Draft docs | Do not invent data. |
| `/pre-promote-report <id>` | Draft pre-promote report. | No | Draft report | Does not promote. |

## Config Impact

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `.\scripts\workspace.ps1 config-impact -WorkItem <id>` | Analyze config impact. | No | Yes | Uses local config cards if present. |
| `.\scripts\workspace.ps1 config-pack-skeleton -WorkItem <id>` | Create config skeleton. | No | Yes | Review artifact only; no apply. |

## Precheck

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `.\scripts\workspace.ps1 ac-coverage -WorkItem <id>` | Check design coverage for each acceptance criterion. | No | Yes | Writes AC coverage and traceability artifacts. |
| `.\scripts\workspace.ps1 design-lint -WorkItem <id>` | Lint solution design evidence and metadata references. | No | Yes | Fails on blocking findings. |
| `.\scripts\workspace.ps1 wi-precheck -WorkItem <id> -BaseRef <ref>` | Local Work Item precheck. | No | Yes | Advisory findings. |
| `.\scripts\workspace.ps1 wi-precheck-strict -WorkItem <id> -BaseRef <ref>` | Strict precheck. | No | Yes | Fails on high findings. |
| `.\scripts\workspace.ps1 wi-scope-check -WorkItem <id>` | Scope check wrapper. | No | Yes | Calls precheck. |

## MCP

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `.\scripts\workspace.ps1 mcp-salesforce-context` | Start local MCP server. | No | No | Read-only stdio. |
| `.\scripts\workspace.ps1 mcp-smoke-test` | List MCP tools through JSON-RPC. | No | No | Local smoke check. |

## Azure Wiki

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `.\scripts\workspace.ps1 wiki-dry-run ...` | Prepare preview. | Git repo access | Yes | No push. |
| `.\scripts\workspace.ps1 wiki-prepare-branch ...` | Create local draft branch/commit. | Git repo access | Yes | Vendor clone ignored. |
| `.\scripts\workspace.ps1 wiki-push-approved ...` | Push approved branch. | Git repo access | Yes/push | Requires approval note and push enablement. |
| `.\scripts\workspace.ps1 wiki-scan ...` | Scan local wiki clone. | No | Yes | Local clone only. |

## Documentation Pack

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `.\scripts\workspace.ps1 docs-build` | Validate docs package. | No | No | Local check. |
| `.\scripts\workspace.ps1 docs-export-pdf` | Export PDFs if tool exists. | No | Yes | Writes manual instructions if no PDF tool. |
| `.\scripts\workspace.ps1 docs-pack` | Run docs build and PDF export. | No | Yes | Local-only. |
| `.\scripts\workspace.ps1 docs-open-html` | Print/open HTML runbook path. | No | No | Offline HTML. |

## GitHub Publishing

No workspace publishing target is implemented. Repository creation, commit, and push remain manual and approval-gated.
