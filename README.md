# Salesforce VSC AI Workspace

> Local, deterministic AI assistance for Salesforce teams working on KimbleOne/Kantata — powered by GitHub Copilot, with no external LLM APIs.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-lightgrey)
![AI](https://img.shields.io/badge/AI-GitHub%20Copilot%20only-green)
![Salesforce](https://img.shields.io/badge/Salesforce-DevOps%20Center-blue)

---

## What It Does

- **Build local context packs** from Azure DevOps Work Items, repository metadata, Salesforce org schema, config records, and a curated internal Knowledge Base
- **Generate solution designs, QA docs, and technical documentation** using specialized Copilot agents
- **Review and validate** — implementation code, config impact, and release readiness before DevOps Center promotion
- **Maintain internal knowledge** — sync, curate, index, search, and push a private KB about the managed package
- **Publish Azure Wiki drafts** — draft-first, human-approved documentation pipeline

## What It Does NOT Do

- Does **not** deploy metadata or trigger Salesforce promotions
- Does **not** apply configuration records
- Does **not** call external LLM APIs (OpenAI, Anthropic, LangChain, etc.)
- Does **not** auto-approve any design, release, or publication decision

---

## Quick Start

**1. Install prerequisites:** Python 3.11+, Git, Salesforce CLI (`sf`), VS Code + GitHub Copilot

**2. Clone, install, and set up:**

```bash
git clone <repo-url> && cd <repo-folder>
pip install -e .
make setup
make configure
```

> `pip install -e .` is run automatically by `setup` — needed only if skipping setup.  
> `configure` is interactive: sets your Salesforce org alias, Azure DevOps organization, and Knowledge Base URL.

**3. Authenticate Salesforce:**
```bash
sf org login web --alias IntDev
```

**4. Verify and index:**
```bash
make doctor
make ai-index-repo
```

**5. Open VS Code and start:**
```bash
code .
```
Open Copilot Chat and type `/fetch-us YOUR-WORK-ITEM-ID` to begin.

> **VS Code Tasks**: `Ctrl+Shift+P` → `Tasks: Run Task` — all commands available as clickable tasks.

---

## Features

| Feature | Command |
|---|---|
| Context indexing | `make ai-index-repo` |
| Index all (schema + config) | `make ai-index-all ORG=IntDev` |
| Build context pack | `make ai-context WORK_ITEM=<ID> QUERY="<topic>"` |
| Build context from AC keywords | `make ai-context-auto WORK_ITEM=<ID>` |
| Knowledge Base sync | `make knowledge-sync KB_REPO=<url>` |
| Knowledge Base validation | `make knowledge-validate` |
| Knowledge graph | `make knowledge-graph` |
| Knowledge Base push | `make knowledge-push KB_REPO=<url>` |
| KB search | `make knowledge-search QUERY="<topic>"` |
| AC coverage check | `make ac-coverage WORK_ITEM=<ID>` |
| Solution design lint | `make design-lint WORK_ITEM=<ID>` |
| Pre-promote check | `make wi-precheck WORK_ITEM=<ID>` |
| Config impact | `make config-impact WORK_ITEM=<ID>` |
| Wiki draft | `make wiki-dry-run WORK_ITEM=<ID> ...` |
| MCP server | `make mcp-salesforce-context` |
| Run tests | `make test` |

---

## Copilot Prompts

Type these slash commands in VS Code Copilot Chat:

| Command | Purpose |
|---|---|
| `/fetch-us <ID>` | Fetch and normalize Azure DevOps Work Item |
| `/estimate-complexity <ID>` | Estimate size and risk (XS–XL) |
| `/solution-design <ID>` | Generate implementation-neutral solution design |
| `/solution-design-review <ID>` | Review design completeness and risk |
| `/design-to-work-packets <ID>` | Break approved design into work packets |
| `/investigate-bug <ID>` | Root-cause analysis for defects |
| `/review-implementation <ID>` | Review Apex/Flow/LWC against design |
| `/config-impact <ID>` | Review config record impact |
| `/create-documentation <ID>` | Generate technical documentation draft |
| `/create-how-to-test <ID>` | Generate QA how-to-test instructions |
| `/pre-promote-report <ID> <ENV>` | Draft pre-promote report |
| `/release-readiness-review <ID>` | Full release readiness review |
| `/rollback-impact-analysis <ID> <ENV>` | Analyze rollback impact |
| `/prepare-wiki-page <ID>` | Prepare Azure Wiki draft |
| `/sync-knowledge <KB_URL>` | Sync external Knowledge Base |
| `/build-knowledge-context <QUERY>` | Select relevant KB notes |

Full prompt reference: [docs/workspace/USER-GUIDE.md — §9](docs/workspace/USER-GUIDE.md#9-copilot-prompts-reference)

---

## Documentation

| Document | Description |
|---|---|
| [USER-GUIDE.md](docs/workspace/USER-GUIDE.md) | **Complete user guide** — step-by-step instructions for every feature |
| [QUICKSTART.md](QUICKSTART.md) | Five-step quick start |
| [installation-guide.md](docs/workspace/installation-guide.md) | Detailed installation guide |
| [developer-process-runbook.md](docs/workspace/developer-process-runbook.md) | End-to-end developer workflow |
| [knowledge-base-runbook.md](docs/workspace/knowledge-base-runbook.md) | Knowledge Base management guide |
| [azure-wiki-publication-runbook.md](docs/workspace/azure-wiki-publication-runbook.md) | Azure Wiki publication workflow |
| [workspace-architecture-technical.md](docs/workspace/workspace-architecture-technical.md) | Technical architecture reference |
| [appendix-command-reference.md](docs/workspace/appendix-command-reference.md) | Complete command reference |
| [security-and-governance.md](docs/workspace/security-and-governance.md) | Security model and governance |
| [troubleshooting.md](docs/workspace/troubleshooting.md) | Common issues and fixes |
| [AI-CONTEXT.md](AI-CONTEXT.md) | Single-file AI orientation (attach to any AI chat) |

---

## Repository Structure

```
.github/
├── agents/          # 11 custom Copilot agents
├── prompts/         # 24+ slash-command prompt files
└── workflows/       # GitHub Actions validation (no deployment)

.ai/
├── config/          # workspace.local.json (gitignored), example template
├── context/         # Work Item artifacts + generated indexes (gitignored)
├── knowledge/       # Curated KB notes (synced from external repo)
├── skills/python/   # Python toolchain (zero runtime pip deps)
├── deployment/      # Runbooks and pipeline gate configuration
├── templates/       # Document templates
└── wiki/            # Wiki module map and publication policy

.vscode/
├── mcp.json         # MCP server configuration (auto-updated by configure)
├── tasks.json       # VS Code tasks — all commands
└── settings.json    # Workspace settings

scripts/
├── setup.py         # Python setup script
├── configure.py     # Python configure script
└── doctor.py        # Python doctor script

config/data-promotion/
├── config-object-registry.yaml  # Enabled config objects for indexing
└── masking-policy.yaml          # Field masking rules for config records

docs/workspace/      # Workspace documentation
force-app/           # Salesforce metadata (DX project)
specs/               # Solution designs (proposed + approved)
Makefile             # Command interface
setup.py             # Enables pip install -e .
```

---

## Requirements

| Requirement | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Local toolchain (zero external pip deps) |
| Git | Any | Repository and KB operations |
| Salesforce CLI (`sf`) | Latest | Schema and config indexing, org auth |
| VS Code | Latest | Editor + Copilot Chat integration |
| GitHub Copilot | Active subscription | AI layer (only approved AI) |
| Azure DevOps | Read access | Work Item retrieval via MCP |

---

## Security & Governance

- All AI outputs are **drafts** — no auto-approve, no auto-deploy
- No external LLM APIs — GitHub Copilot only
- No Salesforce writes — `allow_salesforce_writes: false` enforced in config
- No config record application — `allow_config_apply: false` enforced
- No secrets in repository — `.ai/config/workspace.local.json` is gitignored
- KB notes scanned for secret-like values before push
- Azure Wiki: push requires explicit `WIKI_APPROVAL_NOTE` and local `push_enabled: true`
- DevOps Center remains the only official metadata promotion mechanism

Full governance reference: [docs/workspace/security-and-governance.md](docs/workspace/security-and-governance.md)

---

## Knowledge Base Repositories

| Repository | Purpose | Visibility |
|---|---|---|
| `Vescik/Salesforce-vsc-ai-workspace` | This workspace | Public |
| `Vescik/Salesforce-knowledge-base` | Curated KimbleOne/Kantata notes | Private |
