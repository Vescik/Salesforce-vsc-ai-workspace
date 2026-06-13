---
description: Human-review checklist for pushing an Azure Wiki draft branch.
mode: ask
---

# Review Wiki Publication

Review the generated Azure Wiki publication report and page preview before any branch push.

## Check

- Content is accurate and traceable to source artifacts.
- Placement is correct for the existing wiki structure.
- No secrets, credentials, raw data dumps, or unsupported claims are present.
- No unreviewed AI-only statements are treated as authoritative.
- Existing page updates include diff evidence and review notes.
- The target branch is a feature branch, not the default branch.
- PR creation, review, merge, and final publication remain manual Azure DevOps steps.

## Output

Return one of:

- `APPROVED_FOR_BRANCH_PUSH`
- `APPROVED_WITH_CHANGES`
- `BLOCKED`

Include the approval note that should be passed to `--approval-note` if branch push is approved.
