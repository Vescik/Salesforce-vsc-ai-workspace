# Salesforce Knowledge Base

Internal knowledge base for Salesforce/KimbleOne managed package development.

## Structure

| Folder | Purpose |
|---|---|
| `domains/` | Domain-specific knowledge by functional area |
| `object-notes/` | Notes on specific Salesforce / KimbleOne objects |
| `decisions/` | Architecture Decision Records (ADRs) |
| `governance/` | Data handling, access, and review policies |
| `process-maps/` | End-to-end business process documentation |

## Usage

Sync into the workspace with:

```bash
make knowledge-sync KB_REPO=git@github.com:Vescik/Salesforce-knowledge-base.git
```

## Rules

- All notes are internal — do not publish externally.
- `status: draft` notes require human review before acting on them.
- If a note conflicts with current Salesforce schema or config, flag for validation.
- No credentials, org IDs, or raw data exports in this repo.
