# AI-CONTEXT: Salesforce VSC AI Workspace

> **Purpose of this file:** Single-file reference for AI assistants (Claude, Copilot, Codex, Gemini, etc.) to understand this workspace without exploring the full repository. Attach this file to any AI chat session to provide complete context. Last updated: 2026-06-13.

---

## 1. What This Workspace Is

A **local, deterministic, Copilot-only AI assistance layer** for Salesforce development on top of the closed **KimbleOne/Kantata** managed package. It does NOT deploy to Salesforce, does NOT call external LLM APIs, and does NOT automate releases. It helps developers:

- Build context packs for Work Items
- Generate solution designs, QA docs, and technical documentation
- Index Salesforce org schema and config records locally
- Run pre-promote checks before DevOps Center promotion
- Curate and sync an internal knowledge base about the managed package
- Prepare Azure DevOps Wiki documentation drafts

**GitHub repos:**
- Workspace: `https://github.com/Vescik/Salesforce-vsc-ai-workspace`
- Knowledge Base (private): `https://github.com/Vescik/Salesforce-knowledge-base`

**Tech stack:** Python 3.11+ (stdlib only, zero runtime pip deps), Salesforce CLI (`sf`), VS Code + GitHub Copilot, Azure DevOps MCP (read-only).

---

## 2. Hard Rules for AI Assistants

These rules are absolute. Do not deviate.

| Rule | Detail |
|---|---|
| **No external LLM APIs** | Never suggest or scaffold OpenAI, Anthropic, LangChain, or any provider API |
| **No Salesforce writes** | Never write to, deploy to, or apply config to any Salesforce org |
| **No autonomous deployment** | DevOps Center is the only approved metadata promotion path |
| **No invented branch names** | Branch names come from DevOps Center / team config — use placeholders |
| **No raw data commits** | No Salesforce IDs, record IDs, PII, tokens, or credentials in any file |
| **IntDev ≠ source of truth** | IntDev is a shared Full Copy sandbox — not git-managed |
| **No KB guessing** | Never invent KimbleOne/Kantata internals beyond documented knowledge |
| **Draft-first wiki** | All Azure Wiki changes require human review and approval before push |
| **ADO MCP = read-only** | Only `/fetch-us` — never create, update, or transition Work Items |
| **KB claims need citations** | Every fact from KB must reference the source note path |

---

## 3. Repository Structure

