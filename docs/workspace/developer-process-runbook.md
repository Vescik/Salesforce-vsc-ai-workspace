# Developer Process Runbook

This runbook maps the workspace to a normal Salesforce delivery flow. It assumes DevOps Center remains the official metadata promotion mechanism.

> **Platform note:** All commands shown Windows (PowerShell) first, followed by Mac / Linux. VS Code Tasks are also available: Ctrl+Shift+P → Tasks: Run Task

## 1. Intake / Work Item

Start from a DevOps Center Work Item branch and a real Azure DevOps Work Item or pasted requirement.

```text
/fetch-us KIM-1234
```

Expected local artifacts:

- `.ai/context/work-items/KIM-1234/ado-work-item.json`
- `.ai/context/work-items/KIM-1234/work-item-summary.md`
- `.ai/context/work-items/KIM-1234/acceptance-criteria.md`

If MCP is unavailable, paste the Work Item description and acceptance criteria.

## 1a. Complexity Estimation (Optional)

Before building context or starting design, estimate the Work Item size and risk to inform sprint planning:

```text
/estimate-complexity KIM-1234
```

This reads the Work Item summary and acceptance criteria and produces an advisory size rating (XS–XL), a risk factor table, and a recommended approach (`PROCEED_TO_DESIGN`, `SPIKE_FIRST`, or `NEEDS_CLARIFICATION`).

Run this before `/solution-design` when the Work Item scope is unclear, the team needs a rough estimate for sprint planning, or you want to surface unknowns that may block design.

All estimates are advisory and require human validation.

## 2. Build Context

Local metadata:

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 ai-index-repo
```
```bash
# Mac / Linux
make ai-index-repo
```

Optional org schema and config cards:

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 ai-index-schema -Org IntDev
.\scripts\workspace.ps1 ai-index-config -Org IntDev
```
```bash
# Mac / Linux
make ai-index-schema ORG=IntDev
make ai-index-config ORG=IntDev
```

Knowledge Base:

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 knowledge-index
```
```bash
# Mac / Linux
make knowledge-index
```

Context pack:

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 ai-context -WorkItem KIM-1234 -Query "invoice approval"
```
```bash
# Mac / Linux
make ai-context WORK_ITEM=KIM-1234 QUERY="invoice approval"
```

## 3. Solution Design or Bug Investigation

**For feature and enhancement Work Items**, use the context pack and Work Item artifacts:

```text
/solution-design KIM-1234
```

The design should map every implementation recommendation to acceptance criteria and label evidence as confirmed, inferred, unknown, or human-confirmed.

**For defect and incident Work Items**, run the bug investigation first:

```text
/investigate-bug KIM-1234
```

The investigation produces ranked root-cause hypotheses with evidence from workspace artifacts. Provide the error message, reproduction steps, and affected environment when prompted.

Review the investigation output and decide:

- `PROCEED_TO_DESIGN` — root cause is clear enough to start `/solution-design`.
- `NEED_MORE_EVIDENCE` — gather additional debug logs, SOQL results, or config record values first.
- `ESCALATE` — the root cause is outside workspace knowledge; escalate to the KimbleOne/Kantata team.

Once the root cause is confirmed, continue with `/solution-design KIM-1234` as normal.

## 4. Design Review

```text
/solution-design-review KIM-1234
```

Review focus:

- Acceptance criteria coverage.
- Flow vs Apex decision.
- UI impact.
- Permission impact.
- Config impact.
- Managed package uncertainty.
- Testability and DevOps Center readiness.

## 5. Work Packets

```text
/design-to-work-packets KIM-1234
```

Use small scoped packets. Do not create broad refactors or unrelated metadata changes.

## 6. Development

Develop manually and with Copilot assistance. Keep changes traceable to the Work Item acceptance criteria.

Rules:

- Do not edit managed package internals.
- Do not hardcode Salesforce record IDs.
- Use sharing declarations intentionally in Apex.
- Check CRUD/FLS for user/business data.

