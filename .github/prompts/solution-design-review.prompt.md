---
name: solution-design-review
description: Review a proposed Salesforce/KimbleOne solution design before implementation planning.
agent: solution-design-reviewer
mode: ask
---

# Review Solution Design

Use this prompt to review a proposed Salesforce/KimbleOne solution design before development or implementation planning.

## Scope

Do not rewrite the entire solution unless asked. Do not generate implementation code. Do not assume KimbleOne/Kantata managed package internals or source code. Keep configuration record impact separate from Salesforce metadata impact.

## Inputs

Read available:

- Proposed solution design.
- ADO Work Item summary.
- Acceptance criteria.
- Context pack.
- Relevant metadata, schema, configuration records, tests, documentation, and human-provided facts.

## Review Instructions

1. Validate acceptance criteria coverage.
2. Challenge the Flow vs Apex choice and confirm the reasoning is explicit.
3. Check whether KimbleOne/Kantata configuration-record impact is handled separately from Salesforce metadata.
4. Check impacted metadata completeness.
5. Check FlexiPage, Layout, field visibility, and Permission Set impacts.
6. Check security, CRUD, and FLS considerations where user or business data is involved.
7. Check deployment sequencing through DevOps Center.
8. Check QA testability and whether expected validations are specific.
9. Check assumptions, risks, open questions, and missing evidence.
10. Mark uncertainty where the available context is incomplete.

## Decision

Return one decision:

- `APPROVED`
- `APPROVED_WITH_COMMENTS`
- `BLOCKED`

## Findings

Group findings by:

- Blocking.
- High.
- Medium.
- Low.

For each finding, include:

- Issue.
- Evidence or missing evidence.
- Impact.
- Recommendation.

## Proposed Future Output

When file-writing support is intentionally added in a later phase, write:

- `.ai/outputs/solution-design/<WORK_ITEM_ID>.design-review.md`

Do not create this output unless the user explicitly asks and the phase permits it.

## Response

Return the decision, findings, concrete recommendations, and a concise readiness summary.
