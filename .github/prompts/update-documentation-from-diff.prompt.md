---
name: update-documentation-from-diff
description: Update existing technical documentation based on current git diff.
agent: tech-doc-writer
argument-hint: <WORK_ITEM_ID>
---

# Update Documentation From Diff

Update existing technical documentation for `<WORK_ITEM_ID>` based on the current Git diff.

## Scope

Do not rewrite the entire document unless the diff proves the whole structure is stale. Do not write implementation code. Do not modify Salesforce metadata. Do not call Salesforce CLI, ADO, MCP servers, GitHub Actions, or external model APIs.

## Source Artifacts To Read

Read these artifacts when present:

- `docs/architecture/<WORK_ITEM_ID>.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/context-pack.md`
- `specs/approved/<WORK_ITEM_ID>.solution-design.md`
- `specs/proposed/<WORK_ITEM_ID>.solution-design.md`
- `.ai/outputs/precheck/<WORK_ITEM_ID>.precheck.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-metadata.yaml`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-config-records.yaml`
- Current Git diff.

## Behavior

- Update only sections affected by the diff.
- Add a `Documentation Change Summary` section if useful.
- Mark unresolved discrepancies between the diff, solution design, context pack, and existing documentation.
- If existing documentation is missing, create a draft using the `create-documentation` structure and state that it is a new draft.

## Rules

- Do not invent missing facts.
- Do not assume KimbleOne/Kantata managed package internals or source code.
- Keep metadata changes separate from KimbleOne/Kantata configuration record changes.
- Do not include raw data dumps, secrets, logs, uncontrolled exports, or credentials.
- Every important update must trace back to Git diff, context pack, solution design, precheck report, or a human-provided fact.