```
/
├── AI-CONTEXT.md                    ← THIS FILE — AI orientation guide
├── README.md                        ← Human-readable project overview
├── QUICKSTART.md                    ← Fast setup guide
├── AGENTS.md                        ← AI assistant rules (short form)
├── Makefile                         ← All workspace commands (Mac/Linux)
├── pyproject.toml                   ← Python package config (zero runtime deps)
├── sfdx-project.json                ← Salesforce DX project (API v64.0)
├── .forceignore                     ← Salesforce metadata ignore rules
├── .gitignore                       ← Excludes: workspace.local.json, vendor/, indexes, outputs
│
├── force-app/main/default/          ← Salesforce metadata (Apex, LWC, Flows, etc.)
├── manifest/package.xml             ← Salesforce package manifest
│
├── specs/
│   ├── proposed/                    ← Work Item solution designs (pre-approval)
│   └── approved/                    ← Approved solution designs
│
├── docs/
│   ├── architecture/                ← Architecture docs per Work Item
│   ├── qa-how-to-test/              ← QA test instructions per Work Item
│   └── workspace/                   ← Workspace documentation (installation, runbooks)
│
├── config/
│   └── data-promotion/
│       ├── config-object-registry.yaml   ← Which Salesforce config objects to index
│       └── masking-policy.yaml           ← PII/sensitive field masking rules
│
├── scripts/
│   ├── workspace.ps1                ← Windows PowerShell: ALL make targets
│   ├── setup.ps1 / setup.py / setup.sh  ← Platform-specific setup
│   ├── doctor.ps1 / doctor.py / doctor.sh
│   └── configure.py
│
├── .github/
│   ├── copilot-instructions.md      ← Copilot system instructions (authoritative rules)
│   ├── agents/                      ← 10 custom Copilot agents (see §8)
│   ├── prompts/                     ← 23 slash-command prompts (see §9)
│   └── workflows/
│       ├── validate-work-item.yml   ← CI: infer Work Item ID, run precheck
│       ├── salesforce-validate.yml  ← CI: Salesforce metadata validation
│       └── validate-no-salesforce-ids.yml  ← CI: scan for hardcoded IDs
│
├── .ai/                             ← AI workspace data root
│   ├── config/
│   │   ├── workspace.local.json     ← LOCAL config (gitignored, not committed)
│   │   ├── workspace.example.json   ← Template for workspace.local.json
│   │   └── workspace.local.json.example
│   ├── context/
│   │   ├── index/                   ← Generated indexes (gitignored *.jsonl)
│   │   │   ├── metadata-components.jsonl    ← Repo metadata index
│   │   │   ├── schema-cards.jsonl           ← Salesforce org schema
│   │   │   ├── config-record-cards.jsonl    ← Masked config records
│   │   │   └── knowledge-cards.jsonl        ← KB search index
│   │   └── work-items/<WORK_ITEM>/  ← Per-Work-Item context artifacts
│   │       ├── work-item-summary.md         ← Fetched ADO Work Item
│   │       ├── acceptance-criteria.md
│   │       ├── context-pack.md              ← Built context pack
│   │       └── config-impact.yaml           ← Config impact analysis
│   ├── deployment/
│   │   ├── environments.yaml        ← Pipeline env definitions
│   │   ├── branch-map.yaml          ← Branch name placeholders
│   │   ├── gates.yaml               ← Promotion gate rules
│   │   └── runbooks/                ← Deployment runbooks
│   ├── knowledge/                   ← Local KB copy (synced from KB repo)
│   │   ├── index.yaml               ← KB domain index
│   │   ├── sync-policy.yaml         ← What to copy from KB repo
│   │   ├── domains/                 ← Domain knowledge notes
│   │   ├── object-notes/            ← Salesforce object notes
│   │   ├── process-maps/            ← End-to-end process docs
│   │   ├── decisions/               ← Architecture Decision Records
│   │   └── governance/              ← Data handling policies
│   ├── outputs/                     ← AI-generated reports (gitignored)
│   ├── setup/                       ← Setup docs (first-run, prerequisites)
│   ├── skills/python/               ← Python toolchain (see §7)
│   ├── state/work-items/            ← Work Item processing state
│   ├── templates/                   ← Document templates
│   └── wiki/                        ← Wiki config (module-map, policy)
│
└── .vscode/
    ├── mcp.json                     ← MCP server config (ADO + Salesforce context)
    ├── settings.json                ← VS Code settings
    └── tasks.json                   ← VS Code tasks
```

---

## 4. Configuration: `workspace.local.json`

This file is **gitignored** and must be created locally by each developer. It lives at `.ai/config/workspace.local.json`.

```json
{
  "version": 1,
  "workspace": { "name": "salesforce-ai-workspace" },
  "paths": {
    "repo_root": ".",
    "ai_root": ".ai",
    "python_tools_root": ".ai/skills/python",
    "context_root": ".ai/context",
    "context_index_dir": ".ai/context/index",
    "work_items_dir": ".ai/context/work-items",
    "outputs_dir": ".ai/outputs",
    "knowledge_root": ".ai/knowledge",
    "knowledge_vendor_dir": ".ai/vendor/knowledge-base",
    "specs_proposed_dir": "specs/proposed",
    "specs_approved_dir": "specs/approved",
    "qa_docs_dir": "docs/qa-how-to-test",
    "architecture_docs_dir": "docs/architecture"
  },
  "salesforce": {
    "default_dev_org_alias": "IntDev",
    "validation_org_alias": "",
    "login_url": "https://login.salesforce.com",
    "use_devops_center": true
  },
  "knowledge_base": {
    "enabled": true,
    "repo_url": "https://github.com/Vescik/Salesforce-knowledge-base.git",
    "branch": "main",
    "sync_on_setup": false
  },
  "azure_devops": {
    "enabled": true,
    "organization": "YOUR_ADO_ORG",
    "default_project": "",
    "mcp_server_name": "ado-remote-mcp"
  },
  "azure_wiki": {
    "enabled": false,
    "repo_url": "",
    "push_enabled": false,
    "require_human_approval": true
  },
  "python": { "min_version": "3.11", "use_venv": true, "venv_path": ".venv" },
  "security": {
    "allow_salesforce_writes": false,
    "allow_config_apply": false,
    "allow_external_llm_apis": false
  }
}
```

