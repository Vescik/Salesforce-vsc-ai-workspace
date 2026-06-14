---
name: design-to-work-packets
description: Convert an approved Salesforce/KimbleOne solution design into small implementation-neutral work packets.
agent: implementation-planner
mode: ask
---

# Design To Work Packets

Use this prompt to turn an approved or conditionally approved Salesforce/KimbleOne solution design into small work packets.

## Scope

Do not implement metadata, configuration, tests, documentation, code, parser logic, Salesforce CLI calls, MCP servers, CI workflows, or deployment automation. Create planning artifacts only when a later phase permits file-writing outputs.

Every work packet must map to ADO Work Item acceptance criteria.

## Inputs

Use available:

- Approved solution design.
- Solution design review result.
- ADO Work Item summary.
- Acceptance criteria.
- Context pack.
- Relevant metadata, schema, configuration records, tests, documentation, and human-provided facts.

## Packet Rules

- One packet must have one objective.
- Each packet must include allowed files or component types where possible.
- Each packet must include blocked changes.
- Each packet must map to acceptance criteria.
- Each packet must include definition of done.
- Include separate packets for metadata, configuration impact, tests, documentation, QA how-to-test, and deployment precheck when applicable.
- Keep configuration record promotion separate from metadata promotion.
- Treat DevOps Center as the official Salesforce metadata promotion mechanism.
- Do not assume KimbleOne/Kantata managed package source code or internals.

## Packet Types

Use these packet types:

- `context_analysis`
- `metadata_change`
- `config_impact`
- `tests`
- `documentation`
- `qa_how_to_test`
- `deployment_precheck`
- `code_review` — include when the design includes Apex or Flow changes; the developer runs `/review-implementation <WORK_ITEM_ID>` after development is complete

## Work Packet Template

```yaml
packet_id:
work_item:
title:
type:
objective:
inputs:
allowed_changes:
blocked_changes:
acceptance_criteria:
definition_of_done:
review_notes:
```

## Proposed Future Output Location

When file-writing support is intentionally added in a later phase, create work packet files under:

- `.ai/context/work-items/<WORK_ITEM_ID>/work-packets/`

Do not create these output files unless the user explicitly asks and the phase permits it.

## Response

Return the proposed work packet list and a concise summary. Do not implement actual metadata, configuration, or code changes.
