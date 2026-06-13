---
name: config-delta-plan
description: Plan a KimbleOne/Kantata config delta sidecar from local config impact artifacts.
agent: implementation-planner
argument-hint: <WORK_ITEM_ID>
---

# Config Delta Plan

Create a planning-only config delta sidecar plan for `<WORK_ITEM_ID>`.

## Scope

Do not apply records. Do not write to Salesforce. Do not call Salesforce CLI, ADO, MCP servers, GitHub Actions, external model APIs, or deployment tools. Do not create production deployment steps. Keep the output as a draft plan for human review.

Config records are separate from Salesforce metadata. DevOps Center remains the official Salesforce metadata promotion mechanism. Production config apply is not implemented and requires future controlled tooling/manual approval.

## Source Artifacts To Read

Read these artifacts when present:

- `.ai/context/work-items/<WORK_ITEM_ID>/config-impact.yaml`
- `.ai/outputs/config-impact/<WORK_ITEM_ID>.config-impact.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-config-records.yaml`
- `config/data-promotion/config-object-registry.yaml`
- `config/kimbleone-packs/<WORK_ITEM_ID>/pack.yaml`
- `config/kimbleone-packs/<WORK_ITEM_ID>/README.md`
- `specs/proposed/<WORK_ITEM_ID>.solution-design.md`
- `specs/approved/<WORK_ITEM_ID>.solution-design.md`

If the skeleton pack is missing and config impact appears required, tell the developer to run:

```bash
make config-pack-skeleton WORK_ITEM=<WORK_ITEM_ID>
```

## Output

Return a draft sidecar plan with:

1. Config delta objective.
2. Candidate config objects.
3. Candidate record keys.
4. Required external key review.
5. Fields to exclude.
6. Dry-run/diff/rollback considerations for future tooling.
7. Manual approvals.
8. Open questions.

Do not include raw data dumps, Salesforce IDs, secrets, logs, or uncontrolled exports.
