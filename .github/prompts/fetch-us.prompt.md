---
name: fetch-us
description: Fetch and normalize an Azure DevOps Work Item for the Copilot-only Salesforce AI Workspace.
agent: work-item-context-curator
mode: agent
---

# Fetch Azure DevOps Work Item

Use this prompt as `/fetch-us <WORK_ITEM_ID>` to acquire User Story or Work Item context before solution design, documentation, QA, or precheck work.

## Scope

Read Azure DevOps Work Items only. Do not create, update, assign, transition, comment on, or link Work Items. Do not call Salesforce CLI, deploy metadata, apply configuration records, call GitHub Actions, or use external model APIs.

## Approved Source

1. Prefer the `ado-remote-mcp` server from `.vscode/mcp.json`.
2. Use only read-only Azure DevOps MCP tools that retrieve Work Item data.
3. If MCP is unavailable, ask the user to paste the Work Item title, description, acceptance criteria, linked items, comments, and known constraints.

## Extract

- Work Item ID.
- Work Item type.
- Title.
- State.
- Description.
- Acceptance criteria.
- Area path.
- Iteration path.
- Tags.
- Links and related Work Items, if available.
- Relevant comments or discussion notes, if exposed by the read-only tool.
- Risks.
- Assumptions.
- Open questions.

## Normalize And Write

Write these local artifacts:

- `.ai/context/work-items/<WORK_ITEM_ID>/ado-work-item.json`
- `.ai/context/work-items/<WORK_ITEM_ID>/work-item-summary.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/acceptance-criteria.md`

The JSON file should include the extracted fields above, source metadata, and any missing fields as empty strings or empty arrays. Do not include secrets, raw exports, credentials, or unrelated ADO data.

## Output

Return a concise summary with:

- Work Item title and state.
- Acceptance criteria count.
- Missing fields or open questions.
- Files written.
- Recommended next command (auto-seeds the search query from the acceptance criteria):

```bash
make ai-context-auto WORK_ITEM=<WORK_ITEM_ID>
```

If you want to override the auto-extracted keywords, fall back to:

```bash
make ai-context WORK_ITEM=<WORK_ITEM_ID> QUERY="<business topic>"
```

`ai-context-auto` runs `extract_ac_keywords` over the AC + ADO description, expands
synonyms from `.ai/config/search-synonyms.yaml`, and ranks by IDF before
piping the result into `make ai-context`.

Every downstream recommendation must map to extracted acceptance criteria.
