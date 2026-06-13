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
- To browse all notes in a domain, use the MCP tool `list_knowledge_domain` with the domain name (e.g. `billing`, `time-expense`).
- To read a full note after finding it by search, use `get_knowledge_note` with the note path.
- Treat the external Knowledge Base Git repository as the source of truth and `.ai/knowledge/` as the synchronized local copy.
- Use concise cards and excerpts, not full raw documents.
- Cite knowledge note paths and source file paths.
- Do not assume KimbleOne/Kantata internals beyond documented knowledge, schema, config records, tests, or human-confirmed facts.

## Confidence and Risk Rules

Apply the following rules to every knowledge note before using it.

**Staleness threshold:** A note is stale if `last_reviewed` is more than 180 days ago, missing, or a placeholder (`YYYY-MM-DD`).

**Confidence interpretation:**
- `confidence: high` — Use directly; cite the path.
- `confidence: medium` — Use with a note that human validation is recommended.
- `confidence: low` — Surface to the human; do NOT use as the basis for a design decision.

**Status interpretation:**
- `status: reviewed` or `status: approved` — Eligible for direct use.
- `status: draft` — Include in context but mark clearly as unvalidated. Ask the human whether to trust it.

**Risk flag handling:**
- `possible_secret` — STOP. Do not cite content. Notify human to review the note immediately.
- `low_confidence` — Always escalate: tell the human the note is low-confidence before using it.
- `stale_review` — Cite the `last_reviewed` date explicitly and note its age.
- `missing_owner` — Flag as unverifiable; do not use without human confirmation.
- `draft_status` — Require explicit human confirmation before citing in a solution design.
- `missing_front_matter` — Treat as lowest-quality source; present with a warning.

**Escalation rule:** If any note has `low_confidence`, `draft_status`, or `missing_owner` in its `risk_flags`, ask the human before using it in a solution design. Present the flags verbatim.

## Output

- Suggested KB notes to include.
- Why each note is relevant.
- Risk flags and staleness for each note.
- Open validation questions.
- Recommended next context-pack command.
- Write `.ai/context/work-items/<WORK_ITEM_ID>/relevant-knowledge.yaml` listing selected notes with their risk flags when building context for a Work Item.