**Never commit this file.** It may contain local paths and repo URLs but never tokens, passwords, or credentials.

---

## 5. Core Concepts

### KimbleOne / Kantata

A closed Salesforce managed package for professional services automation (PSA). Object prefix: `kmbi__`. The workspace does NOT have access to package source code. All knowledge about the package comes from:
- Local Salesforce org schema index (`schema-cards.jsonl`)
- Anonymized config record index (`config-record-cards.jsonl`)
- Internal Knowledge Base notes (`.ai/knowledge/`)
- Human-provided facts in ADO Work Items

### Work Item

An Azure DevOps Work Item (e.g. `KIM-1234`) is the unit of work. Everything traces to a Work Item ID:
- Branch: DevOps Center-managed work item branch
- Context: `.ai/context/work-items/KIM-1234/`
- Specs: `specs/proposed/KIM-1234.solution-design.md`
- Docs: `docs/architecture/KIM-1234.md`, `docs/qa-how-to-test/KIM-1234.md`
- Precheck: `.ai/outputs/precheck/KIM-1234.precheck.md`

### DevOps Center Pipeline

Official Salesforce metadata promotion path. Never bypassed.

```
IntDev (Full Copy, not git) → UAT → Staging → Production
```

Branch names come from DevOps Center — never invent them. Use placeholders: `<DEVOPS_CENTER_WORK_ITEM_BRANCH>`, `<UAT_BRANCH>`, `<STAGE_BRANCH>`, `<PROD_BRANCH>`.

### Knowledge Base (KB)

Separate private Git repo (`Vescik/Salesforce-knowledge-base`) containing curated internal notes about the KimbleOne package. Synced locally via `make knowledge-sync`. Indexed into `knowledge-cards.jsonl` for fast search. Structure:

```
domains/<domain>/<note>.md    ← Business domain knowledge
object-notes/<Object>.md      ← Per-Salesforce-object notes
process-maps/<process>.md     ← End-to-end process flows
decisions/ADR-NNN-<title>.md  ← Architecture decisions
governance/<policy>.md        ← Data / access policies
```

Note frontmatter fields: `title`, `domain`, `status` (draft/reviewed), `confidence` (low/medium/high), `last_reviewed`, `related_objects`, `keywords`.

**Rule:** Only `status: reviewed` + `confidence: medium|high` notes should be acted upon without explicit human confirmation.

### MCP Servers (VS Code)

Configured in `.vscode/mcp.json`:
- **`ado-remote-mcp`** — Read-only Azure DevOps Work Item access. Used by `/fetch-us` prompt. Replace `YOUR_ADO_ORG` with actual org name in local VS Code settings.
- **`salesforce-context`** — Local Python MCP server exposing indexes to Copilot via `python -m ai_workspace.mcp.salesforce_context_mcp`.

---

## 6. Key Salesforce Objects (KimbleOne/Kantata)

| Object | Purpose | Key Fields |
|---|---|---|
| `kmbi__Invoice__c` | Customer invoice | `kmbi__Status__c` (Draft→Pending Approval→Approved→Dispatched), `kmbi__TotalAmount__c` (rollup), `kmbi__Project__c`, `kmbi__BillingSchedule__c` |
| `kmbi__InvoiceLine__c` | Invoice line items | Child of `kmbi__Invoice__c` |
| `kmbi__BillingSchedule__c` | Billing schedule per project | `kmbi__BillingType__c` (T&M or Fixed Price) |
| `kmbi__BillingScheduleLine__c` | Individual billing line | `kmbi__Status__c` (Billed locks the line) |
| `kmbi__TimeEntry__c` | Single logged time row | `kmbi__Hours__c`, `kmbi__Date__c`, `kmbi__BillingStatus__c`, `kmbi__Timesheet__c` (master-detail) |
| `kmbi__Timesheet__c` | Weekly timesheet container | `kmbi__Status__c` (Open→Submitted→Approved\|Returned) |
| `kmbi__Resource__c` | Bookable person | `kmbi__User__c` (1:1 with User), `kmbi__IsActive__c`, `kmbi__Capacity__c` |
| `kmbi__ResourceRequest__c` | Staffing request | `kmbi__Status__c` (Draft→Submitted→Approved→In Progress→Fulfilled\|Rejected) |
| `kmbi__ResourceBooking__c` | Resource-to-project allocation | Created by Resource Manager against an approved request |
| `kmbi__Expense__c` | Expense claim | Requires receipt attachment unless category marked exempt |
| `kmbi__Project__c` | Project record | Parent of billing schedules, resource requests, timesheets |
| `kmbi__ProjectPhase__c` | Project phase | Time entries logged against phases in `Active` status only |

