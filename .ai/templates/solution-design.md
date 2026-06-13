# Solution Design

## Header / Metadata

- Work Item ID: `<WORK_ITEM_ID>`
- Title: `<WORK_ITEM_TITLE>`
- Status: `<DRAFT|REVIEWED|APPROVED>`
- Author: `<AUTHOR>`
- Last updated: `<YYYY-MM-DD>`
- Related artifacts:
  - Work Item summary: `.ai/context/work-items/<WORK_ITEM_ID>/work-item-summary.md`
  - Context pack: `.ai/context/work-items/<WORK_ITEM_ID>/context-pack.md`

## Template Rules

- Do not include implementation code.
- Do not assume KimbleOne/Kantata managed package internals or source code.
- Every recommendation must map to acceptance criteria.
- Mark uncertainty where facts are missing or inferred.
- Treat KimbleOne/Kantata configuration records separately from Salesforce metadata.
- Treat DevOps Center as the official Salesforce metadata promotion mechanism.

## Business Requirement

`<BUSINESS_REQUIREMENT_SUMMARY>`

## Acceptance Criteria Mapping

| AC ID | Acceptance Criterion | Design Response | Evidence / Notes |
| --- | --- | --- | --- |
| AC-1 | `<AC_TEXT>` | `<DESIGN_RESPONSE>` | `<NOTES>` |

## Current-State Functional Flow

1. `<CURRENT_STEP_1>`
2. `<CURRENT_STEP_2>`

## Proposed Future-State Functional Flow

1. `<FUTURE_STEP_1>`
2. `<FUTURE_STEP_2>`

## Proposed Technical Flow

1. `<TECHNICAL_STEP_1>`
2. `<TECHNICAL_STEP_2>`

## Architecture Options

### Flow Only

- Coverage: `<AC_IDS>`
- Benefits: `<BENEFITS>`
- Risks: `<RISKS>`
- Unknowns: `<UNKNOWNS>`
- Recommendation: `<YES_NO_OR_PARTIAL>`

### Apex Only

- Coverage: `<AC_IDS>`
- Benefits: `<BENEFITS>`
- Risks: `<RISKS>`
- Unknowns: `<UNKNOWNS>`
- Recommendation: `<YES_NO_OR_PARTIAL>`

### Flow + Apex

- Coverage: `<AC_IDS>`
- Benefits: `<BENEFITS>`
- Risks: `<RISKS>`
- Unknowns: `<UNKNOWNS>`
- Recommendation: `<YES_NO_OR_PARTIAL>`

### Custom Metadata

- Coverage: `<AC_IDS>`
- Benefits: `<BENEFITS>`
- Risks: `<RISKS>`
- Unknowns: `<UNKNOWNS>`
- Recommendation: `<YES_NO_OR_PARTIAL>`

### KimbleOne/Kantata Config Records

- Coverage: `<AC_IDS>`
- Benefits: `<BENEFITS>`
- Risks: `<RISKS>`
- Unknowns: `<UNKNOWNS>`
- Recommendation: `<YES_NO_OR_PARTIAL>`

### FlexiPage/Layout Change

- Coverage: `<AC_IDS>`
- Benefits: `<BENEFITS>`
- Risks: `<RISKS>`
- Unknowns: `<UNKNOWNS>`
- Recommendation: `<YES_NO_OR_PARTIAL>`

### Permission Set Change

- Coverage: `<AC_IDS>`
- Benefits: `<BENEFITS>`
- Risks: `<RISKS>`
- Unknowns: `<UNKNOWNS>`
- Recommendation: `<YES_NO_OR_PARTIAL>`

## Recommended Design

- Recommended option: `<OPTION_NAME>`
- Reasoning: `<REASONING>`
- Acceptance criteria covered: `<AC_IDS>`
- Tradeoffs: `<TRADEOFFS>`

## Impacted Salesforce Metadata

| Metadata Type | Component | Change Summary | Related AC |
| --- | --- | --- | --- |
| `<METADATA_TYPE>` | `<COMPONENT_NAME>` | `<CHANGE_SUMMARY>` | `<AC_IDS>` |

## Impacted KimbleOne/Kantata Config Records

| Config Object API Name | Config Record Key | Change Summary | Related AC |
| --- | --- | --- | --- |
| `<CONFIG_OBJECT_API_NAME>` | `<CONFIG_RECORD_EXTERNAL_KEY>` | `<CHANGE_SUMMARY>` | `<AC_IDS>` |

## Required Fields and UI Changes

| Object API Name | Field API Name | UI Surface | Visibility | Permission Impact | QA Validation | Related AC |
| --- | --- | --- | --- | --- | --- | --- |
| `<OBJECT_API_NAME>` | `<FIELD_API_NAME>` | `<FLEXIPAGE_OR_LAYOUT_NAME>` | `<VISIBILITY_RULE>` | `<PERMISSION_SET_OR_FLS>` | `<VALIDATION>` | `<AC_IDS>` |

## Security / Sharing / Permissions Impact

- Sharing model considerations: `<SHARING_NOTES>`
- CRUD/FLS considerations: `<CRUD_FLS_NOTES>`
- Permission Set impact: `<PERMISSION_SET_NOTES>`
- Data access risks: `<RISKS>`

## Data Considerations

- Data creation or migration needed: `<YES_NO_AND_DETAILS>`
- Transactional data impact: `<IMPACT>`
- Record ID handling: Do not hardcode Salesforce record IDs.
- Data cleanup or backfill: `<DETAILS>`

## Deployment Sequence with DevOps Center

1. `<METADATA_PROMOTION_STEP>`
2. `<VALIDATION_STEP>`
3. `<POST_DEPLOYMENT_CHECK>`

## Config Record Promotion Considerations

- Config promotion required: `<YES_NO>`
- Config pack name: `<CONFIG_PACK_NAME>`
- Source org: `<SOURCE_ORG>`
- Target environments: `<TARGET_ENVIRONMENTS>`
- Rollback consideration: `<ROLLBACK_NOTES>`

## Test Strategy

- Unit tests: `<UNIT_TEST_NOTES>`
- Flow tests: `<FLOW_TEST_NOTES>`
- Integration/regression tests: `<REGRESSION_NOTES>`
- Manual QA tests: `<MANUAL_QA_NOTES>`

## QA How-to-Test Notes

- Primary user role: `<USER_OR_PROFILE>`
- Required setup: `<SETUP_NOTES>`
- Evidence to capture: `<EVIDENCE>`

## Risks

| Risk | Impact | Mitigation | Related AC |
| --- | --- | --- | --- |
| `<RISK>` | `<IMPACT>` | `<MITIGATION>` | `<AC_IDS>` |

## Assumptions

- `<ASSUMPTION>`

## Open Questions

| Question | Owner | Blocking? |
| --- | --- | --- |
| `<QUESTION>` | `<OWNER>` | `<YES_NO>` |

## Decision Log

| Date | Decision | Reason | Owner |
| --- | --- | --- | --- |
| `<YYYY-MM-DD>` | `<DECISION>` | `<REASON>` | `<OWNER>` |
