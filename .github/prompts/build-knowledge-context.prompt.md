---
name: build-knowledge-context
description: Select relevant internal KB notes for a Work Item topic.
agent: knowledge-curator
argument-hint: <WORK_ITEM_ID> <QUERY>
---

# Build Knowledge Context

## Purpose

Help select relevant internal KB notes for a Work Item without loading the entire knowledge base into the prompt.

## Inputs

- Work Item ID.
- Query or business topic.
- `.ai/context/index/knowledge-cards.jsonl`, when present.
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-knowledge.yaml`, when present.
- Context pack, when present.
- `.ai/knowledge/sync-state.json`, when sync provenance is needed.

## Instructions

- Prefer `make knowledge-search QUERY="<QUERY>"` or the read-only `salesforce-context` MCP tool `get_related_knowledge`.
- Treat the external Knowledge Base Git repository as the source of truth and `.ai/knowledge/` as the synchronized local copy.
- Use concise cards and excerpts, not full raw documents.
- Mark draft, low-confidence, stale, or missing-owner notes as requiring validation.
- Cite knowledge note paths and source file paths.
- Do not assume KimbleOne/Kantata internals beyond documented knowledge, schema, config records, tests, or human-confirmed facts.

## Output

- Suggested KB notes to include.
- Why each note is relevant.
- Risks or staleness.
- Open validation questions.
- Recommended next context-pack command.
