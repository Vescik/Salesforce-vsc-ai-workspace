---
name: build-context
description: Build an implementation-neutral context pack for a Salesforce/KimbleOne Work Item.
agent: work-item-context-curator
mode: ask
---

# Build Context Pack

Use this prompt to assemble relevant context for a Salesforce/KimbleOne solution design.

## Scope

This phase does not implement context indexers, Salesforce CLI calls, MCP servers, Python scripts, parser logic, or CI workflows. Read existing context files if present. If required tools or indexes are missing, ask the user to provide the missing content or run future approved commands when those commands exist.

## Expected Future Inputs

- Repository metadata index.
- Salesforce schema cards.
- Anonymized KimbleOne/Kantata configuration record cards.
- Dependency graph.
- ADO Work Item summary.
- Acceptance criteria.
- Existing tests and documentation.
- Human-provided facts.

## Instructions

1. Start from the ADO Work Item summary and acceptance criteria.
2. Read existing context files for the Work Item if present.
3. Identify metadata, schema, configuration records, tests, and documentation that may be relevant.
4. Keep KimbleOne/Kantata configuration records separate from Salesforce metadata.
5. Do not assume managed package source code or internals.
6. Mark uncertainty and missing context clearly.
7. Do not write implementation code or create actual solution specs.

## Proposed Future Outputs

When file-writing support is intentionally added in a later phase, write:

- `.ai/context/work-items/<WORK_ITEM_ID>/context-pack.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-metadata.yaml`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-schema.yaml`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-config-records.yaml`

Do not create these outputs unless the user explicitly asks and the phase permits it.

## Response

Return a concise context summary with:

- Work Item reference.
- Relevant metadata candidates.
- Relevant schema candidates.
- Relevant configuration record candidates.
- Relevant tests or documentation.
- Missing context.
- Open questions.
