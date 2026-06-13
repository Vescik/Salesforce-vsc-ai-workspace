# Work Item Local Flow

## Purpose

Use this local flow on a DevOps Center-managed Work Item branch. The AI workspace prepares context, reports, and review artifacts only. It does not run retrieve/deploy commands as part of this runbook.

## Steps

1. Checkout the Work Item branch created by DevOps Center.

2. Build local context:

```bash
make ai-index-repo
make ai-index-schema ORG=IntDev
make ai-index-config ORG=IntDev
make ai-context WORK_ITEM=<WORK_ITEM_ID> QUERY="<business topic>"
```

3. Use Copilot prompts for design and planning:

```text
/solution-design <WORK_ITEM_ID>
/solution-design-review <WORK_ITEM_ID>
/design-to-work-packets <WORK_ITEM_ID>
```

4. Developer performs scoped retrieve/compare using the team process and Beyond Compare if needed.

5. Run config impact and local precheck:

```bash
make config-impact WORK_ITEM=<WORK_ITEM_ID>
make wi-precheck WORK_ITEM=<WORK_ITEM_ID> BASE_REF=HEAD~1
```

6. Commit and push using the team process for the DevOps Center-managed branch.

7. Use Copilot prompts for documentation and QA:

```text
/create-documentation <WORK_ITEM_ID>
/create-how-to-test <WORK_ITEM_ID>
```

## Notes

- The AI workspace currently does not run retrieve/deploy commands as part of this runbook.
- If the team retrieves metadata manually, keep scope tight and review the Git diff carefully.
- DevOps Center remains the official Salesforce metadata promotion mechanism.
- IntDev is a Full Copy developer/discovery org and is not the source of truth.
- Config record promotion is a separate sidecar process and is currently analysis/skeleton only.
- Production config apply is not implemented and requires future controlled tooling/manual approval.
- If `make config-impact` is not available in the current branch, create or review the equivalent local config impact artifact before promote.
