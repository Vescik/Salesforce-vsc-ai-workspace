---
title: "kmbi__TimeEntry__c — Object Notes"
domain: "time-expense"
source_type: "internal_knowledge"
owner: "Salesforce Platform Team"
status: "reviewed"
confidence: "high"
last_reviewed: "2026-05-28"
applies_to:
  - "KimbleOne/Kantata"
related_objects:
  - "kmbi__TimeEntry__c"
  - "kmbi__Timesheet__c"
  - "kmbi__ProjectPhase__c"
related_config_objects:
  - "Approval Process: Timesheet_Approval"
related_processes:
  - "Timesheet Submission"
  - "Billing Run"
keywords:
  - "time entry"
  - "timesheet"
  - "kmbi__TimeEntry__c"
  - "hours"
---

# Summary

`kmbi__TimeEntry__c` stores a single row of logged time — one resource, one day, one project phase. It is the atomic unit of time tracking in KimbleOne.

# Key Fields

| Field | Type | Notes |
|---|---|---|
| `kmbi__Timesheet__c` | Master-Detail | Parent timesheet |
| `kmbi__ProjectPhase__c` | Lookup | Project phase being worked on |
| `kmbi__Date__c` | Date | Date of the work |
| `kmbi__Hours__c` | Number | Hours logged (decimal, max 24) |
| `kmbi__Notes__c` | Text Area | Optional description of work |
| `kmbi__BillingStatus__c` | Picklist | Unbilled / Billed / Non-Billable |
| `kmbi__Resource__c` | Lookup | Resource who logged the time |

# Known Package Behavior

- Time entries are locked when the parent timesheet status is `Approved`. Edits require `KimbleOne Admin` permission set.
- `kmbi__BillingStatus__c` is set to `Billed` automatically by the billing run when the entry is included in an invoice.
- The package validates that `kmbi__Hours__c` is between 0 and 24.
- Entries with `kmbi__BillingStatus__c = Non-Billable` are excluded from T&M billing runs.

# Triggers & Automations

- **Before Insert/Update**: Validates phase status is `Active`; prevents logging against completed phases.
- **After Update**: Rolls up total hours to parent timesheet.

# Integration Points

- Approved time entries are read by the T&M billing run to generate `kmbi__InvoiceLine__c` records.
- Utilisation reports aggregate `kmbi__Hours__c` across resources for capacity planning.

# Edge Cases

- A resource can log time on a day that falls outside the project phase date range — the package does not enforce date boundary validation (only status check).
- Entries created via data loader bypass the `Active` phase check — use with caution in migrations.

# Open Questions

- Is there a maximum number of time entries per timesheet enforced by the package?

# Review History

- 2026-05-28: Confirmed against IntDev org schema by Platform Team.
