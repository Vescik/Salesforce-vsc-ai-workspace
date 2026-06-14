---
title: "Resource Request Workflow"
domain: "resource-management"
source_type: "internal_knowledge"
owner: "Salesforce Platform Team"
status: "reviewed"
confidence: "high"
last_reviewed: "2026-05-10"
applies_to:
  - "KimbleOne/Kantata"
related_objects:
  - "kmbi__ResourceRequest__c"
  - "kmbi__ResourceBooking__c"
  - "kmbi__Resource__c"
related_config_objects:
  - "Flow: Resource_Request_Approval_Flow"
related_processes:
  - "Resource Booking Lifecycle"
keywords:
  - "resource request"
  - "booking"
  - "approval"
  - "PMO"
---

# Summary

Resource requests move through a status-driven workflow from `Draft` to `Fulfilled`. A Salesforce Flow (`Resource_Request_Approval_Flow`) handles notifications and status transitions.

# Details

**Status Lifecycle:**
```
Draft → Submitted → Approved → In Progress → Fulfilled
                 ↓ Reject
               Rejected
```

- `Draft`: Created by PM, not yet visible to Resource Management team.
- `Submitted`: PM submits request; Resource Manager receives email notification via Flow.
- `Approved`: Resource Manager approves the request and begins sourcing.
- `In Progress`: At least one booking has been created against the request.
- `Fulfilled`: All required hours/days have been booked.
- `Rejected`: Resource Manager rejects with reason; PM notified.

# Known Package Behavior

- `kmbi__ResourceRequest__c.kmbi__Status__c` picklist is managed — values cannot be added without package customisation.
- The managed package enforces that `kmbi__StartDate__c` < `kmbi__EndDate__c` with a validation rule.
- When a booking is created, the managed package automatically updates the request status to `In Progress`.

# Related Salesforce Objects

- `kmbi__ResourceRequest__c`
- `kmbi__ResourceBooking__c`

# Related Config Records

- Flow: `Resource_Request_Approval_Flow` (active)
- Custom Setting: `Resource_Management_Settings__c` (controls notification emails)

# Edge Cases

- If a Resource Manager is on leave, requests pile up with no auto-escalation — the PMO has a weekly triage meeting as a manual workaround.
- Emergency resource requests can skip `Submitted` status via a custom button available to PMO admins only.

# Open Questions

- Is there an SLA tracking mechanism for how long requests sit in `Submitted` state?

# Source Notes

- PMO process documentation and Salesforce Flow inspection, 2025-Q4.