**Package constraints to remember:**
- `kmbi__` picklist values are managed — cannot be extended without package customization
- Approved timesheets and billed invoice lines are locked — require `KimbleOne Admin` permission set to edit
- One `kmbi__Resource__c` per Salesforce User (unique validation rule)
- Overlapping resource bookings for same resource/dates are blocked by managed validation

---

## 7. Python Toolchain

All Python code lives in `.ai/skills/python/ai_workspace/`. **PYTHONPATH must be `.ai/skills/python`** when running any module. Zero runtime pip dependencies (stdlib only).

### Module Map

| Module | `python -m` entrypoint | Purpose |
|---|---|---|
| `configuration.bootstrap` | ✓ | Initial workspace setup, venv creation, local config scaffolding |
| `configuration.doctor` | ✓ | Health check: Python version, tools, paths, Salesforce auth, KB |
| `configuration.workspace_config` | — | Load/validate `workspace.local.json` |
| `indexers.index_repo_metadata` | ✓ | Scan `force-app/` and produce `metadata-components.jsonl` |
| `indexers.index_org_schema` | ✓ | Query Salesforce org for `kmbi__` schema → `schema-cards.jsonl` |
| `indexers.index_config_records` | ✓ | Query config objects from registry → `config-record-cards.jsonl` (masked) |
| `indexers.build_context_pack` | ✓ | Search all indexes by query → `context-pack.md` for a Work Item |
| `knowledge.sync_knowledge_repo` | ✓ | Clone/pull KB repo → copy notes to `.ai/knowledge/` per sync-policy |
| `knowledge.index_knowledge` | ✓ | Index `.ai/knowledge/` → `knowledge-cards.jsonl` |
| `knowledge.import_knowledge` | ✓ | Import a raw source file → draft knowledge note |
| `knowledge.knowledge_search` | ✓ | Search `knowledge-cards.jsonl` by query |
| `config.config_impact` | ✓ | Analyze Work Item context → config impact report |
| `config.config_pack_builder` | ✓ | Build config pack skeleton from impact report |
| `config.config_diff` | — | Diff config record snapshots |
| `deployment.precheck_work_item` | ✓ | Pre-promote check: git diff scope, Work Item traceability |
| `deployment.validate_metadata_scope` | — | Validate metadata files are in scope for Work Item |
| `deployment.git_utils` | — | Git helpers (diff, log, file lists) |
| `mcp.salesforce_context_mcp` | ✓ | MCP server exposing indexes to VS Code Copilot |
| `wiki.wiki_publisher` | ✓ | Prepare and push Azure Wiki draft branches |
| `wiki.wiki_scanner` | ✓ | Scan local Azure Wiki clone structure |
| `wiki.wiki_router` | — | Route pages to correct wiki section |
| `wiki.wiki_page_builder` | — | Build wiki page content from templates |
| `docs.export_docs` | ✓ | Build/export workspace documentation |
| `parsers.parse_apex` | — | Parse Apex class/trigger metadata |
| `parsers.parse_flow` | — | Parse Flow metadata |
| `parsers.parse_lwc` | — | Parse LWC component metadata |
| `parsers.parse_flexipage` | — | Parse FlexiPage/App Builder metadata |
| `parsers.parse_layout` | — | Parse Page Layout metadata |
| `parsers.parse_permissions` | — | Parse Permission Set metadata |
| `salesforce.cli` | — | Wrapper around `sf` CLI calls |
| `salesforce.soql` | — | SOQL query builder/executor |
| `security.redactor` | — | Mask PII and sensitive values in config records |
| `security.no_salesforce_ids` | — | Detect hardcoded Salesforce IDs |
| `search.simple_search` | — | Keyword search over JSONL indexes |

