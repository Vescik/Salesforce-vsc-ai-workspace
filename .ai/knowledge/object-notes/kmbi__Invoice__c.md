---
title: "kmbi__Invoice__c — Object Notes"
domain: "billing"
source_type: "internal_knowledge"
owner: "Salesforce Platform Team"
status: "reviewed"
confidence: "high"
last_reviewed: "2026-05-20"
applies_to:
  - "KimbleOne/Kantata"
related_objects:
  - "kmbi__Invoice__c"
  - "kmbi__InvoiceLine__c"
  - "kmbi__BillingSchedule__c"
  - "kmbi__Project__c"
related_config_objects:
  - "Approval Process: Invoice_Approval"
related_processes:
  - "Billing Run"
  - "Invoice Approval Process"
keywords:
  - "invoice"
  - "kmbi__Invoice__c"
  - "billing"
---

# Summary

`kmbi__Invoice__c` is the core managed object representing a customer invoice generated from a KimbleOne billing run or created manually.

# Key Fields

| Field | Type | Notes |
|---|---|---|
| `kmbi__Status__c` | Picklist | Draft / Pending Approval / Approved / Dispatched / Cancelled |
| `kmbi__Project__c` | Lookup | Parent project |
| `kmbi__BillingSchedule__c` | Lookup | Source billing schedule (nullable for manual invoices) |
| `kmbi__InvoiceDate__c` | Date | Date printed on invoice |
| `kmbi__DueDate__c` | Date | Payment due date |
| `kmbi__TotalAmount__c` | Currency | Rolled up from invoice lines |
| `kmbi__CurrencyIsoCode` | Currency | Must match project currency |

# Known Package Behavior

- `kmbi__TotalAmount__c` is a roll-up summary field — cannot be edited directly.
- Setting `kmbi__Status__c = Cancelled` locks all child `kmbi__InvoiceLine__c` records.
- A before-insert trigger prevents duplicate invoices for the same billing schedule line.
- The package enforces that `kmbi__DueDate__c >= kmbi__InvoiceDate__c`.

# Triggers & Automations

- **Before Insert**: Duplicate prevention trigger (managed, cannot be disabled in normal configuration).
- **After Update**: Status change handler — triggers approval submission when status moves to `Pending Approval`.
- **Flow**: `Invoice_Dispatch_Flow` — sends PDF to customer email when status moves to `Dispatched`.

# Sharing & Access

- Default sharing: Private (controlled by org-wide default).
- Invoice owners and their managers can read invoices.
- `Finance_Read` permission set grants read-only access to finance team.
- `Finance_Admin` permission set grants full edit access.

# Integration Points

- Invoices are exported to the finance system (NetSuite) via a nightly scheduled batch using `kmbi__Invoice__c` status = `Approved`.
- The NetSuite integration reads `kmbi__ExternalId__c` to avoid duplicate imports.

# Edge Cases

- If the project currency differs from the user's currency, amount fields display in project currency but the user's locale formatting applies — this can cause confusion in reports.
- Cancelled invoices remain visible to all users; there is no archive/hide mechanism in the standard package.

# Open Questions

- Is there a soft-delete / archive process for old cancelled invoices?
- What is the retention policy for invoice records?

# Review History

- 2026-05-20: Reviewed by Platform Team against IntDev org schema. All fields confirmed present.
