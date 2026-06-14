# Workspace Configuration

This folder contains the local configuration surface for the Copilot-only Salesforce AI Workspace.

## Files

- `workspace.example.json`: committed safe defaults and placeholders.
- `workspace.local.json.example`: committed template for employee-local configuration.
- `workspace.local.json`: generated local configuration. This file is ignored by Git.

## Rules

- Do not commit `workspace.local.json`.
- Do not store passwords, Salesforce tokens, private keys, or secrets in workspace config.
- Salesforce authentication is managed by Salesforce CLI, not by this repository.
- Azure DevOps authentication is managed by VS Code and the remote Azure DevOps MCP server, not by repository config.
- Employee org aliases can differ locally. Configure them in `workspace.local.json` or with environment variables.
- Azure DevOps organization and default project can differ locally. Configure them through `.\scripts\workspace.ps1 configure`, `workspace.local.json`, or `ADO_ORG`/`ADO_PROJECT`.
- Azure Wiki repository URL, branch, and vendor directory can differ locally. Configure them through `.\scripts\workspace.ps1 configure`, `workspace.local.json`, environment variables, or command arguments.
- The Knowledge Base repo URL is optional and should be configured locally through `.\scripts\workspace.ps1 configure`, in `workspace.local.json`, or through `KB_REPO`.

## Azure DevOps MCP

Committed examples use the placeholder organization `YOUR_ADO_ORG` and server name `ado-remote-mcp`. `.\scripts\workspace.ps1 configure` updates the local VS Code MCP URL from the configured Azure DevOps organization before `/fetch-us <WORK_ITEM_ID>` is used.

Do not store ADO PATs, OAuth tokens, passwords, or employee credentials in `.ai/config/*.json`.

## Azure Wiki

Azure DevOps Wiki draft publication uses a Git repository URL from local config, `AZURE_WIKI_REPO`, or a command argument. The local clone cache defaults to `.ai/vendor/azure-wiki/` and is ignored by Git.

`azure_wiki.push_enabled` defaults to `false`. Keep it false for dry-run and local branch preparation. Set it to `true` only in ignored local config when the team has approved pushing reviewed feature branches.

Supported environment overrides:

- `AZURE_WIKI_REPO`
- `AZURE_WIKI_BRANCH`
- `AZURE_WIKI_VENDOR_DIR`

Do not store Azure DevOps Wiki PATs, OAuth tokens, passwords, or employee credentials in `.ai/config/*.json`.

## Setup

Create local config from the template:

```powershell
.\scripts\workspace.ps1 setup
```

Edit local config interactively:

```powershell
.\scripts\workspace.ps1 configure
```

Run health checks:

```powershell
.\scripts\workspace.ps1 doctor
```