### Generated Index Files (`.ai/context/index/`)

All gitignored. Must be regenerated locally.

| File | Generated by | Contents |
|---|---|---|
| `metadata-components.jsonl` | `index_repo_metadata` | One card per Apex class, LWC, Flow, Permission Set, etc. |
| `schema-cards.jsonl` | `index_org_schema` | KimbleOne object + field definitions from org |
| `schema-index-summary.json` | `index_org_schema` | Summary of indexed objects |
| `config-record-cards.jsonl` | `index_config_records` | Masked config records from registry objects |
| `knowledge-cards.jsonl` | `index_knowledge` | Searchable index of all `.ai/knowledge/` notes |

---

## 8. Agents (`.github/agents/`)

Custom GitHub Copilot agents. Invoke in VS Code Chat with `@<agent-name>`.

| Agent file | Name | Purpose |
|---|---|---|
| `solution-architect.agent.md` | Salesforce Solution Architect | Create solution designs from Work Item context without writing code |
| `implementation-planner.agent.md` | Implementation Planner | Split approved designs into small work packets |
| `code-review.agent.md` | Code Reviewer | Review Apex, Flow, LWC against design + Salesforce best practices |
| `qa-how-to-test-writer.agent.md` | QA How-to-Test Writer | Generate and review QA test instructions |
| `tech-doc-writer.agent.md` | Technical Documentation Writer | Generate traceable technical docs from approved artifacts |
| `azure-wiki-documentation-agent.agent.md` | Azure Wiki Documentation Agent | Prepare wiki draft pages with placement review |
| `solution-design-reviewer.agent.md` | Solution Design Reviewer | Review designs for completeness, risk, testability |
| `release-readiness-reviewer.agent.md` | Release Readiness Reviewer | Review Work Item readiness for DevOps Center promote |
| `knowledge-curator.agent.md` | Knowledge Curator | Curate and review KB notes |
| `bug-investigator.agent.md` | Bug Investigator | Root-cause investigation using local context only |

---

## 9. Prompts / Slash Commands (`.github/prompts/`)

Use in VS Code with `/prompt-name` or attach in Copilot Chat.

| Prompt | Agent | Purpose |
|---|---|---|
| `/fetch-us` | — (MCP) | Fetch + normalize an ADO Work Item |
| `/build-context` | — | Build context pack for a Work Item |
| `/build-knowledge-context` | knowledge-curator | Select relevant KB notes for a topic |
| `/solution-design` | solution-architect | Generate solution design from Work Item |
| `/solution-design-review` | solution-design-reviewer | Review a solution design |
| `/design-to-work-packets` | implementation-planner | Split design into work packets |
| `/estimate-complexity` | — | Estimate size and risk of a Work Item |
| `/create-documentation` | tech-doc-writer | Generate technical docs |
| `/update-documentation-from-diff` | tech-doc-writer | Update docs based on current git diff |
| `/create-how-to-test` | qa-how-to-test-writer | Generate QA test instructions |
| `/review-how-to-test` | qa-how-to-test-writer | Review QA test instructions |
| `/review-implementation` | code-review | Review implementation against design |
| `/investigate-bug` | bug-investigator | Root-cause investigation |
| `/rollback-impact-analysis` | release-readiness-reviewer | Analyze rollback impact |
| `/pre-promote-report` | release-readiness-reviewer | Create pre-promote report |
| `/release-readiness-review` | release-readiness-reviewer | Full release readiness review |
| `/review-config-impact` | release-readiness-reviewer | Review config impact before promote |
| `/config-impact` | solution-design-reviewer | Review config impact evidence |
| `/config-delta-plan` | implementation-planner | Plan config delta sidecar |
| `/prepare-wiki-page` | wiki-agent | Prepare Azure Wiki draft |
| `/wiki-placement-review` | — | Review wiki page placement |
| `/review-wiki-publication` | — | Human review checklist before wiki push |
| `/sync-knowledge` | knowledge-curator | Sync KB notes from external repo |
| `/import-knowledge` | knowledge-curator | Import a raw knowledge source |
| `/review-knowledge-note` | knowledge-curator | Review a KB note |

