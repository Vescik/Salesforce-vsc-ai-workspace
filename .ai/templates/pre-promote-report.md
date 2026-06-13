# Pre-Promote Report

## Work Item ID

`<WORK_ITEM_ID>`

## Target Environment

`<TARGET_ENVIRONMENT>`

## Source Branch / Work Item Branch

`<BRANCH_NAME>`

## Metadata Changes

| Metadata Type | Component | Status | Notes |
| --- | --- | --- | --- |
| `<METADATA_TYPE>` | `<COMPONENT_NAME>` | `<STATUS>` | `<NOTES>` |

## Config Changes

| Config Object API Name | Config Record Key | Status | Notes |
| --- | --- | --- | --- |
| `<CONFIG_OBJECT_API_NAME>` | `<CONFIG_RECORD_EXTERNAL_KEY>` | `<STATUS>` | `<NOTES>` |

## Salesforce Validation Status

- Validation command or reference: `<VALIDATION_REFERENCE>`
- Result: `<PASS_FAIL_NOT_RUN>`
- Notes: `<NOTES>`

## Apex Test Status

- Test scope: `<TEST_SCOPE>`
- Result: `<PASS_FAIL_NOT_RUN>`
- Notes: `<NOTES>`

## Precheck Status

`<PASS_FAIL_BLOCKED>`

## Deployment Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| `<RISK>` | `<IMPACT>` | `<MITIGATION>` |

## Rollback Impact

Rating: `<LOW|MEDIUM|HIGH|CRITICAL>`

### Metadata Rollback Path

`<Describe how a DevOps Center revert covers this Work Item and what it does not cover.>`

### Config Sidecar Rollback Path

`<Describe manual config record rollback steps required. State if none are needed. Note: config record rollback is not automated in this workspace.>`

### Data Impact

`<Describe any data mutations (records written, flows triggered) that would not be reverted by a metadata rollback. State "None expected" if applicable.>`

### Post-Rollback Validation Steps

`<List QA test case IDs from docs/qa-how-to-test/<WORK_ITEM_ID>.md that must be re-run to confirm the system is stable after rollback.>`

_Use `/rollback-impact-analysis <WORK_ITEM_ID> <TARGET_ENVIRONMENT>` to generate a detailed version of this section._

## Manual Approval Checklist

- [ ] Work Item acceptance criteria reviewed.
- [ ] Metadata changes reviewed.
- [ ] Configuration impact reviewed separately.
- [ ] Salesforce validation completed or explicitly deferred.
- [ ] Apex tests completed or explicitly deferred.
- [ ] QA how-to-test reviewed.
- [ ] Rollback impact reviewed.

## Go / No-Go Recommendation

`<GO|NO_GO|GO_WITH_APPROVAL>`
