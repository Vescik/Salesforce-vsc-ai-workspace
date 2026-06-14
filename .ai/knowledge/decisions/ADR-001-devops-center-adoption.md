---
title: "ADR-001: Adopt Salesforce DevOps Center as Official Promotion Tool"
domain: "general"
source_type: "decision"
owner: "Salesforce Platform Team"
status: "accepted"
confidence: "high"
last_reviewed: "2025-09-01"
applies_to:
  - "KimbleOne/Kantata"
keywords:
  - "devops center"
  - "ADR"
  - "architecture decision"
  - "metadata promotion"
---

# Decision

Adopt Salesforce DevOps Center as the single official mechanism for promoting metadata changes through the pipeline (IntDev → UAT → Staging → Production). Change sets are no longer permitted for production deployments.

# Context

Prior to Q3 2025, the team used manual change sets for metadata promotion. This led to:
- Missed metadata components (manual selection error-prone)
- No audit trail linking changes to work items
- Conflicts when multiple developers promoted simultaneously
- No rollback capability

# Decision Rationale

- DevOps Center provides Work Item–based promotion with automatic conflict detection.
- Git-backed pipeline provides audit history.
- Native Salesforce tooling — no third-party licence required.
- Aligned with Salesforce's recommended practice for managed package customisation projects.

# Consequences

- All developers must use DevOps Center to track and promote changes.
- IntDev remains a shared sandbox not managed directly by Git — developers pull changes from IntDev into DevOps Center Work Items.
- Change sets are still permitted for emergency hotfixes but must be followed by a retroactive DevOps Center work item.

# Status

Accepted — implemented Q4 2025.

# Review History

- 2025-09-01: Decision made by Platform Lead and Engineering Manager.
