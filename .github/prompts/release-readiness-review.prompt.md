---
name: release-readiness-review
description: Review Work Item release readiness before DevOps Center promote.
agent: release-readiness-reviewer
argument-hint: <WORK_ITEM_ID>
---

# Release Readiness Review

Review release readiness for `<WORK_ITEM_ID>` before DevOps Center promote.

## Scope

Perform evidence review only. Do not deploy. Do not call Salesforce CLI. Do not apply records. Do not call ADO, GitHub Actions, MCP servers, or external model APIs. Do not approve production release automatically.

DevOps Center is the official Salesforce metadata promotion mechanism. IntDev is a Full Copy developer/discovery org and is not the source of truth. Config record promotion is a separate sidecar process and is currently analysis/skeleton only. Production config apply is not implemented and requires future controlled tooling/manual approval.

## Source Artifacts To Read

Read available:

- Work Item summary and acceptance criteria.
- Context pack.
- Solution design and design review.
- Relevant metadata and schema context.
- Config impact artifacts and config pack skeleton if relevant.
- Local precheck report.
- QA how-to-test documentation.
- Technical documentation and release notes.
- Current Git diff.
- Human-provided DevOps Center status.

Mark every missing artifact or unknown status.

## Review Areas

1. Metadata readiness.
2. Config sidecar readiness.
3. QA readiness.
4. Documentation readiness.
5. Deployment sequencing.
6. Assumptions and open questions.
7. DevOps Center compatibility.

## Decision

Return one decision:

- `APPROVED_FOR_PROMOTE`
- `APPROVED_WITH_RISKS`
- `BLOCKED`

## Response

For each review area, include:

- Status.
- Evidence reviewed.
- Missing evidence.
- Risks.
- Required action.

End with a Go/No-Go recommendation for human reviewers and the specific conditions that must be satisfied before DevOps Center promote.
