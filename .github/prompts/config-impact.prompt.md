---
name: config-impact
description: Review local config impact evidence for a Salesforce/KimbleOne Work Item.
agent: solution-design-reviewer
argument-hint: <WORK_ITEM_ID>
---

# Config Impact

Review config impact evidence for `<WORK_ITEM_ID>`.

## Scope

Do not call Salesforce CLI, ADO, MCP servers, GitHub Actions, external model APIs, or deployment tools. Do not apply configuration records. Do not modify Salesforce metadata. Treat this as local evidence review only.

Config record promotion is separate from Salesforce metadata promotion. DevOps Center remains the official metadata promotion mechanism. Production config apply is not implemented and requires future controlled tooling/manual approval.

## Source Artifacts To Read

Read these artifacts when present:

- `.ai/context/work-items/<WORK_ITEM_ID>/context-pack.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/config-impact.yaml`
- `.ai/outputs/config-impact/<WORK_ITEM_ID>.config-impact.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-config-records.yaml`
- `config/data-promotion/config-object-registry.yaml`
- `config/kimbleone-packs/<WORK_ITEM_ID>/pack.yaml`
- `specs/proposed/<WORK_ITEM_ID>.solution-design.md`
- `specs/approved/<WORK_ITEM_ID>.solution-design.md`
- Current Git diff.

If `config-impact.yaml` is missing, tell the developer to run:

```bash
make config-impact WORK_ITEM=<WORK_ITEM_ID>
```

## Output

Return a concise config impact summary with:

1. Decision: `CONFIG_IMPACT_REQUIRED`, `NO_CONFIG_IMPACT_FOUND`, or `UNKNOWN`.
2. Evidence reviewed.
3. Impacted config objects and record keys, if known.
4. Missing evidence.
5. Sidecar review needs.
6. Risks and open questions.

Do not create config packs unless the user explicitly asks and the phase permits it.