## 7. Local Precheck

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 wi-precheck -WorkItem KIM-1234 -BaseRef HEAD~1
```
```bash
# Mac / Linux
make wi-precheck WORK_ITEM=KIM-1234 BASE_REF=HEAD~1
```

Strict mode can fail on high findings:

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 wi-precheck-strict -WorkItem KIM-1234 -BaseRef origin/main
```
```bash
# Mac / Linux
make wi-precheck-strict WORK_ITEM=KIM-1234 BASE_REF=origin/main
```

Precheck output is advisory for developers and reviewers; it does not approve release.

## 7a. Implementation Review

Run the code review before submitting a PR when the Work Item includes Apex or Flow changes:

```text
/review-implementation KIM-1234
```

The review checks SOQL discipline, sharing model, CRUD/FLS, hardcoded IDs, design alignment, acceptance criteria coverage, and test class quality. Review findings are a draft for human PR reviewers; they do not block or approve the PR automatically.

## 8. Documentation

```text
/create-documentation KIM-1234
/update-documentation-from-diff KIM-1234
```

Write docs under `docs/architecture/` or another approved location. Use placeholders where human evidence is required.

## 9. QA How-To-Test

```text
/create-how-to-test KIM-1234
/review-qa-how-to-test KIM-1234
```

QA docs should include:

- Acceptance criteria mapping.
- Test data placeholders.
- Environment.
- Evidence placeholders.
- Pass/fail and notes sections.

## 10. Config Impact

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 config-impact -WorkItem KIM-1234
```
```bash
# Mac / Linux
make config-impact WORK_ITEM=KIM-1234
make config-pack-skeleton WORK_ITEM=KIM-1234
```

Config record promotion is a separate sidecar review. The skeleton is not an apply script.

## 11. Release Readiness

```text
/pre-promote-report KIM-1234 UAT
/release-readiness-review KIM-1234
```

Inputs should include:

- Work Item context.
- Design and review.
- Precheck output.
- QA docs.
- Config impact.
- Validation evidence if available.

For L/XL Work Items, Work Items with config sidecar changes, or Work Items containing destructive metadata changes, also run a rollback impact analysis before promoting:

```text
/rollback-impact-analysis KIM-1234 UAT
```

This fills the Rollback Impact section of the pre-promote report and identifies whether config sidecar manual rollback steps are required.

## 12. DevOps Center Promotion

Use DevOps Center for Salesforce metadata promotion. The workspace can provide review artifacts but does not promote.

Human approval remains required for:

- Merge/promotion.
- Config sidecar decisions.
- QA signoff.
- Release readiness.

## 13. Azure Wiki Documentation Draft

Dry run:

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 wiki-dry-run -WorkItem KIM-1234 -WikiTitle "Invoice Approval Routing" -WikiSource docs/architecture/KIM-1234.md -AzureWikiRepo "<wiki-repo>"
```
```bash
# Mac / Linux
make wiki-dry-run WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo>
```

Prepare local draft branch:

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 wiki-prepare-branch -WorkItem KIM-1234 -WikiTitle "Invoice Approval Routing" -WikiSource docs/architecture/KIM-1234.md -AzureWikiRepo "<wiki-repo>"
```
```bash
# Mac / Linux
make wiki-prepare-branch WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo>
```

Push approved branch only after human approval and local enablement:

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 wiki-push-approved -WorkItem KIM-1234 -WikiTitle "Invoice Approval Routing" -WikiSource docs/architecture/KIM-1234.md -AzureWikiRepo "<wiki-repo>" -WikiApprovalNote "Approved by <reviewer/date>"
```
```bash
# Mac / Linux
make wiki-push-approved WORK_ITEM=KIM-1234 WIKI_TITLE="Invoice Approval Routing" WIKI_SOURCE=docs/architecture/KIM-1234.md AZURE_WIKI_REPO=<wiki-repo> WIKI_APPROVAL_NOTE="Approved by <reviewer/date>"
```

PR creation, merge, and final publication remain manual Azure DevOps steps.
