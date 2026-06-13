---
name: review-config-impact
description: Review config impact and sidecar readiness before metadata promote.
agent: release-readiness-reviewer
argument-hint: <WORK_ITEM_ID>
---

# Review Config Impact

Review config impact and sidecar readiness for `<WORK_ITEM_ID>`.

## Scope

Review evidence only. Do not deploy, retrieve, apply records, write to Salesforce, call Salesforce CLI, call ADO, call MCP servers, call GitHub Actions, or use external model APIs.

DevOps Center remains the official Salesforce metadata promotion mechanism. Config record promotion is a separate sidecar process and is currently analysis/skeleton only. Production config apply is not implemented and requires future controlled tooling/manual approval.

## Source Artifacts To Read

Read these artifacts when present:

- `.ai/context/work-items/<WORK_ITEM_ID>/config-impact.yaml`
- `.ai/outputs/config-impact/<WORK_ITEM_ID>.config-impact.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-config-records.yaml`
- `config/kimbleone-packs/<WORK_ITEM_ID>/pack.yaml`
- `config/kimbleone-packs/<WORK_ITEM_ID>/README.md`
- `.ai/deployment/runbooks/config-sidecar.md`
- `.ai/outputs/precheck/<WORK_ITEM_ID>.precheck.md`
- Current Git diff.

## Decision

Return one decision:

- `CONFIG_READY_FOR_SIDECAR_REVIEW`
- `CONFIG_READY_WITH_RISKS`
- `CONFIG_BLOCKED`
- `NO_CONFIG_IMPACT_FOUND`

## Review Criteria

Review:

1. Whether config impact is required.
2. Whether impacted objects and records are identified.
3. Whether stable external keys are known.
4. Whether system fields and transactional records are excluded.
5. Whether sidecar review and manual approvals are clear.
6. Whether metadata promotion can proceed independently through DevOps Center.
7. Missing evidence and open questions.
