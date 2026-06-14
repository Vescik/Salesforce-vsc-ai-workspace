---
title: "kmbi__Resource__c — Object Notes"
domain: "resource-management"
source_type: "internal_knowledge"
owner: "Salesforce Platform Team"
status: "reviewed"
confidence: "medium"
last_reviewed: "2026-04-20"
applies_to:
  - "KimbleOne/Kantata"
related_objects:
  - "kmbi__Resource__c"
  - "kmbi__ResourceBooking__c"
  - "kmbi__ResourceRequest__c"
  - "User"
related_config_objects: []
related_processes:
  - "Resource Booking Lifecycle"
keywords:
  - "resource"
  - "kmbi__Resource__c"
  - "booking"
  - "user"
---

# Summary

`kmbi__Resource__c` represents a bookable person (usually a Salesforce User) in KimbleOne. Every employee who logs time or is booked on projects must have an active resource record.

# Key Fields

| Field | Type | Notes |
|---|---|---|
| `kmbi__User__c` | Lookup (User) | Linked Salesforce User — must be unique |
| `kmbi__ResourceType__c` | Picklist | Employee / Contractor / External |
| `kmbi__IsActive__c` | Checkbox | Inactive resources cannot be booked |
| `kmbi__DefaultRole__c` | Lookup | Default role for bookings |
| `kmbi__Capacity__c` | Number | Standard weekly hours capacity (default: 40) |
| `kmbi__CostRate__c` | Currency | Internal cost rate per hour |

# Known Package Behavior

- One `kmbi__Resource__c` per Salesforce User is enforced by a unique validation rule.
- Deactivating a resource (`kmbi__IsActive__c = false`) does not delete existing bookings or time entries.
- The package links `kmbi__Resource__c` to `User` via `kmbi__User__c` — if the User is deactivated in Salesforce, the resource record is NOT automatically deactivated.

# Onboarding / Offboarding Notes

- **New employee**: Create `kmbi__Resource__c`, link to User, set role and capacity. Assign `KimbleOne_User` permission set.
- **Leaver**: Set `kmbi__IsActive__c = false`. Do not delete — historical time entries and bookings depend on the record.

# Edge Cases

- Contractors can be resources without a Salesforce User licence if they use a Community/Experience Cloud licence — confirm with licence admin.
- `kmbi__CostRate__c` is visible to users with `Finance_Read` permission — ensure contractors' rates are not visible to project managers by reviewing FLS.

# Open Questions

- Is `kmbi__CostRate__c` populated for all resources, or only for billing calculations?
- Is there a process to auto-deactivate resources when their User record is deactivated?

# Review History

- 2026-04-20: Reviewed against IntDev org by Platform Team. `kmbi__CostRate__c` FLS question raised and open.
