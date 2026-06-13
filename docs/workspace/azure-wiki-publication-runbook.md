# Azure Wiki Publication Runbook

## Purpose

Azure Wiki publication support helps teams prepare reviewed developer documentation pages from local workspace docs. It is draft-first and human-reviewed.

## What Azure Wiki Is Used For

Azure DevOps Wiki can hold reviewed team documentation, architecture notes, runbooks, and process documentation. This workspace prepares draft pages and local Git branches for review.

## Git-Based Wiki Flow

1. Clone or update the wiki Git repository into an ignored vendor folder.
2. Scan existing wiki sections.
3. Choose placement based on module map, object/functionality hints, or explicit target.
4. Generate a dry-run page preview.
5. Review content and placement.
6. Prepare a draft branch.
7. Push the approved branch only after explicit approval.
8. Create PR or manually merge outside the tool.

## Commands

Dry run:

```bash
make wiki-dry-run WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo>
```

Prepare draft branch:

```bash
make wiki-prepare-branch WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo>
```

Push approved branch:

```bash
make wiki-push-approved WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo> WIKI_APPROVAL_NOTE="Approved by <reviewer/date>"
```

Scan existing wiki clone:

```bash
make wiki-scan AZURE_WIKI_VENDOR_DIR=.ai/vendor/azure-wiki
```

## Placement Logic

The workspace can route pages to:

- object pages
- functionality pages
- module pages
- `_Proposed`
- `_Unclassified`

Explicit `WIKI_TARGET_PATH` wins when provided. Otherwise module map and page hints guide placement. If confidence is low, place in `_Proposed` or `_Unclassified` for human review.

## Approval Gates

- Source document must be reviewed.
- Placement must be reviewed.
- Sensitive data must be checked.
- `WIKI_APPROVAL_NOTE` is required for push.
- Local config must enable wiki push before push can occur.

## Safety Boundaries

- No direct default branch push.
- No auto merge.
- No overwrite without review.
- No publication without human approval.
- No external LLM APIs.
- No Salesforce deploy/write/apply actions.

## Example Scenario

1. A Work Item produces `docs/architecture/KIM-1234.md`.
2. The developer runs `make wiki-dry-run`.
3. The workspace scans the wiki and suggests `_Proposed/Invoice-Approval-Routing.md`.
4. The team reviews content and placement.
5. The developer runs `make wiki-prepare-branch`.
6. After approval, the developer runs `make wiki-push-approved`.
7. The team creates or reviews the Azure DevOps PR and merges manually.
