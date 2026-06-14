---
title: "DevOps Center Pipeline"
domain: "general"
source_type: "internal_knowledge"
owner: "Salesforce Platform Team"
status: "reviewed"
confidence: "high"
last_reviewed: "2026-06-05"
applies_to:
  - "KimbleOne/Kantata"
related_objects: []
related_config_objects:
  - "DevOps Center Pipeline Configuration"
related_processes:
  - "Metadata Promotion"
  - "Release Management"
keywords:
  - "devops center"
  - "pipeline"
  - "sandbox"
  - "promotion"
  - "metadata"
---

# Summary

Salesforce DevOps Center is the official metadata promotion tool. Changes flow from developer sandboxes through Integration, UAT, and Staging before reaching Production.

# Details

**Pipeline stages (in order):**

| Stage | Org | Type | Notes |
|---|---|---|---|
| Development | IntDev | Full Copy | Shared integration sandbox, not git-managed |
| UAT | UAT | Partial Copy | Business acceptance testing |
| Staging | Staging | Full Copy | Pre-prod dry run |
| Production | Production | Production | Live org |

**Work Item branches** are managed by DevOps Center. Do not manually merge to environment branches.

# Known Package Behavior

- Managed package components (prefix `kmbi__`) cannot be included in change sets or DevOps Center pipelines — they are installed via the managed package installer.
- Custom metadata and custom settings that extend the managed package can be promoted via DevOps Center.
- Permission Set Assignments are not promotable via metadata — must be applied manually or via a script in each org.

# Known Rules

- All metadata changes must be associated with a DevOps Center Work Item.
- IntDev is a shared sandbox — never use it as a source of truth for metadata state.
- Staging deployment must succeed before a Production deployment is scheduled.
- Rollback is manual: restore from a pre-deployment snapshot or re-deploy previous version.

# Edge Cases

- Custom objects added by the managed package (new in a package upgrade) do not appear in DevOps Center until the upgrade is installed in all pipeline orgs.
- Flows that reference managed package objects need to be re-activated after a package upgrade if the package upgrade deactivates them.

# Open Questions

- Is there an automated smoke test suite that runs after each Staging deployment?

# Source Notes

- Salesforce DevOps Center documentation and internal release management runbook, 2025.
