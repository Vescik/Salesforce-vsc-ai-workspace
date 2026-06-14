---
title: "ADR-002: Separate Private Git Repo for Internal Knowledge Base"
domain: "general"
source_type: "decision"
owner: "Salesforce Platform Team"
status: "accepted"
confidence: "high"
last_reviewed: "2026-01-15"
applies_to:
  - "KimbleOne/Kantata"
keywords:
  - "knowledge base"
  - "ADR"
  - "architecture decision"
  - "documentation"
---

# Decision

Maintain internal knowledge notes about the KimbleOne managed package in a separate private Git repository, synced into the workspace via `make knowledge-sync`.

# Context

Internal knowledge about the managed package (object behaviour, business rules, undocumented constraints) was being stored ad-hoc in Confluence, personal notes, and email threads. This made it hard for AI tooling (Copilot, Claude Code) to access it consistently.

# Decision Rationale

- A private repo keeps sensitive internal documentation separate from the Salesforce metadata repo (which may have broader access).
- Markdown-based notes are portable and easily indexed by AI tooling.
- Git history provides review and audit trail for knowledge changes.
- Syncing into `.ai/knowledge/` keeps the workspace main repo clean.

# Consequences

- Knowledge notes must be maintained in the knowledge base repo, not in the main workspace repo.
- Developers need `read` access to the knowledge base repo to use `make knowledge-sync`.
- Stale notes are a risk — a review cadence must be established.

# Status

Accepted — implemented Q1 2026.

# Review History

- 2026-01-15: Decision made by Platform Lead.
