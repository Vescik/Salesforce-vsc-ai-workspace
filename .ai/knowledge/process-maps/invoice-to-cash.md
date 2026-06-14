---
title: "Invoice to Cash Process Map"
domain: "billing"
source_type: "internal_knowledge"
owner: "Salesforce Platform Team"
status: "reviewed"
confidence: "medium"
last_reviewed: "2026-05-15"
applies_to:
  - "KimbleOne/Kantata"
related_objects:
  - "kmbi__Invoice__c"
  - "kmbi__BillingSchedule__c"
related_processes:
  - "Billing Run"
  - "Invoice Approval Process"
keywords:
  - "invoice"
  - "cash"
  - "process"
  - "finance"
  - "netsuite"
---

# Summary

End-to-end flow from project billing schedule through invoice approval, customer dispatch, and payment recording.

# Process Map

```
[Project Setup]
    |
    ↓
[Billing Schedule Created] (kmbi__BillingSchedule__c)
    |
    ↓
[Billing Run] (manual or scheduled)
    |
    ↓
[Invoice Generated] (kmbi__Invoice__c, status=Draft)
    |
    ↓
[Invoice Review by PM]
    |
    ↓
[Submit for Approval] (status=Pending Approval)
    |
    ↓
[Stage 1: PM Approval]
    |
    ├── Reject → status=Draft (return to PM)
    |
    ↓
[Stage 2: Finance Controller Approval]
    |
    ├── Reject → status=Rejected (locked)
    |
    ↓
[Invoice Approved] (status=Approved)
    |
    ├──→ [Nightly Export to NetSuite] (batch job)
    |
    ↓
[Invoice Dispatched to Customer] (status=Dispatched, PDF emailed)
    |
    ↓
[Payment Received] (recorded in NetSuite, not in Salesforce)
    |
    ↓
[Invoice Closed in NetSuite]
```

# Handoff Points

| Step | System | Owner |
|---|---|---|
| Billing Schedule → Invoice | Salesforce / KimbleOne | Project Manager |
| Invoice Approval | Salesforce Approval Process | PM + Finance Controller |
| Invoice Export | Salesforce → NetSuite batch | Platform / Finance Ops |
| Dispatch | Salesforce Flow | Automated |
| Payment | NetSuite | Finance Team |

# Known Gaps

- Payment status is not visible in Salesforce — must be checked in NetSuite.
- Credit notes follow a parallel but separate process (not fully mapped here).

# Open Questions

- Is there a reconciliation report that matches Salesforce dispatched invoices with NetSuite paid invoices?

# Source Notes

- Finance team process walkthrough and Salesforce automation review, 2025-Q4.
