---
name: prepare-wiki-page
description: Prepare an Azure DevOps Wiki publication draft for a Work Item.
agent: azure-wiki-documentation-agent
mode: agent
---

# Prepare Azure Wiki Page

Use this prompt to prepare a draft Azure DevOps Wiki page from local Work Item documentation artifacts.

## Inputs

- Work Item ID.
- Source documentation path.
- Page title.
- Optional module key.
- Optional explicit target path.

## Behavior

1. Confirm the source artifact exists under an allowed documentation root.
2. Run a dry run first:

```powershell
.\scripts\workspace.ps1 wiki-dry-run -WorkItem <WORK_ITEM_ID> -WikiTitle "<title>" -WikiSource <source-path> -WikiModule <module-key> -WikiTargetPath <target-path>
```

3. If the wiki repository is not configured locally, use `-AzureWikiRepo "<wiki-repo>"` for this run or run `.\scripts\workspace.ps1 configure`.
4. Review the generated placement report and page preview.
5. Do not push, merge, create PRs, or publish to the default wiki branch.
6. Recommend `wiki-prepare-branch` only after the placement is reviewed.

## Output

- Placement recommendation.
- Source artifacts used.
- Existing wiki sections considered.
- Warnings or blockers.
- Next command, if human review approves the next step.
