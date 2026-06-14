# Agents, Prompts, Skills, and MCP Reference

This reference inventories files detected in this repository. Items marked planned or optional are not implemented unless a file or command is listed here.

## Custom Agents

| Agent | Path | Purpose | Inputs | Outputs | Risk | Human review | May modify files | Boundaries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Azure Wiki Documentation Agent | `.github/agents/azure-wiki-documentation-agent.agent.md` | Prepare Azure Wiki drafts and placement review. | Work Item docs, source doc, wiki module map. | Draft wiki page and review checklist. | Medium | Yes | Draft docs only | No direct default-branch publish. |
| Implementation Planner | `.github/agents/implementation-planner.agent.md` | Convert approved design into scoped work packets. | Approved design, ACs, context pack. | Work packets. | Medium | Yes | Draft artifacts | Must map to Work Item ACs. |
| Knowledge Curator | `.github/agents/knowledge-curator.agent.md` | Review and shape curated KB notes. | Source note, evidence, owner. | Curated note draft/review. | Medium | Yes | Knowledge docs | No raw dumps or unsupported package claims. |
| QA How-to-Test Writer | `.github/agents/qa-how-to-test-writer.agent.md` | Draft QA how-to-test guidance. | ACs, design, context pack, config impact. | QA how-to-test doc. | Medium | Yes | QA docs | Must not invent test data or package behavior. |
| Release Readiness Reviewer | `.github/agents/release-readiness-reviewer.agent.md` | Review readiness before DevOps Center promotion. | Precheck, QA docs, config impact, validation evidence. | Readiness findings. | High | Yes | Reports only | Does not approve or promote. |
| Salesforce Solution Architect | `.github/agents/solution-architect.agent.md` | Draft solution design. | Work Item, ACs, context pack, metadata evidence. | Solution design. | Medium | Yes | Design docs | No managed package internals assumed. |
| Solution Design Reviewer | `.github/agents/solution-design-reviewer.agent.md` | Review solution design quality and evidence. | Design, ACs, context. | Review findings. | Medium | Yes | Review docs | No auto-approval. |
| Technical Documentation Writer | `.github/agents/tech-doc-writer.agent.md` | Draft technical documentation. | Design, diff, context, QA needs. | Technical docs. | Medium | Yes | Docs | Documentation only, no deploy authority. |
| Work Item Context Curator | `.github/agents/work-item-context-curator.agent.md` | Fetch, normalize, and assemble Work Item context from approved read-only and local sources. | Work Item ID, ADO MCP or pasted content, local indexes. | Work Item summaries, ACs, context gaps, risk notes. | Medium | Yes | Local context artifacts | Read-only ADO; no Salesforce, ADO, deploy, or config writes. |

## Prompt Files

