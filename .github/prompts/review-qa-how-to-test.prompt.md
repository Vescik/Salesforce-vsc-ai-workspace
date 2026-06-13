---
name: review-qa-how-to-test
description: Review QA how-to-test instructions for completeness and traceability.
agent: qa-how-to-test-writer
argument-hint: <WORK_ITEM_ID>
---

# Review QA How-to-Test

Review QA how-to-test documentation for `<WORK_ITEM_ID>` for completeness, clarity, and traceability.

## Source Artifacts To Read

Read these artifacts when present:

- `docs/qa-how-to-test/<WORK_ITEM_ID>.md`
- `.ai/outputs/qa/<WORK_ITEM_ID>.how-to-test-draft.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/work-item-summary.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/acceptance-criteria.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/context-pack.md`
- `specs/approved/<WORK_ITEM_ID>.solution-design.md`
- `specs/proposed/<WORK_ITEM_ID>.solution-design.md`
- `.ai/outputs/solution-design/<WORK_ITEM_ID>.design-review.md`
- `.ai/outputs/precheck/<WORK_ITEM_ID>.precheck.md`

## Review Criteria

Review:

- Acceptance criteria coverage.
- Clarity of steps.
- Expected results.
- Required data and configuration.
- Permission and user assumptions.
- Regression coverage.
- Negative cases.
- Evidence to capture.
- Missing open questions.
- Whether any managed package internals are assumed without evidence.

## Output

Return one decision:

- `APPROVED`
- `APPROVED_WITH_COMMENTS`
- `BLOCKED`

Group findings by severity:

- Blocking
- High
- Medium
- Low

For each finding, include:

- Issue.
- Evidence or missing evidence.
- Impact.
- Concrete change required.

## Rules

- Do not rewrite the entire QA document unless asked.
- Do not invent real test data.
- Do not assume KimbleOne/Kantata managed package internals or source code.
- Every functional test case must map to an acceptance criterion, or the finding should call out the gap.
