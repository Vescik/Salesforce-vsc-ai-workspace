# Internal Knowledge Base

This folder contains a synchronized local copy of curated internal knowledge about managed package behavior, business processes, and company-specific Salesforce/KimbleOne/Kantata usage.

The external private Knowledge Base Git repository is the source of truth. This workspace syncs curated Markdown notes locally with `make knowledge-sync`, indexes them with `make knowledge-index`, and selects relevant notes into Work Item context packs.

Knowledge notes are not global AI instructions. Instructions define rules and guardrails. Knowledge notes define sourced facts, assumptions, process behavior, troubleshooting notes, package behavior, and config-related knowledge.

## Folder Structure

- `domains/`: domain-specific knowledge notes grouped by business area.
- `object-notes/`: Salesforce object-focused notes.
- `process-maps/`: business process notes and process maps.
- `decisions/`: architecture or knowledge-base decision records.
- `governance/`: KB governance notes from the source repository.
- `imports/`: raw import staging in the source repository; not the preferred AI source.
- `archive/`: retired notes; not indexed or copied by default.
- `index.yaml`: human-maintained domain index and knowledge rules.
- `sync-policy.yaml`: local policy that controls what is copied from the external repository.
- `sync-state.json`: generated sync state from the last successful local sync.

## Sync From The External KB Repository

Run a dry run first:

```bash
make knowledge-sync-dry-run KB_REPO=<private-kb-repo-url>
```

Then sync:

```bash
make knowledge-sync KB_REPO=<private-kb-repo-url>
```

The local clone cache is `.ai/vendor/knowledge-base/` and is ignored by Git. Do not use git submodules.

Raw import files are not copied by default. Curated Markdown notes are preferred for AI context.

## Index The Knowledge Base

```bash
make knowledge-index
```

This writes `.ai/context/index/knowledge-cards.jsonl` and `.ai/context/index/knowledge-index-summary.json`.

## Search The Knowledge Base

```bash
make knowledge-search QUERY="invoice approval"
```

Search uses local lexical matching only. It does not call Salesforce, ADO, or external model APIs.

## Context Packs

`make ai-context WORK_ITEM=<WORK_ITEM_ID> QUERY="<topic>"` searches `knowledge-cards.jsonl` and writes:

- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-knowledge.yaml`
- a `Relevant Internal Knowledge` section in `context-pack.md`

Draft, low-confidence, or stale notes are marked for human validation.

## Review Workflow

1. Update curated knowledge in the external KB repository.
2. Sync this workspace with `make knowledge-sync KB_REPO=<private-kb-repo-url>`.
3. Review sync warnings and `.ai/knowledge/sync-state.json`.
4. Run `make knowledge-index`.
5. Rebuild affected Work Item context packs.
6. Review selected KB notes before relying on them in design, QA, or release decisions.

## Metadata Requirements

Curated notes should include metadata for:

- `title`
- `domain`
- `source_type`
- `source_file`
- `owner`
- `status`
- `confidence`
- `last_reviewed`
- `related_objects`
- `related_config_objects`
- `related_processes`
- `keywords`

## Safety Rules

- Do not store secrets, credentials, logs, raw exports, or uncontrolled data dumps.
- Do not treat synced draft or low-confidence knowledge as guaranteed truth.
- Claims based on KB notes must reference the note path or source file path.
- If KB conflicts with Salesforce schema, config records, tests, or human-provided facts, mark the conflict for validation.
- Do not assume KimbleOne/Kantata internals beyond documented KB, schema, config records, tests, or human-confirmed facts.

## Legacy Local Imports

Local deterministic import tooling may exist for creating draft notes, but the external KB repository is the source of truth for curated knowledge. Imported notes default to draft and low confidence until reviewed and moved through the KB governance process.
