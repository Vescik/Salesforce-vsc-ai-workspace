---
name: sync-knowledge
description: Sync curated internal Knowledge Base notes from the external source repository.
agent: knowledge-curator
mode: agent
argument-hint: <KB_REPO_URL_OR_LOCAL_PATH>
---

# Sync Knowledge Base

## Purpose

Guide a human through syncing curated internal managed package knowledge from the external Knowledge Base Git repository into this workspace.

## Instructions

- Use the external Knowledge Base Git repository as the source of truth.
- Provide the repository URL or local test repository path through `KB_REPO`; do not hardcode it into project files.
- Start with a dry run:

```bash
make knowledge-sync-dry-run KB_REPO=<repo-url-or-local-path>
```

- Review `.ai/outputs/knowledge-sync/knowledge-sync.md` for copied files, skipped files, and warnings.
- If the dry run is acceptable, sync:

```bash
make knowledge-sync KB_REPO=<repo-url-or-local-path>
```

- After sync completes, call the `rebuild_knowledge_index` MCP tool to refresh the knowledge card index without requiring a separate terminal command.

- If a Work Item context pack needs updating, call the `build_context_pack` MCP tool with the Work Item ID and query topic.

## Rules

- Do not sync raw `imports/` or `archive/` files unless a human explicitly approves `--allow-imports`.
- Do not treat synced KB as guaranteed truth.
- Draft, low-confidence, stale, or unowned notes require human validation.
- If KB conflicts with Salesforce schema, anonymized config records, tests, or human-provided facts, flag the conflict.
- Do not call Salesforce, ADO, deployment tools, config apply tools, GitHub APIs, or external model APIs.

## Output

- Sync command used.
- Report path.
- Index path.
- Warnings and required human review.
- Next context-pack command.
