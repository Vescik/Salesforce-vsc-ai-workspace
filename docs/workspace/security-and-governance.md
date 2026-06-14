# Security And Governance

## Purpose

This document defines the governance boundary for all workspace runbooks, prompts, commands, and generated artifacts. It is the safety reference used by the Runbook 2.0 operator docs.

## Runbook 2.0 Alignment

Every operator runbook must preserve these controls:

- State the source of truth for the workflow.
- Name the human approval gate for risky actions.
- Use Windows PowerShell commands first on this branch.
- Document expected local output paths for commands that write files.
- Prohibit external model APIs, Salesforce writes, Salesforce deployment, and configuration apply actions.
- Route failures involving secrets, raw data, unsupported package claims, or release authority to human escalation.

## Core Rules

- GitHub Copilot/Codex-style tooling is the approved AI assistance layer.
- External model APIs are not part of this workspace.
- No OpenAI, Anthropic, Gemini, LangChain, or LangGraph dependencies are implemented.
- DevOps Center remains the official Salesforce metadata promotion mechanism.
- IntDev is a Full Copy developer/discovery org and is not source of truth.
- The workspace must not deploy metadata automatically.
- The workspace must not apply configuration records.
- The workspace must not write Salesforce data.

## Source Boundaries

The workspace can reason from:

- Azure DevOps Work Item requirements.
- Repository metadata.
- Salesforce schema visible through approved read-only commands.
- Controlled anonymized config record cards.
- Curated Knowledge Base notes.
- Tests.
- Human-provided facts.

The workspace must not assume KimbleOne/Kantata managed package internals.

## Data Handling

Do not commit:

- `.env` or `.env.*`
- `.ai/config/workspace.local.json`
- `.ai/vendor/`
- `.sf/`
- `.sfdx/`
- `.venv/` or `venv/`
- raw production or Full Copy dumps
- uncontrolled exports
- logs with sensitive data
- secrets or credentials

Generated indexes are local context helpers and are ignored by default.

## Knowledge Base Governance

Knowledge Base content should be curated and reviewed. Approved notes require owner, status, confidence, last reviewed date, and source/evidence. Draft or stale notes must be labeled and validated before being used for implementation decisions.

Forbidden KB content:

- secrets
- production data dumps
- unsupported package claims
- environment-specific IDs as keys
- uncontrolled raw imports

## Azure Wiki Governance

Azure Wiki publication is draft-first. The workspace may prepare local previews and branches, but human review is required before pushing. PR creation, merge, and final publication remain outside the automated workspace.

## MCP Governance

Configured MCP servers:

- `salesforce-context`: local read-only context MCP.
- `ado-remote-mcp`: Azure DevOps Work Item MCP endpoint placeholder.

Rules:

- Use ADO MCP only for read-only Work Item retrieval.
- Do not use ADO write tools.
- Do not expose arbitrary filesystem roots.
- Do not add deploy, config apply, or Salesforce write tools.
- Do not store ADO tokens or secrets in repo config.

## Deterministic Enforcement

Local and CI checks include:

- `.\scripts\workspace.ps1 wi-precheck`
- `.\scripts\workspace.ps1 wi-precheck-strict`
- `.\scripts\workspace.ps1 test`
- `validate-no-salesforce-ids.yml`
- `validate-work-item.yml`
- optional validate-only `salesforce-validate.yml`

These checks reduce risk but do not replace human review.

## Human Approval Gates

| Feature | Human approval required | Reason |
| --- | --- | --- |
| Solution design | Yes | Architecture and package-boundary assumptions. |
| Config impact | Yes | Config behavior can drive managed package behavior. |
| Config pack skeleton | Yes | Not an apply tool; sidecar decision required. |
| QA how-to-test | Yes | Test data and expected behavior must be verified. |
| Release readiness | Yes | Reports are advisory only. |
| Knowledge Base push | Yes | Prevents unreviewed or unsafe knowledge publication. |
| Azure Wiki publish | Yes | Prevents unreviewed documentation changes. |
| DevOps Center promotion | Yes | Official metadata promotion mechanism. |

## Risk Levels By Feature

| Feature | Risk | Notes |
| --- | --- | --- |
| Local docs and prompt generation | Low | Review for accuracy. |
| Repo metadata indexing | Low | Local files only. |
| Schema indexing | Medium | Requires org auth; read-only. |
| Config indexing | Medium | Uses allowed registry objects and masking. |
| Knowledge Base sync | Medium | Private repo access and content governance needed. |
| Azure Wiki branch push | Medium | Requires explicit approval and local enablement. |
| Salesforce validation-only CI | Medium | Requires secrets and validate-only command. |
| Salesforce deploy/write/config apply | Not implemented | Prohibited in this workspace. |

## Release Boundary

The workspace can produce evidence and readiness reports. It cannot approve, promote, deploy, or apply. Release decisions remain with the accountable human roles and DevOps Center process.
