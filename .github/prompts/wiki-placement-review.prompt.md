---
description: Review whether an Azure Wiki page placement decision is correct.
mode: ask
---

# Wiki Placement Review

Review the Azure Wiki placement report and decide whether the selected section/path is appropriate.

## Check

- Existing wiki sections were inspected.
- Existing object/functionality/process pages were considered.
- Module match is justified by source artifacts and wiki structure.
- Fallback to `_Proposed` or `_Unclassified` is justified if no section exists.
- Page title is clear.
- Source artifacts are referenced.
- Duplicate page risk is addressed.
- Existing pages are not overwritten without review.

## Output

Return one of:

- `APPROVED`
- `APPROVED_WITH_COMMENTS`
- `BLOCKED`

Include concise findings and required changes.
