# Workspace Documentation Pack

This folder documents the Copilot-only Salesforce AI Workspace in this repository.

The workspace assists with context gathering, solution design, documentation, QA how-to-test guidance, prechecks, Knowledge Base use, and Azure Wiki draft publication. It does not deploy Salesforce metadata, apply configuration records, write Salesforce data, or call external LLM APIs.

## Documents

- [Installation Guide](installation-guide.md): employee setup, local configuration, Salesforce CLI auth, Knowledge Base setup, VS Code tasks, and troubleshooting.
- [Non-Technical Workspace Overview](workspace-overview-nontechnical.md): business-friendly explanation of purpose, value, boundaries, and process mapping.
- [Technical Architecture](workspace-architecture-technical.md): repository architecture, data flow, indexes, MCP, GitHub Actions, security model, and extension points.
- [Agents, Prompts, Skills, and MCP Reference](agents-prompts-skills-mcp-reference.md): inventory of actual custom agents, prompt files, Python tools, MCP servers, and workflows.
- [Developer Process Runbook](developer-process-runbook.md): how the workspace maps to intake, design, build, testing, release readiness, and DevOps Center promotion.
- [Knowledge Base Runbook](knowledge-base-runbook.md): Runbook 2.0 operator procedure for KB sync, creation, validation, indexing, graph, search, review, and push.
- [Azure Wiki Publication Runbook](azure-wiki-publication-runbook.md): Runbook 2.0 draft-first Azure DevOps Wiki publication workflow.
- [Runbook 2.0 Quality Checklist](runbook-2.0-quality-checklist.md): shared runbook standard, review checklist, command style, and maintenance rules.
- [Security and Governance](security-and-governance.md): guardrails, approval points, MCP boundaries, and data handling rules.
- [Troubleshooting](troubleshooting.md): common setup, auth, MCP, Knowledge Base, PDF, and CI issues.
- [Command Reference](appendix-command-reference.md): Windows command groups, auth requirements, writes, and notes.
- [HTML One-Page Runbook](html/index.html): offline visual runbook for onboarding and architecture review.
- [PDF Folder](pdf/README.md): generated PDFs when local tools are available, or manual export instructions.

## Regeneration Commands

```powershell
.\scripts\workspace.ps1 docs-build
.\scripts\workspace.ps1 docs-export-pdf
.\scripts\workspace.ps1 docs-pack
```

`docs-build` validates that the documentation pack exists. `docs-export-pdf` exports PDFs when a supported local tool is installed; otherwise it writes manual PDF export instructions.
