# Knowledge Base Runbook

## Why The Knowledge Base Exists

KimbleOne/Kantata is a closed managed package. The workspace cannot inspect package internals. The Knowledge Base gives teams a controlled way to reuse reviewed knowledge from exposed behavior, schema, configuration, tests, documentation, and owner validation.

## Instructions vs Knowledge vs Context Pack

- Instructions: rules that tell Copilot and tools how to behave, such as `AGENTS.md` and prompt guardrails.
- Knowledge: curated business or technical notes under `.ai/knowledge/`.
- Context pack: a Work Item-specific bundle that selects relevant metadata, schema, config, and knowledge for a task.

Knowledge supports reasoning. It is not source code and should not become uncontrolled global instruction.

## Source-Of-Truth Model

The intended source of truth is a separate private Knowledge Base Git repository. This workspace syncs selected notes into `.ai/knowledge/`.

Local vendor clone:

```text
.ai/vendor/knowledge-base/
```

This path is ignored.

## Sync Flow

Dry run:

```bash
make knowledge-sync-dry-run KB_REPO=<repo-url-or-local-path>
```

Sync:

```bash
make knowledge-sync KB_REPO=<repo-url-or-local-path>
```

Index:

```bash
make knowledge-index
```

Search:

```bash
make knowledge-search QUERY="invoice approval"
```

## Folder Structure

| Path | Purpose |
| --- | --- |
| `.ai/knowledge/index.yaml` | Domain registry and rules. |
| `.ai/knowledge/domains/` | Domain notes. |
| `.ai/knowledge/object-notes/` | Object-specific notes. |
| `.ai/knowledge/process-maps/` | Process-level notes. |
| `.ai/knowledge/decisions/` | Architecture or business decisions. |
| `.ai/knowledge/governance/` | Governance placeholders. |
| `.ai/knowledge/imports/` | Raw import staging; ignored except `.gitkeep`. |
| `.ai/knowledge/archive/` | Archived placeholders. |

## Markdown Note Standards

Each approved note should include:

- title
- domain
- owner
- status
- confidence
- last_reviewed
- source
- evidence or owner validation

Use the template in `.ai/templates/knowledge-note.md`.

## Draft vs Approved Knowledge

- Draft notes can be used for discovery only.
- Approved notes require review by the domain owner.
- Stale notes require revalidation.
- Conflicting notes must be surfaced to a human reviewer.

## How Context Packs Use Knowledge

`make knowledge-index` turns curated Markdown notes into `knowledge-cards.jsonl`. `make ai-context` searches those cards and includes relevant excerpts under the Work Item context pack.

Knowledge is included as supporting evidence. Prompts should still require acceptance criteria and source artifacts.

## What Not To Store

- Secrets, tokens, passwords, private keys, PATs, or OAuth credentials.
- Raw production or Full Copy data dumps.
- Unreviewed exports.
- Screenshots containing sensitive customer data unless separately approved and controlled.
- Unsupported claims about managed package internals.
- Salesforce record IDs as stable identifiers.

## Governance Model

- Changes should go through pull request review in the Knowledge Base repo.
- Domain owners review approved notes.
- Draft notes are clearly labeled.
- Notes have a review date and confidence level.
- Claims should reference a source artifact, config evidence, test evidence, or named owner validation.

## Troubleshooting

- Repo access denied: verify Git credentials and repository permissions.
- Wrong branch: pass `KB_BRANCH=<branch>`.
- Notes not appearing in context: run `make knowledge-index` after sync.
- Raw import rejected: curate the content into Markdown and remove sensitive fields.
- Conflicting notes: keep both only if clearly labeled and escalate to a domain owner.
