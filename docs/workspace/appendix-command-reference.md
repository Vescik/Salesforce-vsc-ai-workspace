# Appendix: Command Reference

Commands are defined in `Makefile`. Commands marked "writes files" create or update local artifacts only unless otherwise noted.

## Setup And Config

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `make help` | Show command list. | No | No | Safe. |
| `make setup` | Bootstrap local workspace config/folders. | No | Yes | No Salesforce calls. |
| `make setup-venv` | Bootstrap and create local venv. | No | Yes | Venv is ignored. |
| `make configure` | Create/update ignored local config. | No | Yes | Do not commit local config. |
| `make first-run` | Setup, doctor, repo index, knowledge index. | No | Yes | Local-only. |

## Doctor And Testing

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `make doctor` | Validate local setup. | No | Yes | Writes doctor reports. |
| `make doctor-strict` | Strict checks including optional auth/KB. | Optional | Yes | May warn/fail without auth. |
| `make ai-check-python` | Import important modules. | No | No | Fast health check. |
| `make test` | Run unit tests. | No | No | Standard-library unittest. |
| `make smoke` | Run local smoke path. | No | Yes | Does not require org auth. |

## Indexing

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `make ai-index-repo` | Index local repo metadata. | No | Yes | Reads `force-app` if present. |
| `make ai-index-schema ORG=IntDev` | Index Salesforce schema. | Yes | Yes | Read-only Salesforce CLI calls. |
| `make ai-index-config ORG=IntDev` | Index enabled config registry objects. | Yes | Yes | Read-only and masked. |
| `make ai-index-all ORG=IntDev` | Run repo, knowledge, schema, and config indexes. | Yes | Yes | Requires org auth for schema/config. |

## Knowledge

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `make knowledge-sync-dry-run KB_REPO=<repo>` | Preview KB sync. | Git repo access | Yes | Writes reports only. |
| `make knowledge-sync KB_REPO=<repo>` | Sync curated KB notes. | Git repo access | Yes | Vendor clone ignored. |
| `make knowledge-index` | Index KB notes. | No | Yes | Writes `knowledge-cards.jsonl`. |
| `make knowledge-search QUERY="<topic>"` | Search KB cards. | No | No | Local index search. |
| `make knowledge-import ...` | Convert controlled source to KB note. | No | Yes | No raw dumps/secrets. |
| `make knowledge-import-manifest ...` | Import from manifest. | No | Yes | Uses local manifest. |

## Context

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `make ai-context WORK_ITEM=<id> QUERY="<topic>"` | Build Work Item context pack. | No | Yes | Uses local indexes. |
| `make ai-context-example` | Build example context. | No | Yes | Example generated files are ignored. |
| `make ai-list-outputs WORK_ITEM=<id>` | List generated outputs. | No | No | Diagnostic. |
| `make ai-clean-context` | Remove generated context indexes/files. | No | Yes | Deletes generated local artifacts only. |
| `make clean-ai-generated` | Remove generated JSON/log files. | No | Yes | Local cleanup. |

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
| `make config-impact WORK_ITEM=<id>` | Analyze config impact. | No | Yes | Uses local config cards if present. |
| `make config-pack-skeleton WORK_ITEM=<id>` | Create config skeleton. | No | Yes | Review artifact only; no apply. |

## Precheck

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `make wi-precheck WORK_ITEM=<id> BASE_REF=<ref>` | Local Work Item precheck. | No | Yes | Advisory findings. |
| `make wi-precheck-strict WORK_ITEM=<id> BASE_REF=<ref>` | Strict precheck. | No | Yes | Fails on high findings. |
| `make wi-scope-check WORK_ITEM=<id>` | Scope check wrapper. | No | Yes | Calls precheck. |

## MCP

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `make mcp-salesforce-context` | Start local MCP server. | No | No | Read-only stdio. |
| `make mcp-smoke-test` | List MCP tools through JSON-RPC. | No | No | Local smoke check. |

## Azure Wiki

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `make wiki-dry-run ...` | Prepare preview. | Git repo access | Yes | No push. |
| `make wiki-prepare-branch ...` | Create local draft branch/commit. | Git repo access | Yes | Vendor clone ignored. |
| `make wiki-push-approved ...` | Push approved branch. | Git repo access | Yes/push | Requires approval note and push enablement. |
| `make wiki-scan ...` | Scan local wiki clone. | No | Yes | Local clone only. |

## Documentation Pack

| Command | Purpose | Requires auth | Writes files | Notes |
| --- | --- | --- | --- | --- |
| `make docs-build` | Validate docs package. | No | No | Local check. |
| `make docs-export-pdf` | Export PDFs if tool exists. | No | Yes | Writes manual instructions if no PDF tool. |
| `make docs-pack` | Run docs build and PDF export. | No | Yes | Local-only. |
| `make docs-open-html` | Print HTML runbook path. | No | No | Offline HTML. |

## GitHub Publishing

No Makefile publishing target is implemented. Phase 20 prepared a dry-run plan and staged safe files, but GitHub repository creation, commit, and push remain manual and approval-gated.
