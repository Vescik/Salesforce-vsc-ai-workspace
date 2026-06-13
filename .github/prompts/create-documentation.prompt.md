---
name: create-documentation
description: Generate technical documentation for a Salesforce/KimbleOne Work Item.
agent: tech-doc-writer
argument-hint: <WORK_ITEM_ID>
---

# Create Documentation

Generate draft technical documentation for `<WORK_ITEM_ID>`.

## Scope

Do not write implementation code. Do not modify Salesforce metadata. Do not call Salesforce CLI, ADO, MCP servers, GitHub Actions, or external model APIs. Do not invent missing facts. Generated documentation is a draft requiring human review.

Do not fetch Azure DevOps directly in this prompt. Use the normalized local Work Item artifacts created by `/fetch-us <WORK_ITEM_ID>`.

## Source Artifacts To Read

Read these artifacts when present:

- `.ai/context/work-items/<WORK_ITEM_ID>/work-item-summary.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/acceptance-criteria.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/context-pack.md`
- `specs/approved/<WORK_ITEM_ID>.solution-design.md`
- `specs/proposed/<WORK_ITEM_ID>.solution-design.md`
- `.ai/outputs/precheck/<WORK_ITEM_ID>.precheck.md`
- `.ai/outputs/solution-design/<WORK_ITEM_ID>.design-review.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-metadata.yaml`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-config-records.yaml`
- Current Git diff.

If `work-item-summary.md` or `acceptance-criteria.md` is missing, stop and instruct the user to run `/fetch-us <WORK_ITEM_ID>` first. For other missing artifacts, state that they are missing and mark assumptions or uncertainty.

## Output

Create:

- `docs/architecture/<WORK_ITEM_ID>.md`

Optionally create:

- `docs/release-notes/<WORK_ITEM_ID>.md` if release notes are applicable.
- `.ai/outputs/docs/<WORK_ITEM_ID>.documentation-draft.md` if the docs folder should not be updated directly.

## Required Sections

1. Work Item Summary
2. Business Context
3. Technical Summary
4. Current-State vs Future-State
5. Changed Salesforce Metadata
6. Changed KimbleOne/Kantata Config Records
7. Functional Flow
8. Technical Flow
9. UI/FlexiPage/Layout Impact
10. Permission/Security Impact
11. Data/Config Considerations
12. Deployment Notes with DevOps Center
13. Config Record Promotion Notes
14. Rollback / Support Notes
15. Known Risks
16. Open Questions
17. References / Source Artifacts

## Documentation Rules

- Do not assume KimbleOne/Kantata managed package internals or source code.
- Do not include raw data dumps, secrets, logs, uncontrolled exports, or credentials.
- Clearly separate metadata changes from KimbleOne/Kantata configuration record changes.
- Every important statement must trace back to a source artifact or human-provided fact.
- Use placeholders such as `<OBJECT_API_NAME>`, `<FLOW_NAME>`, and `<CONFIG_OBJECT_API_NAME>` when facts are not confirmed.