---

## 10. Commands Reference

### Windows (PowerShell — `scripts/workspace.ps1`)

```powershell
# Setup
.\scripts\workspace.ps1 setup                                          # Bootstrap workspace
.\scripts\workspace.ps1 setup-venv                                     # Bootstrap + create venv
.\scripts\workspace.ps1 configure                                      # Interactive configuration
.\scripts\workspace.ps1 doctor                                         # Health check
.\scripts\workspace.ps1 doctor-strict                                  # Health check + Salesforce auth + KB
.\scripts\workspace.ps1 first-run                                      # setup + doctor + index-repo + knowledge-index

# Testing
.\scripts\workspace.ps1 test                                           # Run Python unit tests
.\scripts\workspace.ps1 smoke                                          # Full smoke test suite
.\scripts\workspace.ps1 ai-check-python                                # Verify all Python imports work

# Indexing (requires Salesforce CLI auth for schema/config)
.\scripts\workspace.ps1 ai-index-repo                                  # Index repo metadata
.\scripts\workspace.ps1 ai-index-schema -Org IntDev                   # Index Salesforce org schema
.\scripts\workspace.ps1 ai-index-config -Org IntDev                   # Index config records (masked)
.\scripts\workspace.ps1 ai-index-all -Org IntDev                      # All three indexes

# Context packs
.\scripts\workspace.ps1 ai-context -WorkItem KIM-1234 -Query "invoice approval"
.\scripts\workspace.ps1 ai-context-example                             # Example with EXAMPLE-WI

# Config analysis
.\scripts\workspace.ps1 config-impact -WorkItem KIM-1234
.\scripts\workspace.ps1 config-pack-skeleton -WorkItem KIM-1234

# Knowledge base
.\scripts\workspace.ps1 knowledge-sync -KbRepo "https://github.com/Vescik/Salesforce-knowledge-base.git"
.\scripts\workspace.ps1 knowledge-sync-dry-run -KbRepo "https://github.com/Vescik/Salesforce-knowledge-base.git"
.\scripts\workspace.ps1 knowledge-index
.\scripts\workspace.ps1 knowledge-create -KnowledgeSource ".ai/knowledge/imports/note.txt" -KnowledgeDomain billing -KnowledgeTitle "Invoice Rules"
.\scripts\workspace.ps1 knowledge-validate
.\scripts\workspace.ps1 knowledge-graph
.\scripts\workspace.ps1 knowledge-search -Query "invoice approval"
.\scripts\workspace.ps1 knowledge-push-dry-run -KbRepo "https://github.com/Vescik/Salesforce-knowledge-base.git"
.\scripts\workspace.ps1 knowledge-push -KbRepo "https://github.com/Vescik/Salesforce-knowledge-base.git"

# Work Item pre-promote checks
.\scripts\workspace.ps1 wi-precheck -WorkItem KIM-1234 -BaseRef HEAD~1
.\scripts\workspace.ps1 wi-precheck-strict -WorkItem KIM-1234 -BaseRef origin/main
.\scripts\workspace.ps1 wi-scope-check -WorkItem KIM-1234 -BaseRef HEAD~1

# Azure Wiki (AzureWikiRepo = Azure DevOps Wiki git URL)
.\scripts\workspace.ps1 wiki-dry-run -WorkItem KIM-1234 -WikiTitle "Invoice Approval" -WikiSource docs/architecture/KIM-1234.md -AzureWikiRepo "<url>"
.\scripts\workspace.ps1 wiki-prepare-branch -WorkItem KIM-1234 -WikiTitle "Invoice Approval" -WikiSource docs/architecture/KIM-1234.md -AzureWikiRepo "<url>"
.\scripts\workspace.ps1 wiki-push-approved -WorkItem KIM-1234 -WikiTitle "Invoice Approval" -WikiSource docs/architecture/KIM-1234.md -AzureWikiRepo "<url>" -WikiApprovalNote "Approved by Name/2026-06-13"
.\scripts\workspace.ps1 wiki-scan

# Docs
.\scripts\workspace.ps1 docs-build
.\scripts\workspace.ps1 docs-export-pdf
.\scripts\workspace.ps1 docs-pack

# MCP
.\scripts\workspace.ps1 mcp-salesforce-context                        # Start MCP server
.\scripts\workspace.ps1 mcp-smoke-test                                 # Test MCP tools/list

# Cleanup
.\scripts\workspace.ps1 ai-clean-context                               # Remove generated index/context files
.\scripts\workspace.ps1 clean-ai-generated                             # Remove all AI outputs
.\scripts\workspace.ps1 ai-list-outputs -WorkItem KIM-1234             # List generated files
```

