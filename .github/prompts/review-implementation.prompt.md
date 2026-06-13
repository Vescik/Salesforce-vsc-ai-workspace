---
name: review-implementation
description: Review implemented Apex, Flow, LWC, and metadata for a Salesforce/KimbleOne Work Item against the approved design and Salesforce best practices.
agent: code-review
argument-hint: <WORK_ITEM_ID>
---

# Review Implementation

Review the implementation for Work Item `<WORK_ITEM_ID>` before PR submission.

## Scope

Do not rewrite implementation code. Do not modify Salesforce metadata. Do not suggest production deployment steps. Do not assume KimbleOne/Kantata managed package internals or source code. Keep configuration record findings separate from Salesforce metadata findings.

Generated review findings are a draft for human PR reviewers. This review does not approve or block a PR automatically.

Do not fetch Azure DevOps directly in this prompt. Use the normalized local Work Item artifacts created by `/fetch-us <WORK_ITEM_ID>`.

## Source Artifacts To Read

Read these artifacts when present:

- `.ai/context/work-items/<WORK_ITEM_ID>/work-item-summary.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/acceptance-criteria.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/context-pack.md`
- `specs/approved/<WORK_ITEM_ID>.solution-design.md`
- `specs/proposed/<WORK_ITEM_ID>.solution-design.md`
- `.ai/outputs/solution-design/<WORK_ITEM_ID>.design-review.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-metadata.yaml`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-schema.yaml`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-config-records.yaml`
- `.ai/outputs/precheck/<WORK_ITEM_ID>.precheck.md`
- Current Git diff (all changed files in the Work Item branch).

If `work-item-summary.md` or `acceptance-criteria.md` is missing, stop and instruct the user to run `/fetch-us <WORK_ITEM_ID>` first. For other missing artifacts, note the gap and mark resulting assumptions as unconfirmed.

## Review Focus

Check:

1. SOQL and SOSL queries are not inside loops.
2. Sharing model (`with sharing`, `without sharing`, `inherited sharing`) is declared on every Apex class.
3. CRUD and FLS checks are present where user or business data is accessed.
4. No hardcoded Salesforce record IDs appear in the diff; cross-reference against the precheck report.
5. Every acceptance criterion maps to at least one implemented component or test case.
6. Implemented components match the impacted metadata list in the approved solution design.
7. Apex test classes are present for every new Apex class; assertions are non-trivial.
8. Record-triggered Flows are bulkified; fault paths are handled.
9. Config record impact is not mixed into the metadata commit.

## Output

Create:

- `.ai/outputs/code-review/<WORK_ITEM_ID>.code-review.md`

If file writing is not permitted in the current phase, return the review inline and ask the user if they want to save it.

## Required Sections

1. Decision: `APPROVED` / `APPROVED_WITH_COMMENTS` / `BLOCKED`
2. Findings grouped by severity (Blocking / High / Medium / Low) — each finding includes issue, location, evidence, impact, and recommendation
3. Design Alignment Summary
4. Acceptance Criteria Coverage
5. Required Changes Before Merge (if decision is not `APPROVED`)

## Review Rules

- Every finding must cite a specific file, class, method, or line range from the diff.
- Mark uncertainty when a finding cannot be confirmed without org context (e.g., missing schema cards).
- Do not flag style preferences unless they create a runtime or security risk.
- Do not invent findings not supported by the diff or design artifacts.
