# DevOps Center Work Item Runbook

## Purpose

Use this runbook to align Copilot-assisted Salesforce work with the DevOps Center Work Item flow. The AI workspace supports planning, review, documentation, and readiness checks; it does not replace DevOps Center.

DevOps Center remains the official Salesforce metadata promotion mechanism. IntDev is a Full Copy developer/discovery org without Git and is not the source of truth.

## Work Item Branches

Work Item branches are created and managed through DevOps Center. Do not invent branch names in prompts, docs, or tooling. Use placeholders such as `<DEVOPS_CENTER_WORK_ITEM_BRANCH>`, `<UAT_BRANCH>`, `<STAGE_BRANCH>`, and `<PROD_BRANCH>` until the team provides the actual DevOps Center mapping.

The repository and DevOps Center branch state are the authoritative basis for metadata promotion. IntDev may be used for discovery and curated context indexing, but it is not deployment authority.

## AI Workspace Role

The AI workspace may help with:

- Context building from local repository metadata, schema indexes, and curated anonymized config indexes.
- Solution design support tied to Work Item acceptance criteria.
- Solution design review and implementation work packet planning.
- Git diff and scope review.
- Local precheck evidence before commit, PR, or promote.
- Technical documentation drafts.
- QA how-to-test drafts.
- KimbleOne/Kantata config impact analysis.

## AI Workspace Must Not

- Deploy metadata to Salesforce orgs.
- Replace DevOps Center as the metadata promotion path.
- Apply production config records.
- Claim deployment or promotion success.
- Assume KimbleOne/Kantata managed package internals or source code.
- Treat config record promotion as Salesforce metadata promotion.
- Use external LLM APIs or autonomous deployment agents.

Config record promotion is a separate sidecar process and is currently analysis/skeleton only. Production config apply is not implemented and requires future controlled tooling/manual approval.

## High-Level Flow

1. Create or open the Work Item in DevOps Center.
2. Create or checkout the Work Item branch created by DevOps Center.
3. Build local AI workspace context from repository metadata, schema, and curated config indexes.
4. Create a solution design tied to Work Item acceptance criteria.
5. Retrieve, compare, and implement changes using the existing team process.
6. Run local precheck and review warnings.
7. Commit changes to the DevOps Center-managed Work Item branch.
8. Run PR and validation gates configured by the team.
9. Promote metadata through DevOps Center.
10. Handle config sidecar review if KimbleOne/Kantata configuration records are required.
