---
title: "KimbleOne Package Upgrade Notes"
domain: "general"
source_type: "internal_knowledge"
owner: "Salesforce Platform Team"
status: "draft"
confidence: "medium"
last_reviewed: "2026-03-10"
applies_to:
  - "KimbleOne/Kantata"
related_objects: []
related_config_objects: []
related_processes:
  - "Package Upgrade"
  - "Release Management"
keywords:
  - "package upgrade"
  - "managed package"
  - "kimbleone"
  - "kantata"
---

# Summary

KimbleOne (now Kantata) releases managed package upgrades periodically. Upgrades must be tested in sandbox before production. Post-upgrade steps are required for Flows and Permission Sets.

# Details

**Typical upgrade process:**
1. Kantata releases upgrade in AppExchange.
2. Upgrade installed in IntDev first.
3. QA smoke test against key billing, resource, and time entry flows.
4. Upgrade promoted to UAT for business acceptance.
5. Production upgrade scheduled during low-traffic window.

**Known post-upgrade steps:**
- Re-activate any Flows that the upgrade deactivated (check for `Status = Inactive` after upgrade).
- Review and re-apply any overridden picklist values that the upgrade may have reset.
- Check `kmbi__BillingSchedule__c` field changes — new fields sometimes appear with default values that affect existing records.

# Known Package Behavior

- The managed package enforces strict field-level security on `kmbi__` fields — custom permission sets may lose access after upgrades if the upgrade changes FLS defaults.
- Upgrades are non-destructive to existing data but may add required fields with defaults.

# Edge Cases

- If a package upgrade fails mid-install, Salesforce may leave the org in a partial upgrade state. Contact Kantata support immediately in this case.
- Some upgrades require the org to have specific Salesforce platform features enabled (e.g., Enhanced Lightning Experience, specific API version). Check release notes.

# Open Questions

- What is the current installed package version in Production? (Check: Setup > Installed Packages)
- Is there a Kantata release calendar shared with the team?

# Source Notes

- Kantata/KimbleOne release notes archive and internal upgrade runbooks, 2024-2025.