### Mac / Linux (make)

Exact equivalent for every make target. Usage:

```powershell
.\scripts\workspace.ps1 help
.\scripts\workspace.ps1 setup
.\scripts\workspace.ps1 doctor
.\scripts\workspace.ps1 first-run
.\scripts\workspace.ps1 ai-index-repo
.\scripts\workspace.ps1 ai-index-schema -Org IntDev
.\scripts\workspace.ps1 ai-context -WorkItem KIM-1234 -Query "invoice approval"
.\scripts\workspace.ps1 knowledge-sync -KbRepo "https://github.com/Vescik/Salesforce-knowledge-base.git"
.\scripts\workspace.ps1 knowledge-search -Query "invoice approval"
.\scripts\workspace.ps1 wi-precheck -WorkItem KIM-1234 -BaseRef "HEAD~1"
.\scripts\workspace.ps1 wi-precheck-strict -WorkItem KIM-1234 -BaseRef "origin/main"
.\scripts\workspace.ps1 wiki-dry-run -WorkItem KIM-1234 -WikiTitle "Invoice Approval" -WikiSource "docs/architecture/KIM-1234.md" -AzureWikiRepo "<url>"
.\scripts\workspace.ps1 wiki-push-approved -WorkItem KIM-1234 -WikiTitle "Invoice Approval" -WikiSource "docs/architecture/KIM-1234.md" -AzureWikiRepo "<url>" -WikiApprovalNote "Approved by Name/2026-06-13"
```

---

## 11. Typical Workflows

### First-time setup
```bash
git clone https://github.com/Vescik/Salesforce-vsc-ai-workspace.git
cd salesforce-vsc-ai-workspace
cp .ai/config/workspace.local.json.example .ai/config/workspace.local.json
# Edit workspace.local.json: set default_dev_org_alias, knowledge_base.repo_url, azure_devops.organization
make first-run
```

### Start a new Work Item
```bash
# 1. Fetch Work Item from Azure DevOps (via VS Code Copilot)
#    /fetch-us KIM-1234

# 2. Build context pack
make ai-context WORK_ITEM=KIM-1234 QUERY="<feature keywords>"

# 3. Run config impact analysis
make config-impact WORK_ITEM=KIM-1234

# 4. Generate solution design (via Copilot)
#    /solution-design → saves to specs/proposed/KIM-1234.solution-design.md

# 5. Review design (via Copilot)
#    /solution-design-review

# 6. Split into work packets (via Copilot)
#    /design-to-work-packets
```

### Pre-promote checklist
```bash
# 1. Run precheck
make wi-precheck WORK_ITEM=KIM-1234 BASE_REF=origin/main

# 2. Generate pre-promote report (via Copilot)
#    /pre-promote-report

# 3. Review release readiness (via Copilot)
#    /release-readiness-review

# 4. Promote via DevOps Center (human action — not automated)
```

### Knowledge Base maintenance
```bash
# Sync latest notes from KB repo
make knowledge-sync KB_REPO=https://github.com/Vescik/Salesforce-knowledge-base.git

# Re-index after sync
make knowledge-index

# Search the KB
make knowledge-search QUERY="billing schedule T&M"

# Create new draft notes from a controlled source file
make knowledge-create KNOWLEDGE_SOURCE=.ai/knowledge/imports/new-notes.txt KNOWLEDGE_DOMAIN=billing KNOWLEDGE_TITLE="Credit Note Process"
make knowledge-validate
make knowledge-graph
# → Review generated draft in .ai/knowledge/domains/billing/
# → Update status from "draft" to "reviewed" after human review
```

