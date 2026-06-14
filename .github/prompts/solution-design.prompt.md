---
name: solution-design
description: Generate an implementation-neutral Salesforce/KimbleOne solution design from Work Item context.
agent: solution-architect
mode: ask
---

# Generate Solution Design

Use this prompt to produce a functional and technical solution design for a Salesforce/KimbleOne enhancement.

## Scope

Do not write implementation code. Do not modify Salesforce metadata. Do not create configuration record packs. Do not create deployment automation. Do not assume KimbleOne/Kantata managed package internals or source code. Mark uncertainty wherever facts are missing or inferred.

Every recommendation must map to ADO Work Item acceptance criteria.

## Inputs

Use available:

- ADO Work Item summary and acceptance criteria.
- Context pack.
- Repository metadata.
- Salesforce schema.
- Existing Salesforce metadata.
- Anonymized KimbleOne/Kantata configuration records.
- Tests and documentation.
- Human-provided facts.

## Design Structure

Produce a design with these sections:

1. Business summary.
2. Acceptance criteria mapping.
3. Current-state functional flow.
4. Future-state functional flow.
5. Proposed technical flow.
6. Architecture options.
7. Recommended option with reasoning.
8. Impacted metadata.
9. Impacted configuration records.
10. Required fields and UI changes.
11. Security and permission impact.
12. Deployment sequence.
13. QA test strategy.
14. Open questions.
15. Assumptions.
16. Knowledge References.
17. Coverage Table.

### Knowledge References (section 16)

A bullet list, one per cited knowledge note pulled from `relevant-knowledge.yaml`:

- `[<slug>](<.ai/knowledge/...>)` — status, confidence, why cited.

Only cite entries present in `.ai/context/work-items/<WORK_ITEM_ID>/relevant-knowledge.yaml`.
Any citation of a `status: draft` or `confidence: low` knowledge note must be
wrapped in `[unverified]` in the design body (for example:
`[unverified] As noted in [billing-schedule-rules](.ai/knowledge/domains/billing/billing-schedule-rules.md), …`).
`design_lint` will flag unwrapped draft/low-confidence citations as high-severity.

### Coverage Table (section 17)

A markdown table with one row per acceptance criterion:

| AC | Cited Knowledge | Cited Metadata | Notes |
| --- | --- | --- | --- |
| AC-1 | `[invoice-approval-process](.ai/knowledge/domains/billing/invoice-approval-process.md)` | `kmbi__Invoice__c`, `Invoice_Approval` | … |
| AC-2 | … | … | … |

Every AC ID from the work item must appear here. `ac_coverage_check` classifies
each row as `covered | partial | missing` and `precheck_work_item` promotes any
`missing` row to a blocking finding.

## Architecture Options To Consider

Evaluate these options where relevant:

- Flow only.
- Apex only.
- Flow + Apex.
- Custom Metadata.
- KimbleOne configuration records.
- FlexiPage or Layout changes.
- Permission Set changes.

For each option, identify:

- Acceptance criteria covered.
- Benefits.
- Risks.
- Unknowns.
- Metadata impact.
- Configuration record impact.
- Testability.

## UI And Field Guidance

If a field should be added to a UI, specify:

- Object.
- Field.
- FlexiPage or Layout impact.
- Visibility impact.
- Permission impact.
- QA validation.

## Configuration Guidance

If configuration records are involved:

- Identify the records as configuration impact separate from metadata deployment.
- Do not promote transactional records.
- Prefer stable external keys where possible.
- Avoid `Id`, `OwnerId`, and `SystemModstamp` in future configuration packs.

## Proposed Future Outputs

When file-writing support is intentionally added in a later phase, write:

- `specs/proposed/<WORK_ITEM_ID>.solution-design.md`
- `.ai/outputs/solution-design/<WORK_ITEM_ID>.architecture-options.md`

Do not create these outputs unless the user explicitly asks and the phase permits it.

## Response

Return the solution design only. Do not include implementation code.