| Slash command | Path | Purpose | Expected inputs | Expected outputs | Draft/file-writing | Safety notes |
| --- | --- | --- | --- | --- | --- | --- |
| `/build-context` | `.github/prompts/build-context.prompt.md` | Build implementation-neutral context pack. | Work Item ID, query, indexes. | Context pack. | File-writing via local tools | Local context only. |
| `/build-knowledge-context` | `.github/prompts/build-knowledge-context.prompt.md` | Build KB-focused context. | Query, KB index. | Relevant KB context. | Draft/context | Human validation for stale notes. |
| `/config-delta-plan` | `.github/prompts/config-delta-plan.prompt.md` | Plan config delta review. | Config impact/cards. | Delta plan. | Draft-only | No config apply. |
| `/config-impact` | `.github/prompts/config-impact.prompt.md` | Analyze config impact. | Work Item, context pack, config cards. | Config impact draft. | File-writing via local tools | Config records are separate from metadata. |
| `/create-documentation` | `.github/prompts/create-documentation.prompt.md` | Draft technical documentation. | Work Item artifacts, design, context. | Docs draft. | Draft/file-writing | Requires Work Item context. |
| `/create-how-to-test` | `.github/prompts/create-how-to-test.prompt.md` | Draft QA how-to-test. | ACs, design, context, config impact. | QA doc. | Draft/file-writing | Do not invent data. |
| `/design-to-work-packets` | `.github/prompts/design-to-work-packets.prompt.md` | Convert design into work packets. | Approved design and ACs. | Work packet YAML/docs. | Draft/file-writing | Keep scoped to Work Item. |
| `/estimate-complexity` | `.github/prompts/estimate-complexity.prompt.md` | Estimate Work Item size and risk before design. | Local Work Item summary and ACs. | Advisory size, risk factors, and proceed/spike/clarify recommendation. | Draft-only | Human sprint-planning review required. |
| `/fetch-us` | `.github/prompts/fetch-us.prompt.md` | Fetch/normalize ADO Work Item context. | Work Item ID or pasted content. | Local Work Item summary and ACs. | File-writing | Read-only ADO MCP only; no ADO writes. |
| `/import-knowledge` | `.github/prompts/import-knowledge.prompt.md` | Create draft KB notes from controlled source. | Source, domain, title, owner. | Draft KB note(s), validation/index steps. | File-writing | No raw dumps or secrets. |
| `/pre-promote-report` | `.github/prompts/pre-promote-report.prompt.md` | Draft pre-promote report. | Precheck, QA, config, docs. | Report draft. | Draft/file-writing | DevOps Center remains promotion tool. |
| `/prepare-wiki-page` | `.github/prompts/prepare-wiki-page.prompt.md` | Prepare Azure Wiki draft. | Work Item, title, source doc, wiki repo. | Wiki draft preview/branch. | File-writing via local tools | Human approval required. |
| `/release-readiness-review` | `.github/prompts/release-readiness-review.prompt.md` | Review release readiness. | Precheck, validation, QA, config. | Readiness review. | Draft-only | No auto-approval. |
| `/review-config-impact` | `.github/prompts/review-config-impact.prompt.md` | Review config impact. | Config impact report. | Findings. | Draft-only | No config apply. |
| `/review-knowledge-note` | `.github/prompts/review-knowledge-note.prompt.md` | Review KB note. | Knowledge note and evidence. | Review findings. | Draft-only | Claims need evidence. |
| `/review-qa-how-to-test` | `.github/prompts/review-qa-how-to-test.prompt.md` | Review QA doc. | QA doc, ACs, design. | Findings. | Draft-only | Test data placeholders required. |
| `/review-wiki-publication` | `.github/prompts/review-wiki-publication.prompt.md` | Review wiki publication readiness. | Wiki draft and placement. | Approval checklist. | Draft-only | Push requires explicit approval. |
| `/solution-design-review` | `.github/prompts/solution-design-review.prompt.md` | Review solution design. | Design and evidence. | Review findings. | Draft-only | No auto-approval. |
| `/solution-design` | `.github/prompts/solution-design.prompt.md` | Generate solution design. | Work Item, ACs, context pack. | Design draft. | Draft/file-writing | Evidence-labeled; no internals assumed. |
| `/sync-knowledge` | `.github/prompts/sync-knowledge.prompt.md` | Sync KB repo. | Repo URL/path and branch. | Synced notes/index. | File-writing via local tools | No external model APIs or Salesforce calls. |
| `/update-documentation-from-diff` | `.github/prompts/update-documentation-from-diff.prompt.md` | Update docs from implementation diff. | Diff, Work Item, docs. | Updated docs draft. | Draft/file-writing | Human review required. |
| `/wiki-placement-review` | `.github/prompts/wiki-placement-review.prompt.md` | Review wiki placement. | Module map, source doc, proposed path. | Placement findings. | Draft-only | Avoid overwriting reviewed docs. |

## Python Tools And Commands

