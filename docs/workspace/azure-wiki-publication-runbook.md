# Azure Wiki Publication Runbook

> Platform note: this branch uses the Windows PowerShell command surface. Mac/Linux `make` equivalents are included only as compact cross-platform references.

## Purpose

Use this runbook to prepare reviewed workspace documentation for Azure DevOps Wiki publication. The workspace prepares local previews and draft branches only; humans remain responsible for review, PR creation, merge, and final publication.

## When To Use

Use this runbook when a Work Item has reviewed documentation that should become team-facing Azure DevOps Wiki content, such as architecture notes, process documentation, operator runbooks, QA guidance, or support documentation.

Do not use this runbook to publish unreviewed AI-generated content, overwrite existing wiki pages without review, push to the wiki default branch, merge wiki PRs, deploy Salesforce metadata, or apply configuration records.

## Inputs

| Input | Required | Notes |
| --- | --- | --- |
| Work Item ID | Yes | Used in reports, branch names, and page metadata. |
| Wiki title | Yes unless inferable | Use the human-readable page title. |
| Source document | Yes | Must be a reviewed local document under an approved docs root. |
| Azure Wiki Git repo URL | Yes | Configure once with `.\scripts\workspace.ps1 configure` or `AZURE_WIKI_REPO`; use `-AzureWikiRepo` only as an override. |
| Wiki branch | Optional | Defaults to configured branch or `main`. |
| Module or target path | Optional | Use when placement must be explicit. |
| Approval note | Push only | Required for approved branch push. |

## Preconditions

1. Run commands from the repository root.
2. Confirm local setup is healthy:

```powershell
.\scripts\workspace.ps1 doctor
```

3. Confirm the source document has human review or clear draft status.
4. Confirm the wiki repo is reachable:

```powershell
git ls-remote "<configured-wiki-repo-url>"
```

5. For push only, confirm `.ai/config/workspace.local.json` has local-only Azure Wiki push enablement:

```json
"azure_wiki": {
  "push_enabled": true
}
```

Do not commit local config.

## Operator Steps

### 1. Create Or Update Source Documentation

Generate or update the source document:

```text
/create-documentation KIM-1234
/update-documentation-from-diff KIM-1234
```

Expected output:

- `docs/architecture/KIM-1234.md` or another reviewed source document path.
- Clear source artifacts, Work Item mapping, and human review notes.

### 2. Run A Wiki Dry Run

```powershell
.\scripts\workspace.ps1 wiki-dry-run -WorkItem KIM-1234 -WikiTitle "Invoice Approval Routing" -WikiSource "docs/architecture/KIM-1234.md"
```

Mac/Linux equivalent:

```bash
make wiki-dry-run WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo-url>
```

If local config is not set, rerun `.\scripts\workspace.ps1 configure`, set `AZURE_WIKI_REPO`, or pass `-AzureWikiRepo "<wiki-repo-url>"` for a one-off override.

Expected output:

- `.ai/outputs/wiki/KIM-1234.wiki-publication-report.md`
- `.ai/outputs/wiki/KIM-1234.wiki-publication-report.json`
- `.ai/outputs/wiki/KIM-1234.wiki-placement.md`
- Page preview inside the publication report.

### 3. Review Placement

Use the placement report and the prompt review:

```text
/wiki-placement-review KIM-1234
```

Approve only when:

- Existing wiki structure was inspected.
- Module, object, process, or functionality placement is justified.
- `_Proposed` or `_Unclassified` is used when no safe section exists.
- Duplicate page risk is addressed.
- Existing pages are not overwritten without review.

If placement is wrong, rerun dry run with a module or explicit target path:

```powershell
.\scripts\workspace.ps1 wiki-dry-run -WorkItem KIM-1234 -WikiTitle "Invoice Approval Routing" -WikiSource "docs/architecture/KIM-1234.md" -WikiModule "invoicing_billing"
```

### 4. Prepare A Local Draft Branch

After content and placement review:

```powershell
.\scripts\workspace.ps1 wiki-prepare-branch -WorkItem KIM-1234 -WikiTitle "Invoice Approval Routing" -WikiSource "docs/architecture/KIM-1234.md"
```

Expected output:

