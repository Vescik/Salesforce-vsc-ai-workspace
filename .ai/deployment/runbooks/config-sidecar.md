# Config Sidecar Runbook

## Purpose

KimbleOne/Kantata behavior may depend on configuration records. Config records are not the same as Salesforce metadata, so their review and promotion must be handled separately from DevOps Center metadata promotion.

Config record promotion is a separate sidecar process and is currently analysis/skeleton only. Production config apply is not implemented in this workspace and requires future controlled tooling/manual approval.

## Current Implemented Support

- Config object registry.
- Config record indexing.
- Config impact analysis.
- Config pack skeleton.
- Local config diff.

## Current Not Implemented

- Config apply.
- Production writes.
- Automatic rollback.
- Autonomous config deployment.

## Future Sidecar Flow

1. Identify config impact for the Work Item.
2. Build a config delta pack.
3. Review stable external keys.
4. Run dry-run compare.
5. Obtain manual approval.
6. Apply through controlled tooling.
7. Capture rollback snapshot.
8. Record audit log.

## Rules

- Do not use Salesforce IDs as keys.
- Stable external keys are required where possible.
- Exclude `Id`, `OwnerId`, `SystemModstamp`, and similar system-managed fields from config packs.
- Do not promote transactional records.
- Separate config record promotion from Salesforce metadata promotion.
- Production apply requires release/system owner approval.
- Do not commit raw data dumps, secrets, logs, or uncontrolled exports.
- Use curated, anonymized indexes and context packs for AI review.