| Module | Command | Purpose | Reads | Writes | Salesforce auth | Network | Destructive |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ai_workspace.configuration.bootstrap` | `.\scripts\workspace.ps1 setup` | Initialize local folders/config. | Config examples. | Local config/folders. | No | No | No |
| `scripts.configure` | `.\scripts\workspace.ps1 configure` | Prompt for local config values and patch MCP URL. | Config examples. | Ignored local config and `.vscode/mcp.json`. | No | No | No |
| `ai_workspace.configuration.doctor` | `.\scripts\workspace.ps1 doctor` | Validate environment/config. | Local files/config. | Doctor reports. | Optional strict | No | No |
| `ai_workspace.indexers.index_repo_metadata` | `.\scripts\workspace.ps1 ai-index-repo` | Index local metadata. | `force-app/` if present. | `metadata-components.jsonl`. | No | No | No |
| `ai_workspace.indexers.index_org_schema` | `.\scripts\workspace.ps1 ai-index-schema` | Read Salesforce schema via CLI. | Salesforce org schema. | schema cards. | Yes | Salesforce CLI | No |
| `ai_workspace.indexers.index_config_records` | `.\scripts\workspace.ps1 ai-index-config` | Read allowed config records. | Registry and Salesforce org. | masked config cards. | Yes | Salesforce CLI | No |
| `ai_workspace.indexers.build_context_pack` | `.\scripts\workspace.ps1 ai-context` | Build Work Item context pack. | Work Item artifacts and indexes. | context pack and source maps. | No | No | No |
| `ai_workspace.config.config_impact` | `.\scripts\workspace.ps1 config-impact` | Analyze config impact. | Work Item artifacts and config index. | YAML/report. | No | No | No |
| `ai_workspace.config.config_pack_builder` | `.\scripts\workspace.ps1 config-pack-skeleton` | Create review skeleton. | Config impact YAML. | config pack skeleton. | No | No | No apply |
| `ai_workspace.config.config_diff` | Python module only | Compare config snapshots. | JSONL snapshots. | Diff output when invoked. | No | No | No |
| `ai_workspace.deployment.precheck_work_item` | `.\scripts\workspace.ps1 wi-precheck` | Local Work Item precheck. | Git diff and artifacts. | precheck reports. | No | No | No |
| `ai_workspace.deployment.validate_metadata_scope` | Included in precheck | Validate scope artifacts. | Metadata scope files. | Findings. | No | No | No |
| `ai_workspace.knowledge.sync_knowledge_repo` | `.\scripts\workspace.ps1 knowledge-sync` | Sync configured external KB repo. | Git repo from local config/env/override. | `.ai/knowledge/`, vendor clone. | No | Git | No |
| `ai_workspace.knowledge.create_knowledge` | `.\scripts\workspace.ps1 knowledge-create` | Convert controlled source into structured draft KB note(s). | PDF/CSV/MD/TXT/XML source or manifest. | KB notes/report. | No | No | No |
| `ai_workspace.knowledge.import_knowledge` | `.\scripts\workspace.ps1 knowledge-import` | Backward-compatible alias implementation for KB creation. | Local source/manifest. | KB note/report. | No | No | No |
| `ai_workspace.knowledge.validate_knowledge` | `.\scripts\workspace.ps1 knowledge-validate` | Validate KB schema, quality, freshness, secrets, and Salesforce ID rules. | `.ai/knowledge/`, schema. | validation reports. | No | No | No |
| `ai_workspace.knowledge.index_knowledge` | `.\scripts\workspace.ps1 knowledge-index`, `.\scripts\workspace.ps1 knowledge-index-yaml` | Index curated KB notes and optional per-file YAML. | `.ai/knowledge/`. | `knowledge-cards.jsonl`, YAML index. | No | No | No |
| `ai_workspace.knowledge.metadata_to_knowledge` | `.\scripts\workspace.ps1 metadata-knowledge-index` | Build local metadata-derived knowledge cards. | `force-app/`. | metadata knowledge index. | No | No | No |
| `ai_workspace.knowledge.build_graph` | `.\scripts\workspace.ps1 knowledge-graph` | Build semantic graph across notes, source files, objects, fields, metadata, processes, business rules, and Work Items. | local indexes. | `knowledge-graph.json`. | No | No | No |
| `ai_workspace.knowledge.knowledge_search` | `.\scripts\workspace.ps1 knowledge-search` | BM25 search over knowledge cards with semantic filters. | KB index. | Console output. | No | No | No |
| `ai_workspace.mcp.salesforce_context_mcp` | `.\scripts\workspace.ps1 mcp-salesforce-context` | Read-only context MCP. | `.ai/context`. | JSON-RPC responses. | No | Local stdio | No |
| `ai_workspace.wiki.wiki_publisher` | `.\scripts\workspace.ps1 wiki-dry-run`, `.\scripts\workspace.ps1 wiki-prepare-branch`, `.\scripts\workspace.ps1 wiki-push-approved` | Prepare Azure Wiki draft branch from configured wiki repo. | Docs and wiki repo. | previews/branch. | No | Git | Push only when explicitly approved |
| `ai_workspace.wiki.wiki_scanner` | `.\scripts\workspace.ps1 wiki-scan` | Scan wiki clone. | local wiki clone. | wiki index JSON. | No | No | No |
| `ai_workspace.docs.export_docs` | `.\scripts\workspace.ps1 docs-build`, `.\scripts\workspace.ps1 docs-export-pdf` | Validate docs and export PDFs if tools exist. | `docs/workspace`. | PDFs or manual README. | No | No | No |

## MCP Servers

| Server | Config | Purpose | Tools/capability | Read/write | Allowed roots | Forbidden actions |
| --- | --- | --- | --- | --- | --- | --- |
| `salesforce-context` | `.vscode/mcp.json` stdio Python module | Local context discovery from generated indexes. | Tools are exposed by `ai_workspace.mcp.salesforce_context_mcp`. | Read-only | `.ai/context/index`, `.ai/context` | No deploy, no Salesforce writes, no config apply, no arbitrary filesystem access. |
| `ado-remote-mcp` | `.vscode/mcp.json` HTTP `https://mcp.dev.azure.com/YOUR_ADO_ORG` | Azure DevOps Work Item retrieval when configured. | External Microsoft Azure DevOps MCP server. | Intended read-only for Work Items. | Azure DevOps service scope configured by user auth. | No ADO writes, transitions, assignments, comments, or branch creation from this workspace. |

Salesforce CLI is used by local tools for schema/config reads and optional validate-only CI. No Salesforce write or deployment automation is implemented.

## GitHub Actions

| Workflow | Trigger | Purpose | Requires secrets | Deploys |
| --- | --- | --- | --- | --- |
| `.github/workflows/validate-work-item.yml` | Pull request | Python import check and local Work Item precheck. | No | No |
| `.github/workflows/validate-no-salesforce-ids.yml` | Pull request | Hardcoded Salesforce ID and raw/export data scan. | No | No |
| `.github/workflows/salesforce-validate.yml` | Pull request, manual dispatch | Optional validate-only Salesforce deployment check. | Yes, for validation org auth | No; uses validate-only command. |

## Planned Or Optional, Not Fully Implemented Here

- Read-only ADO Work Item retrieval depends on VS Code MCP configuration and user auth.
- Metadata and knowledge graph generation is implemented through `.\scripts\workspace.ps1 metadata-knowledge-index` and `.\scripts\workspace.ps1 knowledge-graph`.
- Config external key validator and config delta dry-run wrapper targets are planned; only `config_diff.py` is present as a direct Python module.
- Automated wiki PR creation is not implemented.
- Production config apply is not implemented.
