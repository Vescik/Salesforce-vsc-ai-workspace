---
title: "Resource Management Domain"
domain: "resource-management"
owner: "Salesforce Platform Team"
status: "reviewed"
confidence: "high"
last_reviewed: "2026-05-10"
---

# Domain Purpose

Resource Management covers the process of requesting, booking, and tracking people (resources) against projects in KimbleOne.

# Business Process Overview

1. Project Managers raise Resource Requests (`kmbi__ResourceRequest__c`) specifying role, skill, and date range.
2. Resource Managers review open requests and assign resources (`kmbi__Resource__c`) via bookings.
3. Bookings (`kmbi__ResourceBooking__c`) track the allocation of a resource to a project phase.
4. Utilisation reports aggregate bookings to show capacity vs demand.

# Related Package Areas

- Resource Requests
- Resource Bookings
- Skills and Roles
- Utilisation Reporting

# Related Salesforce Objects

- `kmbi__Resource__c`
- `kmbi__ResourceRequest__c`
- `kmbi__ResourceBooking__c`
- `kmbi__Skill__c`
- `kmbi__Role__c`

# Known Rules

- A resource must have an active `kmbi__Resource__c` record linked to their Salesforce User before they can be booked.
- Overlapping bookings for the same resource on the same dates are prevented by a managed package validation.
- Resource requests must be approved before a booking can be created against them.

# Open Questions

- Is the resource request approval process automated (Flow) or manual?

# Source Documents

- Internal resource management process guide (PMO team, 2025)
