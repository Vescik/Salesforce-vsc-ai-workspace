---
title: "Timesheet Approval Flow"
domain: "time-expense"
source_type: "internal_knowledge"
owner: "Salesforce Platform Team"
status: "reviewed"
confidence: "high"
last_reviewed: "2026-05-28"
applies_to:
  - "KimbleOne/Kantata"
related_objects:
  - "kmbi__Timesheet__c"
  - "kmbi__TimeEntry__c"
related_config_objects:
  - "Salesforce Approval Process: Timesheet_Approval"
related_processes:
  - "Timesheet Submission"
  - "Billing Run"
keywords:
  - "timesheet"
  - "approval"
  - "time entry"
  - "weekly"
---

# Summary

Employees submit weekly timesheets via the KimbleOne timesheet UI. Timesheets enter a single-stage approval process where the Project Manager approves or rejects. Approved timesheets feed T&M billing.

# Details

**Timesheet period:** Monday to Sunday. Timesheets are auto-created by a scheduled batch job every Monday morning for all active resources.

**Status Lifecycle:**
```
Open → Submitted → Approved
              ↓ Reject
            Returned
```

- `Open`: Editable by resource.
- `Submitted`: Locked for editing; PM receives notification.
- `Approved`: Locked; time entries available for billing run.
- `Returned`: PM has returned for correction; editable again by resource.

# Known Package Behavior

- The managed package creates one `kmbi__Timesheet__c` per resource per week automatically via batch.
- If a resource is added to a project mid-week, they may need a manual timesheet creation for that week.
- Deleting time entries on an `Approved` timesheet requires the `KimbleOne Admin` permission set.

# Related Salesforce Objects

- `kmbi__Timesheet__c`
- `kmbi__TimeEntry__c`

# Related Config Records

- Approval Process: `Timesheet_Approval`
- Scheduled Job: `KimbleOne Timesheet Generation` (runs Mondays 06:00 UTC)

# Examples

A resource logs 8 hours on Monday against `Project Alpha / Phase 1`, and 4 hours on Tuesday. They submit the timesheet on Friday. The PM reviews and approves on Monday. The time entries are then available in the next T&M billing run.

# Edge Cases

- Public holidays: The timesheet is still created; employees log 0 hours for holiday days.
- If a PM is on leave, the timesheet sits in `Submitted` until the PM returns or delegates approval.
- Timesheets with 0 total hours can be submitted and approved (valid for holiday weeks).

# Open Questions

- Is there an auto-approval rule for timesheets that have been in `Submitted` for more than 5 business days?

# Source Notes

- HR policy documentation and Salesforce Approval Process inspection, 2025.
