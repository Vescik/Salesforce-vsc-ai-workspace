# Non-Technical Workspace Overview

Audience: managers, product owners, QA leads, business analysts, and solution owners.

## What This Workspace Is

The Salesforce AI Workspace is a guided development support workspace. It gives developers and reviewers a consistent way to collect context, prepare solution designs, generate documentation drafts, write QA how-to-test guidance, and check readiness before release.

It is built around GitHub Copilot/Codex-style tooling, local Python scripts, prompt files, and curated project knowledge.

## Why It Exists

Salesforce work on top of a closed managed package can be hard to reason about because the package internals are not visible. This workspace reduces that risk by grounding AI-assisted work in visible evidence:

- Azure DevOps Work Items and acceptance criteria.
- Repository metadata.
- Salesforce schema exposed to the org.
- Anonymized and controlled configuration records.
- Curated Knowledge Base notes.
- Tests and human-provided facts.

## Problems It Helps Solve

- Better solution design from consistent context.
- Faster discovery of relevant metadata, schema, config, and knowledge.
- More consistent documentation.
- QA how-to-test drafts tied to acceptance criteria.
- Safer release readiness checks.
- Reuse of reviewed KimbleOne/Kantata knowledge without assuming package internals.

## What It Does Not Do

- It does not replace developers.
- It does not replace architects or human review.
- It does not replace DevOps Center.
- It does not deploy Salesforce metadata.
- It does not change production data or configuration records.
- It does not bypass QA, release, or approval gates.
- It does not provide access to managed package source code.

## Main Building Blocks

- Work Item context: local files containing title, description, acceptance criteria, and notes.
- Knowledge Base: reviewed internal notes synced from a separate private repository.
- Metadata index: local cards describing Apex, Flow, LWC, objects, layouts, FlexiPages, permissions, and other metadata.
- Schema index: optional Salesforce CLI read-only schema cards.
- Config record index: optional controlled read-only cards for approved config objects.
- Prompt files: repeatable Copilot workflows for design, review, documentation, QA, and wiki publication.
- Custom agents: role-focused Copilot personas for solution design, QA, docs, release readiness, and knowledge curation.
- Precheck and release readiness: local checks that highlight risks before DevOps Center promotion.
- Azure Wiki draft publication: documentation drafts prepared for human review and manual publication.

## Developer Process Mapping

| Process stage | Workspace support |
| --- | --- |
| Solution Design | Fetch Work Item context, build context pack, use `/solution-design`. |
| Development | Use approved work packets and local metadata context. |
| Dev Unit Testing | Use QA prompts and local precheck findings to plan verification. |
| HAT Deployment | Use DevOps Center; workspace can prepare pre-promote reports only. |
| QA UAT | Generate how-to-test drafts and evidence placeholders. |
| Stage Deployment | Use DevOps Center and release readiness review outputs. |
| Stage QA | Reuse QA docs and capture evidence. |
| Production | Human-approved DevOps Center promotion; workspace does not deploy. |

## Human Approval Points

- Solution design approval.
- Config impact and sidecar decision.
- QA how-to-test review.
- Release readiness review.
- Azure Wiki placement and content review.
- DevOps Center promotion.

## Benefits

- Shared vocabulary and repeatable workflow.
- More explicit assumptions and evidence.
- Less time spent reconstructing context.
- Safer handling of managed package uncertainty.
- Better traceability from acceptance criteria to design, docs, QA, and release checks.

## Limitations

- Output quality depends on Work Item quality and available context.
- Package internals remain unknown unless exposed through metadata, schema, config, tests, or human validation.
- Some commands require Salesforce CLI auth.
- Azure DevOps MCP and Azure Wiki use require local user access.
- Scorecards and reports support decisions; they do not approve releases.

## Example Scenario

1. A developer receives Work Item `KIM-1234`.
2. They run `/fetch-us KIM-1234` to store the Work Item description and acceptance criteria locally.
3. They build a context pack with repo metadata, schema, config, and Knowledge Base hits.
4. Copilot drafts a solution design based on that context.
5. A reviewer checks the design and package-boundary assumptions.
6. The developer implements the scoped changes.
7. The workspace creates QA how-to-test guidance and precheck reports.
8. Metadata promotion remains in DevOps Center.
9. Reviewed documentation can be prepared as an Azure Wiki draft.
