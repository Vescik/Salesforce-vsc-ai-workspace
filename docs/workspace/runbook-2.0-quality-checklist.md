# Runbook 2.0 Quality Checklist

This checklist defines the documentation standard for workspace operator runbooks. It is based on common SRE and operations guidance: keep procedures repeatable, role-aware, current, tested, and safe to execute under time pressure.

Reference guidance:

- Google SRE incident response: https://sre.google/workbook/incident-response/
- Microsoft Azure Well-Architected Operational Excellence: https://learn.microsoft.com/en-us/azure/well-architected/operational-excellence/principles
- Atlassian incident response best practices: https://www.atlassian.com/incident-management/incident-response/best-practices
- PagerDuty runbook guidance: https://www.pagerduty.com/resources/automation/learn/what-is-a-runbook/

## Required Sections

Operator runbooks should include these sections unless the document is a pure reference:

- Purpose
- When To Use
- Inputs
- Preconditions
- Operator Steps
- Expected Outputs
- Review Gates
- Troubleshooting
- Escalation
- Safety Boundaries
- Maintenance

Reference documents such as command inventories and governance docs must still identify source-of-truth boundaries, human approval gates, and forbidden actions.

## Command Standard

- Use Windows PowerShell commands first on this branch.
- Add Mac/Linux `make` equivalents only when they materially help cross-platform operators.
- Every command that writes local artifacts must state the expected output path.
- Every command that can push to an external Git repository must state the approval gate.
- Do not document direct Salesforce deploy, Salesforce write, production data update, or configuration apply commands.

## Review Checklist

Before a runbook update is accepted, verify:

- The operator can identify when to run the procedure and when to stop.
- Inputs and local configuration prerequisites are explicit.
- Expected outputs are concrete paths or review artifacts.
- Human review gates are stated for Knowledge Base approval, Azure Wiki push, release readiness, and DevOps Center promotion.
- Troubleshooting has symptoms, checks, safe fixes, and escalation triggers.
- The runbook does not instruct users to commit secrets, raw exports, logs, Salesforce record IDs, or uncontrolled customer data.
- The runbook states that DevOps Center remains the official Salesforce metadata promotion mechanism where release flow is discussed.
- The runbook states that the workspace does not call external model APIs.

## Maintenance

- Review operator runbooks after command-surface changes.
- Re-run docs validation after every runbook update.
- Keep duplicated workflows short in the user guide; link to the authoritative runbook for exact operator steps.
- Treat stale screenshots, examples, and output paths as documentation defects.
