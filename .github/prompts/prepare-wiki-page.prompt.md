---
description: Prepare an Azure DevOps Wiki publication draft for a Work Item.
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

```bash
make wiki-dry-run WORK_ITEM=<WORK_ITEM_ID> WIKI_TITLE="<title>" WIKI_SOURCE=<source-path> AZURE_WIKI_REPO=<wiki-repo> WIKI_MODULE=<module-key> WIKI_TARGET_PATH=<target-path>
```

3. Review the generated placement report and page preview.
4. Do not push, merge, create PRs, or publish to the default wiki branch.
5. Recommend `wiki-prepare-branch` only after the placement is reviewed.

## Output

- Placement recommendation.
- Source artifacts used.
- Existing wiki sections considered.
- Warnings or blockers.
- Next command, if human review approves the next step.
