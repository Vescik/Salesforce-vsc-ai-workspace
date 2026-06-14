---
title: "Billing Schedule Rules"
domain: "billing"
source_type: "internal_knowledge"
owner: "Salesforce Platform Team"
status: "reviewed"
confidence: "medium"
last_reviewed: "2026-04-15"
applies_to:
  - "KimbleOne/Kantata"
related_objects:
  - "kmbi__BillingSchedule__c"
  - "kmbi__BillingScheduleLine__c"
  - "kmbi__Project__c"
related_config_objects:
  - "Billing Run configuration"
related_processes:
  - "Billing Run"
keywords:
  - "billing schedule"
  - "billing run"
  - "milestone"
  - "T&M"
---

# Summary

Billing schedules define how a project is invoiced. Two primary types are used: Time & Materials (T&M) and Fixed Milestone. The rules governing each type differ significantly.

# Details

## Time & Materials (T&M)

- `kmbi__BillingSchedule__c.kmbi__BillingType__c = Time and Materials`
- Lines are generated automatically from approved time entries via billing run.
- Billing date defaults to the last day of the billing period.
- Rate cards (`kmbi__RateCard__c`) must be associated with the project resource assignment.

## Fixed Milestone

- `kmbi__BillingSchedule__c.kmbi__BillingType__c = Fixed Price`
- Lines are created manually by the Project Manager.
- Each line has an explicit `kmbi__BillingDate__c` and `kmbi__Amount__c`.
- Lines must be set to `Ready to Bill` before a billing run will pick them up.

# Known Package Behavior

- A billing schedule cannot be deleted if any of its lines have status `Billed`.
- Changing the billing type after lines exist is blocked by a validation rule in the managed package.
- Partial billing is supported by setting `kmbi__PercentageToInvoice__c` on a line.

# Related Salesforce Objects

- `kmbi__BillingSchedule__c`
- `kmbi__BillingScheduleLine__c`
- `kmbi__Project__c` (parent)
- `kmbi__RateCard__c` (for T&M)

# Edge Cases

- If a project spans multiple currencies, the billing schedule currency must match the project currency. Cross-currency billing is not supported in the standard package.
- Zero-value lines are allowed but will generate a £0 invoice — finance team prefers these to be deleted before billing run.

# Open Questions

- Can billing schedule type be changed via data loader for migration purposes? Needs testing in sandbox.

# Source Notes

- KimbleOne package documentation (v2024.1) and internal billing team guidance.
