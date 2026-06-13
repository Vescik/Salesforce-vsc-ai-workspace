---
name: review-knowledge-note
description: Review an internal KB note for quality, sourcing, and safety.
agent: knowledge-curator
argument-hint: <KNOWLEDGE_NOTE_PATH>
---

# Review Knowledge Note

## Review Criteria

- Source file is present when the note was imported.
- Synced notes can be traced to `.ai/knowledge/sync-state.json` when source provenance is needed.
- Owner is present.
- `last_reviewed` is present and current.
- Confidence is justified.
- Status is correct.
- Related objects, config objects, and processes are populated where known.
- No secrets, credentials, raw data dumps, logs, or uncontrolled sensitive values are present.
- No unsupported claims about KimbleOne/Kantata managed package internals.
- Open questions are clear.
- Summary is concise and traceable to source evidence.
- Claims based on the KB cite source paths.
- The note does not contradict Salesforce schema, anonymized config records, tests, or human-provided facts without an explicit validation question.

## Decision

Return one:

- `APPROVED`
- `APPROVED_WITH_COMMENTS`
- `BLOCKED`

## Output

For each finding, include:

- Severity.
- Evidence or missing evidence.
- Recommendation.
- Whether human validation is required.
