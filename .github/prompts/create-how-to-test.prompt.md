---
name: create-how-to-test
description: Generate QA how-to-test instructions for a Salesforce/KimbleOne Work Item.
agent: qa-how-to-test-writer
argument-hint: <WORK_ITEM_ID>
---

# Create QA How-to-Test

Generate draft QA how-to-test instructions for `<WORK_ITEM_ID>`.

## Scope

Do not modify Salesforce metadata. Do not write implementation code. Do not call Salesforce CLI, ADO, MCP servers, GitHub Actions, or external model APIs. Do not invent real data. Generated QA documentation is a draft requiring human review.

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
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-config-records.yaml`
- `.ai/outputs/precheck/<WORK_ITEM_ID>.precheck.md`
- Current Git diff.

If `work-item-summary.md` or `acceptance-criteria.md` is missing, stop and instruct the user to run `/fetch-us <WORK_ITEM_ID>` first. For other missing artifacts, state that they are missing and mark assumptions or uncertainty.

## Output

Create:

- `docs/qa-how-to-test/<WORK_ITEM_ID>.md`

Optionally create:

- `.ai/outputs/qa/<WORK_ITEM_ID>.how-to-test-draft.md` if the docs folder should not be updated directly.

## Required Sections

1. Objective
2. Scope
3. Test Environment
4. Required User / Profile / Permission Set
5. Required Test Data / Config
6. Preconditions
7. Functional Test Cases mapped to Acceptance Criteria
8. Regression Tests
9. Negative Tests
10. Permission/Security Tests
11. Config-Related Tests
12. Evidence to Capture
13. Known Limitations
14. Open Questions
15. QA Sign-off

## Test Case Format

Each test case must include:

- Test Case ID
- Related AC ID
- Preconditions
- Steps
- Expected Result
- Evidence to Capture
- Notes

## QA Rules

- Every functional test case must map to an acceptance criterion.
- Regression, negative, and edge-case tests must be explicitly labeled.
- Do not invent real records, users, configuration values, or customer data.
- Use placeholders such as `<TEST_USER>`, `<OBJECT_API_NAME>`, `<RECORD_NAME>`, and `<CONFIG_OBJECT_API_NAME>`.
- Do not assume KimbleOne/Kantata managed package internals or source code.
- Output must be understandable for QA and non-developer users.
