# Salesforce VSC AI Workspace — User Guide

> **How to export to PDF:**
> ```bash
> pandoc docs/workspace/USER-GUIDE.md -o docs/workspace/pdf/USER-GUIDE.pdf --toc --toc-depth=2
> ```

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Prerequisites](#2-prerequisites)
3. [Installation & First-Time Setup](#3-installation--first-time-setup)
4. [Core Concepts](#4-core-concepts)
5. [Daily Developer Workflow](#5-daily-developer-workflow)
6. [Knowledge Base Guide](#6-knowledge-base-guide)
7. [Azure Wiki Publication](#7-azure-wiki-publication)
8. [Command Reference](#8-command-reference)
9. [Copilot Prompts Reference](#9-copilot-prompts-reference)
10. [Copilot Agents Reference](#10-copilot-agents-reference)
11. [MCP Tools Reference](#11-mcp-tools-reference)
12. [Windows Users Guide](#12-windows-users-guide)
13. [What This Workspace Does NOT Do](#13-what-this-workspace-does-not-do)
14. [Configuration Reference](#14-configuration-reference)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. Introduction

The **Salesforce VSC AI Workspace** is a local, deterministic AI assistance layer for Salesforce development teams working on top of the closed **KimbleOne/Kantata** managed package. It runs entirely on your machine — no external AI APIs, no cloud execution, no autonomous deployment.

### What It Helps You Do

- **Understand work before starting** — build a local context pack from Azure DevOps Work Items, repository metadata, Salesforce schema, config records, and internal knowledge notes
- **Design solutions safely** — generate implementation-neutral solution designs using Copilot agents that reason only from local evidence
- **Review and validate** — check implementation quality, config impact, and release readiness before DevOps Center promotion
- **Document consistently** — generate technical documentation, QA how-to-test instructions, and Azure Wiki drafts
- **Maintain internal knowledge** — sync, curate, and search a private knowledge base about the managed package

### The AI Layer

GitHub Copilot is the **only** approved AI execution layer. The workspace provides:

- **24+ prompt files** — slash commands that activate specialized workflows in Copilot Chat
- **11 custom agents** — persona-based agents for solution architecture, QA, documentation, and more
- **Local MCP server** — read-only context tool server that Copilot calls automatically
- **Python toolchain** — deterministic local scripts for indexing, searching, and report generation

> ⚠️ **All AI outputs are drafts.** Human review and approval are required before any design, deployment, or publication action.

---

## 2. Prerequisites

### Required

Install these tools before running setup:

1. **Python 3.11 or newer**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify: `python3 --version`

2. **Git**
   - Download from [git-scm.com](https://git-scm.com/)
   - Verify: `git --version`

3. **Salesforce CLI (`sf`)**
   - Install via: `npm install -g @salesforce/cli`
   - Verify: `sf --version`

4. **Visual Studio Code**
   - Download from [code.visualstudio.com](https://code.visualstudio.com/)

5. **GitHub Copilot**
   - Requires an active GitHub Copilot subscription
   - Install the VS Code extension: *GitHub Copilot* and *GitHub Copilot Chat*

6. **Azure DevOps access**
   - Read-only access to your organization's Work Items
   - Used by the `/fetch-us` prompt via MCP

### Optional

- **`make`** (Mac/Linux: pre-installed; Windows: install via Chocolatey or use the PowerShell wrapper)
- **Node.js / npm** (only if the Salesforce project itself requires it)
- **Pandoc** (for PDF export of documentation)
- **GitHub CLI (`gh`)** (for future repository publishing workflows)

### What You Do NOT Need

- No OpenAI API key
- No Anthropic API key
- No LangChain, LangGraph, or model orchestration tools
- No production Salesforce credentials in config files (authentication is handled by Salesforce CLI)

---

## 3. Installation & First-Time Setup

### Step 1 — Clone the Repository

```bash
git clone <your-workspace-repo-url>
cd <repo-folder>
```

### Step 2 — Run Setup

Creates the required directory structure and generates a local configuration file from the example template.

```bash
make setup
```

**Windows:**
```powershell
.\scripts\workspace.ps1 setup
```

**What it creates:**
- `.ai/config/workspace.local.json` (gitignored, your local settings)
- Required context directories under `.ai/context/`

### Step 3 — Configure Local Values

Runs an interactive prompt to set your org alias, Azure DevOps organization, and (optionally) Knowledge Base repository URL. Also automatically updates `.vscode/mcp.json` with your ADO organization.

```bash
make configure
```

**Windows:**
```powershell
.\scripts\workspace.ps1 configure
```

**You will be asked for:**
- Default Salesforce dev org alias (e.g., `IntDev`)
- Validation org alias (optional)
- Azure DevOps organization name
- Azure DevOps default project (optional)
- Knowledge Base repository URL (optional)
- Whether to enable Knowledge Base sync

> ℹ️ No passwords, tokens, or credentials are stored. Salesforce authentication is handled by Salesforce CLI separately.

### Step 4 — Authenticate Salesforce

```bash
sf org login web --alias IntDev
```

Replace `IntDev` with the alias you set in step 3.

### Step 5 — Verify Setup

```bash
make doctor
```

**Windows:**
```powershell
.\scripts\workspace.ps1 doctor
```

The doctor check reports:
- Python version and import health
- Required directories
- Salesforce CLI availability
- Knowledge Base configuration status
- Any warnings or errors

### Step 6 — Build the First Index

Scans your repository and creates a local metadata component index. No Salesforce org connection required.

```bash
make ai-index-repo
```

**Windows:**
```powershell
.\scripts\workspace.ps1 ai-index-repo
```

**What it creates:**
- `.ai/context/index/metadata-components.jsonl` — one card per Apex class, trigger, Flow, LWC, Permission Set, etc.

### Step 7 — (Optional) Index the Knowledge Base

If you have a Knowledge Base repository configured:

```bash
make knowledge-sync KB_REPO=https://github.com/your-org/knowledge-base.git
make knowledge-index
```

### Step 8 — Open in VS Code

```bash
code .
```

The MCP server for the Salesforce context starts automatically when VS Code detects the configuration in `.vscode/mcp.json`.

---

## 4. Core Concepts

### Work Items

A **Work Item** is a unit of work tracked in Azure DevOps (e.g., `KIM-1234`). Everything in the workspace traces back to a Work Item ID:

- Context packs: `.ai/context/work-items/KIM-1234/`
- Solution designs: `specs/proposed/KIM-1234.solution-design.md`
- Architecture docs: `docs/architecture/KIM-1234.md`
- QA docs: `docs/qa-how-to-test/KIM-1234.md`
- Precheck reports: `.ai/outputs/precheck/KIM-1234.precheck.md`

### DevOps Center

**Salesforce DevOps Center** is the official metadata promotion tool. The workspace prepares context, reports, and drafts — but **never** deploys metadata or triggers promotions. The pipeline runs:

```
IntDev (discovery) → UAT → Staging → Production
```

Branch names come from DevOps Center — never invent them in workspace artifacts.

### Knowledge Base

A separate private Git repository containing curated internal notes about the KimbleOne/Kantata managed package. The workspace syncs a local copy into `.ai/knowledge/` and indexes it into a searchable card file. Notes are organized by domain, object, process, decision, and governance category.

### MCP (Model Context Protocol)

Two MCP servers run alongside VS Code:

1. **`salesforce-context`** — local Python server exposing 12 read-only tools to Copilot (search indexes, read knowledge notes, build context packs)
2. **`ado-remote-mcp`** — HTTP connection to Azure DevOps for Work Item retrieval (read-only)

Copilot calls these tools automatically when answering questions that require local project context.

### Context Packs

A **context pack** is a curated Markdown file assembled from all local indexes for a specific Work Item and search query. It contains the most relevant metadata components, schema cards, config records, and knowledge notes — ready to be passed to Copilot for solution design.

---

## 5. Daily Developer Workflow

This section describes the full end-to-end process for a typical Work Item.

### Step 1 — Fetch the Work Item

In VS Code Copilot Chat, type:

```
/fetch-us KIM-1234
```

**What happens:**
1. The prompt calls the Azure DevOps MCP server to retrieve the Work Item
2. Normalizes the content into local artifact files
3. Writes:
   - `.ai/context/work-items/KIM-1234/work-item-summary.md`
   - `.ai/context/work-items/KIM-1234/acceptance-criteria.md`
   - `.ai/context/work-items/KIM-1234/ado-work-item.json`

> ℹ️ If the ADO MCP is unavailable, paste the Work Item content when Copilot prompts you — it will create the same local files from your input.

### Step 2 — Estimate Complexity (Optional)

```
/estimate-complexity KIM-1234
```

**Outputs:**
- Size estimate (XS / S / M / L / XL)
- Risk factors list
- Recommendation: `PROCEED` / `SPIKE` / `CLARIFY`

### Step 3 — Build Context

```bash
make ai-context WORK_ITEM=KIM-1234 QUERY="invoice approval billing"
```

**What it does:**
1. Searches all local indexes with your query
2. Selects the most relevant metadata, schema, config, and knowledge cards
3. Writes the context pack to `.ai/context/work-items/KIM-1234/context-pack.md`

Alternatively, use the MCP tool from Copilot Chat (no terminal required):

```
Build a context pack for KIM-1234 with query "invoice approval"
```

Copilot will call the `build_context_pack` MCP tool automatically.

### Step 4 — Generate Solution Design

For features and enhancements:

```
/solution-design KIM-1234
```

**What it produces:**
- Functional flow description
- Technical approach options
- Architecture decisions
- Risk and assumption register
- Mapping to acceptance criteria

> ⚠️ **Human approval required.** The design is a draft — review it against your knowledge of the package before development begins.

For bugs and incidents:

```
/investigate-bug KIM-1234
```

**What it produces:**
- Root-cause hypotheses ranked by confidence
- Evidence for each hypothesis
- Decision recommendation: `PROCEED` / `NEED_MORE_INFO` / `ESCALATE`

### Step 5 — Review the Design

```
/solution-design-review KIM-1234
```

**Checks performed:**
- Acceptance criteria coverage
- Flow vs. Apex decision justification
- UI and permission impact
- Config record impact identification
- KimbleOne/Kantata package assumption risks
- Testability of the proposed approach

> ⚠️ **Human approval required.** Review findings with the team before proceeding.

### Step 6 — Break Into Work Packets

```
/design-to-work-packets KIM-1234
```

**What it produces:**
- Small, scoped implementation packets
- Each packet maps to specific acceptance criteria
- Sequence and dependency notes

### Step 7 — Develop

Implement changes in VS Code. Copilot assists with code generation, and the local indexes provide context when you ask about existing metadata or schema.

### Step 8 — Run Local Precheck

```bash
make wi-precheck WORK_ITEM=KIM-1234 BASE_REF=HEAD~1
```

**What it checks:**
- Git diff scope alignment with Work Item
- Metadata in scope
- Basic validation rules

For strict mode (fails on high-severity findings):

```bash
make wi-precheck-strict WORK_ITEM=KIM-1234 BASE_REF=origin/main
```

### Step 9 — Review Implementation (Optional)

```
/review-implementation KIM-1234
```

**What it checks:**
- SOQL discipline (no unselective queries, no queries in loops)
- CRUD/FLS enforcement
- Sharing model compliance
- Hardcoded ID detection
- Design alignment
- Test coverage adequacy

### Step 10 — Analyze Config Impact

```bash
make config-impact WORK_ITEM=KIM-1234
```

**What it produces:**
- Config impact YAML: `.ai/context/work-items/KIM-1234/config-impact.yaml`
- Config pack skeleton: `config/kimbleone-packs/KIM-1234/`

> ℹ️ The config pack is a **review artifact only** — it does not apply config records.

### Step 11 — Write Documentation

```
/create-documentation KIM-1234
```

Produces a draft in `docs/architecture/KIM-1234.md`.

To update existing documentation based on what changed:

```
/update-documentation-from-diff KIM-1234
```

### Step 12 — Write QA How-to-Test

```
/create-how-to-test KIM-1234
```

Produces a draft in `docs/qa-how-to-test/KIM-1234.md` with:
- Acceptance criteria mapping
- Test data placeholders (no real IDs or org data)
- Environment setup steps
- Expected result descriptions
- Evidence placeholders for QA sign-off

Review the draft:

```
/review-qa-how-to-test KIM-1234
```

### Step 13 — Release Readiness

Generate a pre-promote report:

```
/pre-promote-report KIM-1234 UAT
```

Full release readiness review:

```
/release-readiness-review KIM-1234
```

For large or risky changes, analyze rollback impact:

```
/rollback-impact-analysis KIM-1234 UAT
```

> ⚠️ **Human approval required.** These reports are advisory — promotion decisions remain with the team and DevOps Center.

### Step 14 — Promote via DevOps Center

The workspace **does not** trigger promotions. After all reviews are complete, use Salesforce DevOps Center to promote the Work Item branch through the pipeline.

---

## 6. Knowledge Base Guide

The Knowledge Base is a curated collection of internal notes about the KimbleOne/Kantata managed package. It lives in a separate private Git repository and is synced locally for use by Copilot.

### Structure

```
.ai/knowledge/
├── index.yaml              ← Domain registry
├── domains/                ← Domain-level knowledge notes
│   ├── billing/
│   ├── resource-management/
│   ├── time-expense/
│   └── general/
├── object-notes/           ← Per-object notes (kmbi__Invoice__c, etc.)
├── process-maps/           ← End-to-end process documentation
├── decisions/              ← Architecture Decision Records (ADRs)
├── governance/             ← Data handling and access policies
└── imports/                ← Raw staging area (gitignored)
```

### Knowledge Note Format

Each note is a Markdown file with YAML front matter:

```yaml
---
title: "Invoice Approval Process"
domain: "billing"
owner: "Salesforce Platform Team"
status: "reviewed"          # draft | reviewed | approved
confidence: "high"          # low | medium | high
last_reviewed: "2026-06-01"
related_objects:
  - "kmbi__Invoice__c"
keywords:
  - "invoice"
  - "approval"
---
```

### Confidence and Status Rules

| Status | Confidence | How to use |
|---|---|---|
| `reviewed` | `high` | Use directly — cite the path |
| `reviewed` | `medium` | Use with a human validation note |
| `draft` | any | Include in context but require explicit confirmation |
| any | `low` | Surface to human — do NOT use as design basis |

> ⚠️ Notes older than 180 days have a `stale_review` risk flag — cite the date and treat as potentially outdated.

### Workflow: Sync from External Repository

1. **Preview what will be synced (no changes made):**

   ```bash
   make knowledge-sync-dry-run KB_REPO=https://github.com/your-org/knowledge-base.git
   ```

2. **Review the report** at `.ai/outputs/knowledge-sync/knowledge-sync.md`

3. **Sync (copies notes to `.ai/knowledge/`):**

   ```bash
   make knowledge-sync KB_REPO=https://github.com/your-org/knowledge-base.git
   ```

4. **Rebuild the search index:**

   ```bash
   make knowledge-index
   ```

   Or call the MCP tool from Copilot: *"Rebuild the knowledge index"*

### Workflow: Import a New Knowledge Note

1. Place your source file in `.ai/knowledge/imports/`

2. Run import:

   ```bash
   make knowledge-import \
     KNOWLEDGE_SOURCE=.ai/knowledge/imports/billing-rules.txt \
     KNOWLEDGE_DOMAIN=billing \
     KNOWLEDGE_TITLE="Billing Schedule Rules"
   ```

3. **Review the generated draft** in `.ai/knowledge/domains/billing/billing-schedule-rules.md`

4. Edit the note:
   - Set `status: reviewed`
   - Set `confidence: high | medium`
   - Fill in `related_objects`, `keywords`, `last_reviewed`
   - Remove the "Review Required" checklist section

5. Rebuild the index:

   ```bash
   make knowledge-index
   ```

### Workflow: Search the Knowledge Base

```bash
make knowledge-search QUERY="invoice approval"
```

Or in Copilot Chat — just ask a question. Copilot calls `get_related_knowledge` automatically.

### Workflow: Push New Notes to External Repository

1. **Preview what will be pushed:**

   ```bash
   make knowledge-push-dry-run KB_REPO=https://github.com/your-org/knowledge-base.git
   ```

2. **Commit and push to external repo:**

   ```bash
   make knowledge-push KB_REPO=https://github.com/your-org/knowledge-base.git
   ```

   This:
   - Compares local `.ai/knowledge/` notes against the vendor clone by checksum
   - Copies changed files into `.ai/vendor/knowledge-base/`
   - Creates a git commit with an auto-generated message
   - Pushes to the remote KB repository

> ⚠️ Review all notes before pushing. Notes with `possible_secret` risk flag are automatically skipped.

### Batch Import via Manifest

For importing multiple source files at once, create a manifest YAML and run:

```bash
make knowledge-import-manifest KNOWLEDGE_MANIFEST=.ai/templates/knowledge-import-manifest.yaml
```

---

## 7. Azure Wiki Publication

The Azure Wiki workflow publishes reviewed technical documentation to Azure DevOps Wiki. All steps are **draft-first with human approval**.

### Prerequisites

- A local clone of the Azure DevOps Wiki git repository
- `azure_wiki.push_enabled: true` set in your local config (for push step only)

### Full Publication Flow

**Step 1 — Generate documentation:**

```
/create-documentation KIM-1234
```

Creates `docs/architecture/KIM-1234.md`.

**Step 2 — Dry run (inspect wiki, choose placement, write preview):**

```bash
make wiki-dry-run \
  WORK_ITEM=KIM-1234 \
  WIKI_TITLE="Invoice Approval Routing" \
  WIKI_SOURCE=docs/architecture/KIM-1234.md \
  AZURE_WIKI_REPO=https://dev.azure.com/ORG/PROJECT/_git/PROJECT.wiki
```

**What it outputs:**
- Preview of the wiki page at `.ai/outputs/wiki/`
- Suggested placement path in the wiki structure
- Dry-run report

**Step 3 — Review placement:**

```
/wiki-placement-review KIM-1234
```

Checks whether the suggested placement section is appropriate.

**Step 4 — Prepare a draft branch (local commit, no remote push):**

```bash
make wiki-prepare-branch \
  WORK_ITEM=KIM-1234 \
  WIKI_TITLE="Invoice Approval Routing" \
  WIKI_SOURCE=docs/architecture/KIM-1234.md \
  AZURE_WIKI_REPO=https://dev.azure.com/ORG/PROJECT/_git/PROJECT.wiki
```

**Step 5 — Human review checklist:**

```
/review-wiki-publication KIM-1234
```

Checks:
- Source document has been reviewed
- Placement is correct
- No sensitive data is present
- Approval note is prepared

**Step 6 — Push approved branch (requires WIKI_APPROVAL_NOTE):**

```bash
make wiki-push-approved \
  WORK_ITEM=KIM-1234 \
  WIKI_TITLE="Invoice Approval Routing" \
  WIKI_SOURCE=docs/architecture/KIM-1234.md \
  AZURE_WIKI_REPO=https://dev.azure.com/ORG/PROJECT/_git/PROJECT.wiki \
  WIKI_APPROVAL_NOTE="Approved by Jane Smith 2026-06-13"
```

**Step 7 — Create and merge PR in Azure DevOps** (manual, outside this workspace).

### Safety Rules

- Never push directly to the wiki default branch
- Never auto-merge wiki PRs
- Never overwrite an existing wiki page without review and approval
- All AI-generated wiki drafts require human review before publication

---

## 8. Command Reference

### Setup & Health

| Command | Purpose |
|---|---|
| `make setup` | Bootstrap workspace, create config and directories |
| `make setup-venv` | Setup + create Python virtual environment |
| `make configure` | Create/update local config interactively |
| `make doctor` | Validate setup and prerequisites |
| `make doctor-strict` | Strict check including Salesforce auth and KB config |
| `make first-run` | Full setup sequence (setup + doctor + index + KB index) |
| `make test` | Run Python unit tests |
| `make smoke` | Run local smoke test (no org auth required) |
| `make ai-check-python` | Verify all Python module imports |

### Indexing

| Command | Auth Required | Output |
|---|---|---|
| `make ai-index-repo` | No | `metadata-components.jsonl` |
| `make ai-index-schema ORG=IntDev` | Yes (SF CLI) | SObject, field, relationship cards |
| `make ai-index-config ORG=IntDev` | Yes (SF CLI) | Config record cards (masked) |
| `make ai-index-all ORG=IntDev` | Yes (schema/config) | All indexes |

### Context Management

| Command | Purpose |
|---|---|
| `make ai-context WORK_ITEM=<ID> QUERY="<topic>"` | Build context pack from all indexes |
| `make ai-context-example` | Build example context for `EXAMPLE-WI` |
| `make ai-list-outputs WORK_ITEM=<ID>` | List all generated outputs for a Work Item |
| `make ai-clean-context` | Delete all generated index files |
| `make clean-ai-generated` | Delete all AI-generated outputs |

### Knowledge Base

| Command | Purpose |
|---|---|
| `make knowledge-sync-dry-run KB_REPO=<url>` | Preview sync (no changes) |
| `make knowledge-sync KB_REPO=<url>` | Sync external KB to `.ai/knowledge/` |
| `make knowledge-index` | Rebuild `knowledge-cards.jsonl` |
| `make knowledge-search QUERY="<topic>"` | Search knowledge index |
| `make knowledge-import KNOWLEDGE_SOURCE=<file> KNOWLEDGE_DOMAIN=<domain> KNOWLEDGE_TITLE="<title>"` | Import source file as KB note |
| `make knowledge-import-manifest KNOWLEDGE_MANIFEST=<yaml>` | Batch import from manifest |
| `make knowledge-push-dry-run KB_REPO=<url>` | Preview push (no changes) |
| `make knowledge-push KB_REPO=<url>` | Push curated notes to external KB repo |

### Work Item Validation

| Command | Purpose |
|---|---|
| `make wi-precheck WORK_ITEM=<ID> BASE_REF=HEAD~1` | Advisory pre-promote check |
| `make wi-precheck-strict WORK_ITEM=<ID> BASE_REF=origin/main` | Strict check (fails on high findings) |
| `make config-impact WORK_ITEM=<ID>` | Analyze config record impact |
| `make config-pack-skeleton WORK_ITEM=<ID>` | Build config review skeleton |

### Azure Wiki

| Command | Purpose |
|---|---|
| `make wiki-dry-run WORK_ITEM=<ID> WIKI_TITLE="<title>" WIKI_SOURCE=<path> AZURE_WIKI_REPO=<url>` | Preview wiki page |
| `make wiki-prepare-branch ...` | Prepare local draft branch |
| `make wiki-push-approved ... WIKI_APPROVAL_NOTE="<note>"` | Push approved branch |
| `make wiki-scan` | Scan local wiki vendor clone structure |

### Documentation

| Command | Purpose |
|---|---|
| `make docs-build` | Validate documentation package |
| `make docs-export-pdf` | Export workspace docs to PDF |
| `make docs-pack` | Build + export |
| `make docs-open-html` | Print path to offline HTML runbook |

### MCP Server

| Command | Purpose |
|---|---|
| `make mcp-salesforce-context` | Start Salesforce context MCP server |
| `make mcp-smoke-test` | Test MCP server (list tools via JSON-RPC) |

---

## 9. Copilot Prompts Reference

Use these slash commands in **VS Code Copilot Chat**. Open the chat panel and type `/` followed by the command name.

### Work Item & Context

| Command | Purpose | Outputs |
|---|---|---|
| `/fetch-us <WORK_ITEM_ID>` | Fetch and normalize Azure DevOps Work Item | `work-item-summary.md`, `acceptance-criteria.md`, `ado-work-item.json` |
| `/build-context <WORK_ITEM_ID> <QUERY>` | Assemble context pack | `context-pack.md`, `relevant-*.yaml` |
| `/build-knowledge-context <QUERY>` | Select relevant KB notes | KB note recommendations with risk flags |
| `/estimate-complexity <WORK_ITEM_ID>` | Estimate size and risk | Size (XS–XL), risk factors, recommendation |

### Solution Design

| Command | Purpose | Outputs |
|---|---|---|
| `/solution-design <WORK_ITEM_ID>` | Generate solution design | Draft design (functional flow, technical approach, risks) |
| `/solution-design-review <WORK_ITEM_ID>` | Review design for completeness | Review findings draft |
| `/design-to-work-packets <WORK_ITEM_ID>` | Split design into work packets | Implementation packet list |

### Bug Investigation

| Command | Purpose | Outputs |
|---|---|---|
| `/investigate-bug <WORK_ITEM_ID>` | Root-cause analysis | Hypotheses, evidence, decision |

### Implementation

| Command | Purpose | Outputs |
|---|---|---|
| `/review-implementation <WORK_ITEM_ID>` | Review Apex/Flow/LWC against design | Code review findings draft |
| `/review-config-impact <WORK_ITEM_ID>` | Review config impact findings | Config readiness assessment |
| `/config-delta-plan <WORK_ITEM_ID>` | Plan config delta sidecar | Config promotion plan (review only) |

### Documentation

| Command | Purpose | Outputs |
|---|---|---|
| `/create-documentation <WORK_ITEM_ID>` | Generate technical documentation | Draft at `docs/architecture/<ID>.md` |
| `/update-documentation-from-diff <WORK_ITEM_ID>` | Update docs based on git diff | Updated documentation draft |

### QA & Testing

| Command | Purpose | Outputs |
|---|---|---|
| `/create-how-to-test <WORK_ITEM_ID>` | Generate QA test instructions | Draft at `docs/qa-how-to-test/<ID>.md` |
| `/review-qa-how-to-test <WORK_ITEM_ID>` | Review QA doc completeness | QA review findings |

### Release & Promotion

| Command | Purpose | Outputs |
|---|---|---|
| `/pre-promote-report <WORK_ITEM_ID> <ENV>` | Draft pre-promote report | Report draft (does not promote) |
| `/release-readiness-review <WORK_ITEM_ID>` | Full readiness review | Readiness assessment draft |
| `/rollback-impact-analysis <WORK_ITEM_ID> <ENV>` | Analyze rollback impact | Rollback analysis draft |

### Azure Wiki

| Command | Purpose | Outputs |
|---|---|---|
| `/prepare-wiki-page <WORK_ITEM_ID>` | Prepare wiki draft | Draft + placement suggestion |
| `/wiki-placement-review <WORK_ITEM_ID>` | Review wiki placement | Placement validation |
| `/review-wiki-publication <WORK_ITEM_ID>` | Approval checklist for wiki push | Approval checklist |

### Knowledge Base

| Command | Purpose | Outputs |
|---|---|---|
| `/sync-knowledge <KB_REPO_URL>` | Sync external KB repo and rebuild index | Sync report |
| `/import-knowledge <SOURCE_FILE>` | Guide knowledge note import | Import instructions + draft note |
| `/review-knowledge-note <FILE>` | Review KB note quality | Review decision (APPROVED / BLOCKED) |

---

## 10. Copilot Agents Reference

Custom agents are activated automatically when you use the corresponding prompts. You can also invoke them directly in Copilot Chat using `@<agent-name>`.

| Agent | Activated by | Purpose |
|---|---|---|
| **Salesforce Solution Architect** | `/solution-design` | Generates implementation-neutral solution designs based on Work Item context, metadata, and schema evidence |
| **Solution Design Reviewer** | `/solution-design-review` | Reviews designs for AC coverage, risk, testability, and package assumption safety |
| **Implementation Planner** | `/design-to-work-packets` | Breaks approved designs into small, sequenced implementation work packets |
| **Code Reviewer** | `/review-implementation` | Reviews Apex, Flow, LWC, and metadata against approved design and Salesforce best practices |
| **Technical Doc Writer** | `/create-documentation`, `/update-documentation-from-diff` | Generates traceable technical documentation from approved artifacts |
| **QA How-to-Test Writer** | `/create-how-to-test`, `/review-qa-how-to-test` | Generates and reviews QA test instructions mapped to acceptance criteria |
| **Bug Investigator** | `/investigate-bug` | Performs structured root-cause investigation using local context only |
| **Release Readiness Reviewer** | `/pre-promote-report`, `/release-readiness-review`, `/rollback-impact-analysis` | Reviews Work Item readiness for DevOps Center promotion |
| **Knowledge Curator** | `/sync-knowledge`, `/import-knowledge`, `/review-knowledge-note`, `/build-knowledge-context` | Curates and reviews KB notes; checks confidence, risk flags, and sourcing |
| **Azure Wiki Documentation Agent** | `/prepare-wiki-page`, `/review-wiki-publication` | Prepares wiki draft pages with placement review and human approval gates |

### Agent Rules (All Agents)

All agents follow these rules:

- Do **not** invent KimbleOne/Kantata package behavior not found in local evidence
- Do **not** call external LLM APIs, Salesforce, ADO mutations, or deployment tools
- Do **not** auto-approve designs, code, releases, or wiki publications
- Cite source file paths for every knowledge or schema claim
- Mark all outputs as drafts requiring human review
- Escalate conflicts between knowledge notes and schema/config evidence to the human

---

## 11. MCP Tools Reference

The local `salesforce-context` MCP server exposes these tools to Copilot. Copilot calls them automatically — you do not need to invoke them manually.

| Tool | Purpose | Key Arguments |
|---|---|---|
| `search_context` | Search all local indexes simultaneously | `query`, `top_k` |
| `get_work_item_context` | Read all context artifacts for a Work Item | `work_item_id` |
| `get_object_card` | Get schema for a specific Salesforce object with its fields and relationships | `object_api_name` |
| `get_related_metadata` | Search metadata component index | `query`, `top_k` |
| `get_related_config_records` | Search masked config record cards | `query`, `top_k` |
| `get_related_knowledge` | Search knowledge card index | `query`, `top_k` |
| `get_knowledge_note` | Read full content of a specific knowledge note | `path` |
| `get_solution_design` | Read approved or proposed solution design | `work_item_id` |
| `get_config_impact` | Read config impact artifacts | `work_item_id` |
| `list_knowledge_domain` | List all notes in a specific knowledge domain | `domain`, `limit` |
| `rebuild_knowledge_index` | Rebuild `knowledge-cards.jsonl` from `.ai/knowledge/` | _(none)_ |
| `build_context_pack` | Build and write a context pack for a Work Item | `work_item_id`, `query` |

### All MCP Tools Are Read-Safe

- No tool writes to Salesforce
- No tool deploys metadata
- No tool modifies ADO Work Items
- Path access is limited to approved roots: `.ai/context/`, `.ai/knowledge/`, `specs/`, `docs/`

### Starting the MCP Server Manually

```bash
make mcp-salesforce-context
```

### Testing the MCP Server

```bash
make mcp-smoke-test
```

---

## 12. Windows Users Guide

All workspace functionality is available on Windows through the PowerShell wrapper.

### PowerShell Wrapper

```powershell
.\scripts\workspace.ps1 <target> [parameters]
```

**Common commands:**

```powershell
# Setup
.\scripts\workspace.ps1 setup
.\scripts\workspace.ps1 configure
.\scripts\workspace.ps1 doctor
.\scripts\workspace.ps1 first-run

# Indexing
.\scripts\workspace.ps1 ai-index-repo
.\scripts\workspace.ps1 ai-index-schema -Org IntDev
.\scripts\workspace.ps1 ai-index-all -Org IntDev

# Context
.\scripts\workspace.ps1 ai-context -WorkItem KIM-1234 -Query "invoice approval"

# Knowledge Base
.\scripts\workspace.ps1 knowledge-sync -KbRepo "https://github.com/your-org/kb.git"
.\scripts\workspace.ps1 knowledge-sync-dry-run -KbRepo "https://github.com/your-org/kb.git"
.\scripts\workspace.ps1 knowledge-index
.\scripts\workspace.ps1 knowledge-search -Query "invoice approval"
.\scripts\workspace.ps1 knowledge-push -KbRepo "https://github.com/your-org/kb.git"

# Validation
.\scripts\workspace.ps1 wi-precheck -WorkItem KIM-1234 -BaseRef "HEAD~1"
.\scripts\workspace.ps1 wi-precheck-strict -WorkItem KIM-1234 -BaseRef "origin/main"

# Wiki
.\scripts\workspace.ps1 wiki-dry-run `
  -WorkItem KIM-1234 `
  -WikiTitle "Invoice Approval Routing" `
  -WikiSource "docs/architecture/KIM-1234.md" `
  -AzureWikiRepo "https://dev.azure.com/ORG/PROJECT/_git/PROJECT.wiki"

.\scripts\workspace.ps1 wiki-push-approved `
  -WorkItem KIM-1234 `
  -WikiTitle "Invoice Approval Routing" `
  -WikiSource "docs/architecture/KIM-1234.md" `
  -AzureWikiRepo "https://dev.azure.com/ORG/PROJECT/_git/PROJECT.wiki" `
  -WikiApprovalNote "Approved by Jane Smith 2026-06-13"

# Testing
.\scripts\workspace.ps1 test
.\scripts\workspace.ps1 smoke

# Help
.\scripts\workspace.ps1 help
```

### Make Equivalents on Windows

| Unix/Make | PowerShell |
|---|---|
| `make setup` | `.\scripts\workspace.ps1 setup` |
| `make configure` | `.\scripts\workspace.ps1 configure` |
| `make doctor` | `.\scripts\workspace.ps1 doctor` |
| `make ai-index-schema ORG=IntDev` | `.\scripts\workspace.ps1 ai-index-schema -Org IntDev` |
| `make ai-context WORK_ITEM=KIM-1234 QUERY="topic"` | `.\scripts\workspace.ps1 ai-context -WorkItem KIM-1234 -Query "topic"` |
| `make knowledge-sync KB_REPO=<url>` | `.\scripts\workspace.ps1 knowledge-sync -KbRepo "<url>"` |
| `make wi-precheck WORK_ITEM=KIM-1234 BASE_REF=HEAD~1` | `.\scripts\workspace.ps1 wi-precheck -WorkItem KIM-1234 -BaseRef "HEAD~1"` |

### VS Code Tasks (Platform-Neutral)

Both Windows and Mac/Linux can use VS Code tasks:

1. Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac)
2. Type `Tasks: Run Task`
3. Select from the list

Available tasks include: Setup, Configure, Doctor, Index Repo, Build Context Pack, Sync Knowledge, Index Knowledge, Run Tests, Build Docs, Export PDFs.

### Python Requirements on Windows

- Use Python 3.11+ from [python.org](https://www.python.org/)
- `make` is not installed by default — use the PowerShell wrapper instead
- `PYTHONPATH` is set automatically by the wrapper

---

## 13. What This Workspace Does NOT Do

### Deployment & Salesforce Writes

- Does **not** deploy metadata (Salesforce DevOps Center is the official mechanism)
- Does **not** apply configuration records (no `apply` tool exists in this workspace)
- Does **not** write data to any Salesforce org
- Does **not** run automated migrations or data loads
- Does **not** trigger DevOps Center promotions

### External AI & APIs

- Does **not** call the OpenAI API
- Does **not** call the Anthropic API
- Does **not** use LangChain, LangGraph, or model orchestration
- Does **not** use any model provider switching
- Does **not** store or forward your Salesforce data to external services

### Autonomous Decision-Making

- Does **not** auto-approve solution designs
- Does **not** auto-approve code reviews
- Does **not** auto-approve QA sign-off
- Does **not** auto-approve wiki publications
- Does **not** approve or execute DevOps Center promotions

All AI outputs are **drafts** that require human review and approval.

### Managed Package Access

- Does **not** access KimbleOne/Kantata package source code
- Does **not** assume or invent package behavior beyond documented facts
- Reasons only from: local metadata, Salesforce org schema, anonymized config records, local KB notes, and human-provided evidence

### Source of Truth

- **IntDev** is a shared Full Copy discovery sandbox — not the source of truth for metadata
- **This workspace** assists and documents — not an authoritative deployment gate
- **KB notes with `status: draft` or `confidence: low`** require human validation before acting on them

---

## 14. Configuration Reference

### Local Configuration File

**Location:** `.ai/config/workspace.local.json` (gitignored — never commit this file)

**Create or update:**
```bash
make configure
```

**Full schema with defaults:**

```json
{
  "version": 1,
  "workspace": {
    "name": "salesforce-ai-workspace"
  },
  "salesforce": {
    "default_dev_org_alias": "IntDev",
    "validation_org_alias": "",
    "login_url": "https://login.salesforce.com",
    "use_devops_center": true
  },
  "knowledge_base": {
    "enabled": false,
    "repo_url": "",
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
    "branch": "main",
    "push_enabled": false,
    "require_human_approval": true
  },
  "python": {
    "min_version": "3.11",
    "use_venv": true,
    "venv_path": ".venv"
  },
  "security": {
    "allow_salesforce_writes": false,
    "allow_config_apply": false,
    "allow_external_llm_apis": false
  }
}
```

### Key Settings

| Setting | Purpose | Default |
|---|---|---|
| `salesforce.default_dev_org_alias` | Org alias for schema/config indexing | `IntDev` |
| `knowledge_base.enabled` | Enable KB sync commands | `false` |
| `knowledge_base.repo_url` | External KB git URL | _(empty)_ |
| `azure_devops.organization` | ADO org name (auto-set by `make configure`) | `YOUR_ADO_ORG` |
| `azure_wiki.push_enabled` | Allow `wiki-push-approved` to push | `false` |
| `security.allow_salesforce_writes` | Must remain `false` | `false` |
| `security.allow_external_llm_apis` | Must remain `false` | `false` |

### MCP Server Configuration

**File:** `.vscode/mcp.json` (automatically updated by `make configure`)

```json
{
  "servers": {
    "ado-remote-mcp": {
      "type": "http",
      "url": "https://mcp.dev.azure.com/YOUR_ADO_ORG"
    },
    "salesforce-context": {
      "type": "stdio",
      "command": "python3",
      "args": [
        "-m", "ai_workspace.mcp.salesforce_context_mcp",
        "--index-dir", ".ai/context/index",
        "--context-root", ".ai/context"
      ],
      "env": {
        "PYTHONPATH": ".ai/skills/python"
      }
    }
  }
}
```

> ℹ️ The `YOUR_ADO_ORG` placeholder is replaced automatically when you run `make configure`.

---

## 15. Troubleshooting

### Setup Issues

Run the doctor to diagnose:

```bash
make doctor
```

If directories are missing:

```bash
make setup
```

### Python Version Error

```
ERROR: Python 3.11+ required
```

1. Check your Python version: `python3 --version`
2. Install Python 3.11+ from [python.org](https://www.python.org/)
3. On Mac with Homebrew: `brew install python@3.11`

### Import Errors

If Python imports fail, ensure `PYTHONPATH` is set:

```bash
PYTHONPATH=.ai/skills/python python3 -c "import ai_workspace; print('OK')"
```

Always run commands through `make` or `.\scripts\workspace.ps1` — they set `PYTHONPATH` automatically.

### Make Not Found (Windows)

Use the PowerShell wrapper instead:

```powershell
.\scripts\workspace.ps1 <target>
```

### Salesforce CLI Auth Error

```
ERROR: No active Salesforce org authenticated
```

Run:

```bash
sf org login web --alias IntDev
sf org list
```

Schema and config indexing (`make ai-index-schema`, `make ai-index-config`) require authenticated org access.

### MCP Server Not Starting

1. Check `.vscode/mcp.json` has the correct ADO org (run `make configure` to update)
2. Verify Python 3.11+ is available as `python3` on your PATH
3. Test manually:

   ```bash
   PYTHONPATH=.ai/skills/python python3 -m ai_workspace.mcp.salesforce_context_mcp --index-dir .ai/context/index --context-root .ai/context
   ```

4. Check VS Code output panel: `View > Output > GitHub Copilot MCP`

### Knowledge Sync Fails

1. Verify git access to the KB repository
2. Test with dry-run first: `make knowledge-sync-dry-run KB_REPO=<url>`
3. Check `.ai/outputs/knowledge-sync/knowledge-sync.md` for error details
4. Ensure `PYTHONPATH=.ai/skills/python` is set if running Python directly

### Context Pack Empty

If `make ai-context` returns no results:

1. Verify indexes exist: `ls .ai/context/index/`
2. Rebuild: `make ai-index-repo`
3. Try a broader query: `make ai-context WORK_ITEM=<ID> QUERY="salesforce"`

### Azure DevOps MCP Not Available

If `/fetch-us` says the MCP is unavailable:

1. Check `azure_devops.organization` in your local config: `cat .ai/config/workspace.local.json`
2. Verify the URL in `.vscode/mcp.json`
3. As a fallback: paste the Work Item content when prompted by `/fetch-us` — it creates the same local artifacts

### Getting Help

- Run `make help` to list all available commands
- Open the offline HTML runbook: `make docs-open-html`
- Check `docs/workspace/troubleshooting.md` for more detail
