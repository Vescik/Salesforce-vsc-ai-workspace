# Full Copy Sandbox Rules

## Purpose

All sandbox environments are Full Copy due to managed package requirements. Full Copy data helps discovery and validation, but it does not make a sandbox the source of truth for metadata or configuration promotion.

## Rules

- IntDev is a Full Copy developer/discovery org, not deployment authority.
- Full Copy does not mean Git source of truth.
- DevOps Center remains the official Salesforce metadata promotion mechanism.
- AI can use anonymized config records through curated indexes and context packs.
- Avoid uncontrolled data dumps, broad exports, logs, secrets, and credentials.
- Context packs are curated AI artifacts, not source of truth.
- Validate assumptions with a human architect/admin when behavior depends on KimbleOne/Kantata package configuration.
- Be careful with config changes because Full Copy sandboxes may already contain production-like setup.
- Keep Salesforce metadata promotion separate from config record sidecar review.
- Production config apply is not implemented and requires future controlled tooling/manual approval.

## AI Workspace Boundaries

The AI workspace may prepare context, design drafts, documentation, QA how-to-test drafts, precheck reports, release-readiness reviews, and config impact summaries.

The AI workspace must not deploy to orgs, write to Salesforce, apply config records, replace DevOps Center, or infer KimbleOne/Kantata managed package internals beyond curated evidence.
