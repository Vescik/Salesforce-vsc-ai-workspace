---
name: pre-promote-report
description: Create a pre-promote report for a DevOps Center Work Item.
agent: release-readiness-reviewer
argument-hint: <WORK_ITEM_ID> <TARGET_ENVIRONMENT>
---

# Pre-Promote Report

Create a pre-promote report for `<WORK_ITEM_ID>` targeting `<TARGET_ENVIRONMENT>`.

## Scope

Prepare a report/checklist only. Do not deploy. Do not call Salesforce CLI. Do not apply config records. Do not call ADO, MCP servers, GitHub Actions, or external model APIs. Do not claim deployment or promotion success.

DevOps Center is the official Salesforce metadata promotion mechanism. IntDev is a Full Copy developer/discovery org and is not the source of truth. Config record promotion is a separate sidecar process and is currently analysis/skeleton only. Production config apply is not implemented and requires future controlled tooling/manual approval.

## Source Artifacts To Read

Read these artifacts when present:

- `.ai/context/work-items/<WORK_ITEM_ID>/context-pack.md`
- `specs/approved/<WORK_ITEM_ID>.solution-design.md`
- `specs/proposed/<WORK_ITEM_ID>.solution-design.md`
- `.ai/outputs/solution-design/<WORK_ITEM_ID>.design-review.md`
- `.ai/outputs/precheck/<WORK_ITEM_ID>.precheck.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/config-impact.yaml`
- `.ai/outputs/config-impact/<WORK_ITEM_ID>.config-impact.md`
- `docs/qa-how-to-test/<WORK_ITEM_ID>.md`
- `docs/architecture/<WORK_ITEM_ID>.md`
- Current Git diff, if available.

If an artifact is missing, state that it is missing. Mark assumptions and uncertainty.

## Output Target

Create:

- `.ai/outputs/pre-promote/<WORK_ITEM_ID>-to-<TARGET_ENVIRONMENT>.md`

## Required Sections

1. Work Item Summary
2. Target Environment
3. Metadata Change Summary
4. Config Impact Summary
5. Salesforce Validation Status
6. Precheck Status
7. QA Readiness
8. Documentation Readiness
9. Risks
10. Missing Evidence
11. Manual Approval Checklist
12. Go/No-Go Recommendation

## Review Rules

- Keep metadata readiness separate from config sidecar readiness.
- Do not assume real branch names; use DevOps Center/team-provided branch mapping only.
- Do not assume KimbleOne/Kantata managed package internals or source code.
- Tie findings to Work Item acceptance criteria, local evidence, or human-provided facts.
- Use one recommendation: `GO`, `GO_WITH_RISKS`, or `NO_GO`.
