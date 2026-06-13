# Azure Wiki Draft Publication

This folder contains policy, routing hints, and templates for preparing Azure DevOps Wiki documentation drafts.

The workflow is draft-first:

1. Configure the wiki repository URL locally through `.ai/config/workspace.local.json`, `AZURE_WIKI_REPO`, or a Makefile argument.
2. Run a dry run to inspect the wiki structure and generate a local preview.
3. Review the placement report and page preview.
4. Prepare a local draft branch only after the placement looks correct.
5. Push the feature branch only after explicit human approval.
6. Create and merge the PR manually in Azure DevOps outside this tool.

No command in this phase deploys Salesforce metadata, applies configuration records, writes Salesforce data, auto-merges wiki changes, or pushes directly to the wiki default branch.

## Commands

```bash
make wiki-dry-run WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-git-url-or-local-path>
make wiki-prepare-branch WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-git-url-or-local-path>
make wiki-push-approved WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-git-url-or-local-path> WIKI_APPROVAL_NOTE="Approved by <reviewer/date>"
```

`wiki-push-approved` pushes only a feature branch and requires local `azure_wiki.push_enabled=true` plus an approval note. It never merges and never pushes to `main`, `master`, or the detected default branch.

## Reports

Reports are written under `.ai/outputs/wiki/`:

- `<WORK_ITEM_ID>.wiki-placement.md`
- `<WORK_ITEM_ID>.wiki-publication-report.md`
- `<WORK_ITEM_ID>.wiki-publication-report.json`
- `preview/<target-path>.md` for dry runs

Markdown reports may be reviewed or committed according to team policy. JSON and log outputs are ignored.