- Local branch in `.ai/vendor/azure-wiki/`.
- Local commit in the wiki vendor clone.
- Updated publication report under `.ai/outputs/wiki/`.
- No remote push.

### 5. Run Publication Review

```text
/review-wiki-publication KIM-1234
```

The review should return one decision:

- `APPROVED_FOR_BRANCH_PUSH`
- `APPROVED_WITH_CHANGES`
- `BLOCKED`

Proceed to push only when the decision is approved and the approval note is explicit.

### 6. Push Approved Branch

```powershell
.\scripts\workspace.ps1 wiki-push-approved -WorkItem KIM-1234 -WikiTitle "Invoice Approval Routing" -WikiSource "docs/architecture/KIM-1234.md" -WikiApprovalNote "Approved by <reviewer/date>"
```

Expected output:

- Approved feature branch pushed to the Azure Wiki Git repository.
- Publication report states that manual PR/review/merge is still required.

The workspace must not push the default branch and must not merge the wiki PR.

### 7. Finish In Azure DevOps

Outside this workspace:

1. Create or review the Azure DevOps PR for the pushed wiki branch.
2. Confirm reviewers, content, placement, and source citations.
3. Merge manually according to team process.

## Expected Outputs

| Procedure | Primary outputs |
| --- | --- |
| Dry run | Wiki placement report, page preview, publication report under `.ai/outputs/wiki/` |
| Placement review | Human decision and placement notes |
| Prepare branch | Local wiki branch and commit under `.ai/vendor/azure-wiki/` |
| Push approved | Remote feature branch only |
| Manual Azure DevOps step | PR, review, merge, and final publication outside the workspace |

## Review Gates

| Gate | Required decision |
| --- | --- |
| Source document | Reviewed, traceable, no unsupported package claims. |
| Placement | Existing wiki structure inspected and target path justified. |
| Sensitive content | No secrets, credentials, raw dumps, logs, or uncontrolled customer data. |
| Branch preparation | Local draft branch only; no remote push. |
| Push | `WIKI_APPROVAL_NOTE` present and `azure_wiki.push_enabled=true` in local config. |
| Publication | Azure DevOps PR review and merge are manual. |

## Troubleshooting

| Symptom | Check | Safe fix | Escalate when |
| --- | --- | --- | --- |
| Dry run cannot clone | `git ls-remote "<wiki-repo-url>"` | Confirm repo URL, branch, Git credentials, and network access. | Access is denied for a valid repo and branch. |
| Placement is wrong | Read `.ai/outputs/wiki/<WORK_ITEM>.wiki-placement.md` | Provide `-WikiModule` or `-WikiTargetPath` and rerun dry run. | No existing wiki section clearly fits. |
| Prepare branch fails | Check `.ai/vendor/azure-wiki/` status | Resolve local Git state in the vendor clone or remove/reclone the ignored vendor cache. | Existing wiki branch has unrelated local work. |
| Push is blocked | Check approval note and local config | Add explicit `-WikiApprovalNote` and local `azure_wiki.push_enabled=true`. | Approval ownership is unclear. |
| Existing page would be overwritten | Review diff and source evidence | Route to `_Proposed` or require explicit page update approval. | The page owner cannot review the change. |

## Escalation

Escalate to the documentation owner, Work Item owner, or Azure Wiki owner when:

- Page placement affects an existing reviewed wiki area.
- Content depends on draft, low-confidence, or stale knowledge.
- Source artifacts conflict or do not support the proposed page.
- Sensitive data may be present.
- The requested action would push, merge, or overwrite without review.

Keep a working record: command run, report path, target path, review decision, approval note, branch name, and next manual Azure DevOps action.

## Safety Boundaries

- Draft-first only.
- No default-branch push.
- No auto-merge.
- No PR creation unless separately requested and approved.
- No overwrite without review and diff evidence.
- No external model APIs.
- No Salesforce deploy/write/apply actions.
- No committed wiki credentials or employee-specific repo URLs.

## Maintenance

- Re-run `wiki-dry-run` after source document changes.
- Re-run `wiki-scan` when the wiki structure changes:

```powershell
.\scripts\workspace.ps1 wiki-scan -AzureWikiVendorDir ".ai/vendor/azure-wiki"
```

- Update this runbook when wiki command names, output paths, approval gates, or local config keys change.
