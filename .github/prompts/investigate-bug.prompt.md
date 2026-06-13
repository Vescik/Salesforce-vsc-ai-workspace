---
name: investigate-bug
description: Structured root-cause investigation for a Salesforce/KimbleOne defect Work Item.
agent: bug-investigator
argument-hint: <WORK_ITEM_ID>
---

# Investigate Bug

Conduct a root-cause investigation for defect Work Item `<WORK_ITEM_ID>`.

## Scope

Do not design a fix. Do not modify Salesforce metadata. Do not call Salesforce CLI, ADO, deployment tools, MCP servers, or external model APIs. Do not invent behavior not evidenced in workspace artifacts.

Generated investigation output is a draft requiring human validation before a solution design starts.

Do not fetch Azure DevOps directly in this prompt. Use the normalized local Work Item artifacts created by `/fetch-us <WORK_ITEM_ID>`.

## Source Artifacts To Read

Read these artifacts when present:

- `.ai/context/work-items/<WORK_ITEM_ID>/work-item-summary.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/acceptance-criteria.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/context-pack.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-metadata.yaml`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-schema.yaml`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-config-records.yaml`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-knowledge.yaml`
- `.ai/outputs/precheck/<WORK_ITEM_ID>.precheck.md`
- Current Git diff and recent commit history for context on recent changes.

If `work-item-summary.md` is missing, stop and instruct the user to run `/fetch-us <WORK_ITEM_ID>` first.

For missing optional artifacts, note what is absent and mark resulting assumptions as unconfirmed.

## Required Human Input

Before starting the investigation, ask the user for:

1. **Error message or symptom**: exact error text, unexpected behavior, or screenshot description.
2. **Reproduction steps**: how to trigger the issue consistently, or whether it is intermittent.
3. **Affected environment**: which org or sandbox (IntDev, UAT, Stage, Prod), which profile or user type, and which records or configuration state.
4. **When it started**: was this working before a recent change? If yes, what changed?

If the user has already provided this in the Work Item or conversation, do not ask again. Proceed with what is available.

## Output

Create:

- `.ai/outputs/bug-investigation/<WORK_ITEM_ID>.investigation.md`

If file writing is not permitted in the current phase, return the investigation inline and ask the user if they want to save it.

## Required Sections

1. Investigation Summary
2. Symptom
3. Affected Workspace Artifacts
4. Hypotheses (ranked by confidence, with evidence for/against and required additional information per hypothesis)
5. Required Additional Information (consolidated)
6. Recommended Next Step (`PROCEED_TO_DESIGN` / `NEED_MORE_EVIDENCE` / `ESCALATE`)
7. Open Questions

## Investigation Rules

- Cite the specific file path, component name, or knowledge note for every evidence claim.
- Rank hypotheses by confidence; do not commit to a single root cause until evidence supports it.
- If the knowledge base contradicts schema or metadata, flag for human validation.
- Do not assume KimbleOne/Kantata managed package internals beyond what knowledge notes document.
- Use placeholders such as `<RECORD_ID>`, `<USERNAME>`, `<ORG_ALIAS>` where specific values are unknown.
