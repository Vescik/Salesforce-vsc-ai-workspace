---
title: "Billing Domain"
domain: "billing"
owner: "Salesforce Platform Team"
status: "reviewed"
confidence: "high"
last_reviewed: "2026-06-01"
---

# Domain Purpose

The Billing domain covers invoice generation, billing schedule execution, credit notes, and revenue recognition within the KimbleOne managed package.

# Business Process Overview

1. Projects are set up with Billing Schedules (`kmbi__BillingSchedule__c`) that define when and how much to invoice.
2. Billing runs (manual or scheduled) generate Invoice records (`kmbi__Invoice__c`).
3. Invoices go through an approval process before being sent to the customer.
4. Approved invoices feed into revenue recognition and external finance systems via integration.

# Related Package Areas

- Billing Schedules
- Invoice Approval
- Revenue Recognition
- Credit Notes

# Related Salesforce Objects

- `kmbi__Invoice__c`
- `kmbi__InvoiceLine__c`
- `kmbi__BillingSchedule__c`
- `kmbi__BillingScheduleLine__c`
- `kmbi__CreditNote__c`

# Related Config Objects

- Billing Run configuration records
- Approval process setup in Salesforce native approvals

# Known Rules

- An invoice cannot be approved if its parent project is not in `Active` status.
- Credit notes must reference the original invoice via `kmbi__OriginalInvoice__c`.
- Billing schedule lines with `kmbi__Status__c = Billed` cannot be re-billed.

# Known Exceptions

- Manual invoice adjustments are allowed by finance admins through a custom permission set.
- One-time invoices can be created without a billing schedule for ad-hoc charges.

# Troubleshooting Notes

- If a billing run produces no invoices, check that billing schedule lines have `kmbi__BillingDate__c` within the run date range.
- Duplicate invoices are prevented by a before-insert trigger on `kmbi__Invoice__c` — check trigger bypass flags if testing.

# Open Questions

- Is revenue recognition automated via the managed package or via a custom integration?

# Source Documents

- Internal billing process runbook (Finance team, 2025-Q3)
