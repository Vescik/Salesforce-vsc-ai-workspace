---
title: "Knowledge Base Data Handling Policy"
domain: "general"
source_type: "governance"
owner: "Salesforce Platform Team"
status: "reviewed"
confidence: "high"
last_reviewed: "2026-01-15"
applies_to:
  - "KimbleOne/Kantata"
keywords:
  - "governance"
  - "data handling"
  - "policy"
  - "security"
---

# Purpose

This policy governs what may and may not be stored in the Salesforce Knowledge Base repository.

# Permitted Content

- Documented business rules and process descriptions
- Object and field notes (field names, types, known behaviours)
- Architecture Decision Records (ADRs)
- Process maps and workflow descriptions
- Known package behaviours and constraints
- Open questions and areas requiring human validation
- Source document references (not the source documents themselves)

# Prohibited Content

- Salesforce org IDs, record IDs, or user IDs
- Authentication credentials, tokens, API keys, or passwords
- Raw data exports or query results from any Salesforce org
- Personally Identifiable Information (PII) about employees or customers
- Customer data of any kind
- Financial figures linked to real customers or contracts
- Unpublished Kantata roadmap information

# Review Requirements

- All notes with `status: draft` must be reviewed by the Platform Team before being referenced in production work.
- Notes with `confidence: low` must not be acted upon without human verification.
- All notes must be reviewed at least annually (`last_reviewed` date must be within 12 months).

# Access

- Read access: All Salesforce Platform Team members
- Write access: Platform Team leads and senior developers
- No external access

# Source Notes

- Adopted from internal platform team guidelines, 2026-01-15.