### Azure Wiki documentation
```bash
# 1. Generate technical doc (via Copilot)
#    /create-documentation → saves to docs/architecture/KIM-1234.md

# 2. Dry-run wiki placement
make wiki-dry-run WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=https://dev.azure.com/ORG/PROJECT/_git/PROJECT.wiki

# 3. Review output in .ai/outputs/wiki/

# 4. Prepare draft branch
make wiki-prepare-branch WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<url>

# 5. Human reviews the branch in .ai/vendor/azure-wiki/

# 6. Push after explicit approval
make wiki-push-approved ... WIKI_APPROVAL_NOTE="Approved by John Smith 2026-06-13"

# 7. Create PR in Azure DevOps manually — merge is a human action
```

---

## 12. Environments & Promotion Gates

| Env | Type | Git | AI Actions Allowed |
|---|---|---|---|
| **IntDev** | Full Copy sandbox | No | schema_index, config_record_index, context_pack_build, precheck |
| **UAT** | Full Copy sandbox | Yes (DevOps Center) | read-only context |
| **Staging** | Full Copy sandbox | Yes (DevOps Center) | read-only context |
| **Production** | Production | Yes (DevOps Center) | read-only context |

Promotion gates (`.ai/deployment/gates.yaml`): all gates must be human-confirmed. AI workspace prepares evidence but does not approve or execute promotion.

---

## 13. Security Model

| Concern | Status |
|---|---|
| Runtime pip dependencies | **Zero** — stdlib only |
| External LLM APIs | **Blocked** by config + instructions |
| Salesforce writes | **Blocked** (`allow_salesforce_writes: false`) |
| Shell injection | **Not possible** — all subprocess calls use list args, no `shell=True` |
| Hardcoded credentials | **None found** |
| Path traversal (MCP) | **Mitigated** — `safe_path_join` + `Path.resolve()` + allowlist roots |
| YAML deserialization | **Safe** — custom scalar-only parser, no `yaml.load()` |
| GitHub Actions injection | **Partially open** — `${{ github.event.pull_request.title }}` inline in bash (known issue, fix: use `env:` block) |

Known open security findings (from audit 2026-06-13):
- **HIGH**: GitHub Actions bash script injection via PR title/branch name (`validate-work-item.yml`)
- **HIGH**: SOQL WHERE clause from config registry YAML not validated
- **MEDIUM**: GitHub Actions not pinned to commit SHAs (using `@v4` tags)

---

## 14. File Templates

All templates live in `.ai/templates/`. Used as starting points for generated artifacts.

| Template | Output file type |
|---|---|
| `solution-design.md` | `specs/proposed/<WI>.solution-design.md` |
| `technical-documentation.md` | `docs/architecture/<WI>.md` |
| `qa-how-to-test.md` | `docs/qa-how-to-test/<WI>.md` |
| `pre-promote-report.md` | `.ai/outputs/precheck/<WI>.precheck.md` |
| `config-impact.yaml` | `.ai/context/work-items/<WI>/config-impact.yaml` |
| `context-pack.md` | `.ai/context/work-items/<WI>/context-pack.md` |
| `work-item-summary.md` | `.ai/context/work-items/<WI>/work-item-summary.md` |
| `knowledge-note.md` | `.ai/knowledge/domains/<domain>/<title>.md` |
| `knowledge-domain.md` | `.ai/knowledge/domains/<domain>/domain.md` |
| `knowledge-import-manifest.yaml` | Batch knowledge import manifest |
| `work-packet.yaml` | Implementation work packet |
| `design-review.md` | Design review output |

---

## 15. What AI Should NOT Do

- Invent KimbleOne/Kantata object names, field names, or behaviors not in the schema index or KB
- Generate Salesforce deployment scripts or `sf` deploy commands
- Create or modify DevOps Center pipeline configuration
- Suggest OpenAI, Anthropic API, LangChain, or any external LLM integration
- Commit or reference `workspace.local.json`
- Use real employee names, Salesforce org IDs, or record IDs
- Approve or merge Azure Wiki PRs
- Use Azure DevOps MCP for anything other than reading Work Items
- Treat IntDev as a source of truth for metadata
- Act on KB notes with `status: draft` or `confidence: low` without flagging for human validation
- Claim deployment success without human-provided evidence
