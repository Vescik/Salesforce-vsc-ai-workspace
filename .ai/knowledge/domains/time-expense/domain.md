---
title: "Time & Expense Domain"
domain: "time-expense"
owner: "Salesforce Platform Team"
status: "reviewed"
confidence: "high"
last_reviewed: "2026-06-01"
---

# Domain Purpose

Time & Expense covers how employees log time against projects and submit expense claims for reimbursement or billing through KimbleOne.

# Business Process Overview

1. Employees log time entries (`kmbi__TimeEntry__c`) against project phases weekly.
2. Timesheets are submitted for approval by the project manager.
3. Approved time entries feed into T&M billing schedules and utilisation reporting.
4. Expenses (`kmbi__Expense__c`) are submitted with receipts, approved by PM, and either recharged to client or processed for employee reimbursement.

# Related Package Areas

- Timesheets
- Time Entry Approval
- Expense Claims
- Expense Reimbursement

# Related Salesforce Objects

- `kmbi__TimeEntry__c`
- `kmbi__Timesheet__c`
- `kmbi__Expense__c`
- `kmbi__ExpenseCategory__c`

# Known Rules

- Time entries can only be logged against project phases in `Active` status.
- Once a timesheet is `Approved`, its time entries are locked and cannot be edited.
- Expenses require a receipt attachment (enforced by validation rule) unless the category is marked as `Receipt Not Required`.

# Open Questions

- Is there integration between KimbleOne expenses and the HR/payroll system for reimbursement?

# Source Documents

- Internal time & expense policy, HR team 2025
