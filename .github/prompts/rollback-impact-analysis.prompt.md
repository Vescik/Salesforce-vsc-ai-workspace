---
name: rollback-impact-analysis
description: Analyze the rollback impact of a Salesforce/KimbleOne Work Item before DevOps Center promotion.
agent: release-readiness-reviewer
argument-hint: <WORK_ITEM_ID> <TARGET_ENVIRONMENT>
---

# Rollback Impact Analysis

Analyze the rollback impact of Work Item `<WORK_ITEM_ID>` before promoting to `<TARGET_ENVIRONMENT>`.

## Scope

Produce an analysis report only. Do not deploy. Do not apply config records. Do not call Salesforce CLI, ADO, MCP servers, GitHub Actions, or external model APIs. Do not claim that a rollback is safe or automatically executable without human review.

DevOps Center is the official Salesforce metadata promotion mechanism. Config record rollback is a separate manual process — production config apply is not implemented in this workspace. All rollback analysis is advisory and requires human validation before any rollback action is taken.

Do not fetch Azure DevOps directly in this prompt. Use the normalized local Work Item artifacts created by `/fetch-us <WORK_ITEM_ID>`.

## Source Artifacts To Read

Read these artifacts when present:

- `.ai/context/work-items/<WORK_ITEM_ID>/work-item-summary.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/acceptance-criteria.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/context-pack.md`
- `specs/approved/<WORK_ITEM_ID>.solution-design.md`
- `specs/proposed/<WORK_ITEM_ID>.solution-design.md`
- `.ai/outputs/solution-design/<WORK_ITEM_ID>.design-review.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/config-impact.yaml`
- `.ai/outputs/config-impact/<WORK_ITEM_ID>.config-impact.md`
- `.ai/outputs/pre-promote/<WORK_ITEM_ID>-to-<TARGET_ENVIRONMENT>.md`
- `.ai/outputs/precheck/<WORK_ITEM_ID>.precheck.md`
- `docs/qa-how-to-test/<WORK_ITEM_ID>.md`
- Current Git diff, if available.

If an artifact is missing, state that it is missing and mark the rollback analysis for that area as incomplete.

## Output

Create:

- `.ai/outputs/rollback/<WORK_ITEM_ID>-to-<TARGET_ENVIRONMENT>.rollback-impact.md`

If file writing is not permitted in the current phase, return the analysis inline and ask the user if they want to save it.

## Required Sections

### 1. Rollback Summary

One paragraph: overall rollback risk rating and the primary driver of that rating.

### 2. Metadata Rollback Path

Describe how a DevOps Center revert would work for this Work Item:

- Which Salesforce metadata components would be reverted.
- What a DevOps Center revert covers and what it does not cover (e.g., data mutations, config records, external system side effects).
- Whether any metadata component changes are destructive (field deletion, object deletion, removal of required fields) that cannot be safely reverted.
- Post-revert validation: which metadata components must be confirmed functional after rollback.

### 3. Config Sidecar Rollback Path

Describe what would be required to roll back configuration record changes:

- List the config objects and record keys identified in `config-impact.yaml` that would need manual rollback.
- Explicitly state: config record rollback is not automated in this workspace. A separate manual process with a system/release owner is required.
- Identify whether a rollback snapshot exists or would need to be captured before promotion.
- List any config records whose rollback is ambiguous or requires investigation.

### 4. Data Impact

Identify whether any data mutations would survive a metadata rollback:

- Records created or modified by Flows or Apex in this Work Item that would not be reverted by a metadata rollback.
- Rollup field values, formula field recalculations, or sharing rule re-evaluations that may be affected.
- Scheduled job or async job state that may be in-flight during rollback.
- Note: if no data mutations are expected, state this explicitly.

### 5. Post-Rollback Validation Steps

List the specific QA how-to-test scenarios that must be re-run to confirm the rollback is complete and the system is stable. Reference the test cases from `docs/qa-how-to-test/<WORK_ITEM_ID>.md` by ID where available.

### 6. Risk Rating

Overall rollback risk:

- `LOW` — metadata rollback via DevOps Center is straightforward; no config or data side effects.
- `MEDIUM` — rollback is possible but requires one or more manual steps beyond DevOps Center revert.
- `HIGH` — rollback involves destructive metadata changes, config record complexity, or data mutations that are difficult to reverse.
- `CRITICAL` — rollback cannot be executed safely without significant manual effort and risk of data or config corruption; escalate to the release/system owner before promoting.

### 7. Open Questions

List any gaps in the available artifacts that prevent a complete rollback analysis.

## Analysis Rules

- Do not assume KimbleOne/Kantata managed package internals or source code beyond what knowledge notes document.
- Cite specific components, config objects, or record keys from workspace artifacts for every risk identified.
- Keep metadata rollback analysis separate from config sidecar rollback analysis.
- Mark every rating as advisory; a human release/system owner must confirm before any rollback action.
- If the pre-promote report does not exist yet, note that rollback analysis is preliminary and should be re-run once the pre-promote report is complete.
