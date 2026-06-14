---
title: "Resource Booking Lifecycle"
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
related_processes:
  - "Resource Request Workflow"
keywords:
  - "resource"
  - "booking"
  - "lifecycle"
  - "PMO"
---

# Summary

End-to-end lifecycle from project staffing need identification through resource booking creation, utilisation tracking, and booking closure.

# Process Map

```
[Project Kick-off]
    |
    ↓
[PM Identifies Staffing Need]
    |
    ↓
[Resource Request Created] (kmbi__ResourceRequest__c, status=Draft)
    |
    ↓
[PM Submits Request] (status=Submitted)
    |
    ↓
[Resource Manager Reviews]
    |
    ├── Reject → status=Rejected (PM notified)
    |
    ↓
[Resource Manager Approves] (status=Approved)
    |
    ↓
[Resource Manager Identifies Candidate]
    |
    ↓
[Resource Booking Created] (kmbi__ResourceBooking__c)
    |   Request status auto-updates → In Progress
    |
    ↓
[Resource Assigned to Project Phase]
    |
    ↓
[Resource Logs Time] (kmbi__TimeEntry__c)
    |
    ↓
[Booking End Date Reached]
    |
    ↓
[Resource Manager Closes Booking] (status=Completed)
    |
    ↓
[Request Fulfilled] (status=Fulfilled, if all hours booked)
```

# Handoff Points

| Step | Owner |
|---|---|
| Create request | Project Manager |
| Approve/reject request | Resource Manager |
| Create booking | Resource Manager |
| Log time | Resource (employee) |
| Close booking | Resource Manager |

# Known Gaps

- No automatic notification when a booking end date is approaching — Resource Manager must monitor manually.
- If a resource leaves mid-project, the booking must be manually closed and a new resource request raised.

# Open Questions

- Is there a capacity planning dashboard visible to Resource Managers showing open requests vs available resources?

# Source Notes

- PMO team process documentation, 2025-Q4.
