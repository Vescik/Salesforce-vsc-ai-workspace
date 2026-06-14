---
name: estimate-complexity
description: Estimate the size and risk of a Salesforce/KimbleOne Work Item before solution design begins.
agent: work-item-context-curator
mode: ask
argument-hint: <WORK_ITEM_ID>
---

# Estimate Work Item Complexity

Estimate the delivery complexity and risk of Work Item `<WORK_ITEM_ID>` before solution design begins.

## Scope

Do not design a solution. Do not write implementation code. Do not modify Salesforce metadata. Do not call Salesforce CLI, ADO, MCP servers, or external model APIs.

All estimates are advisory drafts for human sprint planning. Mark every estimate and risk rating as unconfirmed until a human reviewer validates it.

Do not fetch Azure DevOps directly in this prompt. Use the normalized local Work Item artifacts created by `/fetch-us <WORK_ITEM_ID>`.

## Source Artifacts To Read

Read these artifacts when present:

- `.ai/context/work-items/<WORK_ITEM_ID>/work-item-summary.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/acceptance-criteria.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/context-pack.md`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-metadata.yaml`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-schema.yaml`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-knowledge.yaml`
- `.ai/context/work-items/<WORK_ITEM_ID>/relevant-config-records.yaml`

If `work-item-summary.md` or `acceptance-criteria.md` is missing, stop and instruct the user to run `/fetch-us <WORK_ITEM_ID>` first.

For missing optional artifacts, note the gap and flag it as a sizing risk.

## Size Categories

Use this rubric to determine the size category:

| Size | Acceptance Criteria | Metadata Components | Config Impact | Unknowns |
| --- | --- | --- | --- | --- |
| XS | 1–2 | 0–2 | None likely | Minimal |
| S | 3–4 | 3–5 | Possible, minor | Low |
| M | 5–7 | 6–10 | Likely | Some |
| L | 8–12 | 11–20 | Definite | Significant |
| XL | 13+ or unclear | 20+ | Complex or unknown | High — may need a spike |

When in doubt, size up rather than down. Mark the basis for the size rating explicitly.

## Risk Factors

Assess each of these and rate as LOW / MEDIUM / HIGH:

- **Closed managed package constraints**: does the Work Item touch KimbleOne/Kantata behavior that cannot be examined in source?
- **Config record impact**: are configuration records likely to need a sidecar process separate from metadata promotion?
- **Cross-object relationship complexity**: does the Work Item span multiple objects, lookups, or rollup fields?
- **Permission and security changes**: does the Work Item affect Permission Sets, Profiles, Sharing Rules, or field-level security?
- **Data volume considerations**: could new Flows or triggers encounter governor limits at scale?
- **Rollback complexity**: if this Work Item is reverted after production promotion, is the rollback straightforward?
- **Dependency on other Work Items**: does this depend on unreleased metadata or config from another Work Item?
- **Knowledge gap**: is the relevant domain poorly documented in the knowledge base or solution context?

## Recommended Approach

Based on the size and risk assessment, recommend one of:

- `PROCEED_TO_DESIGN` — requirements and context are sufficient to start `/solution-design`.
- `SPIKE_FIRST` — one or more unknowns must be resolved before a reliable design is possible; describe the spike objective.
- `NEEDS_CLARIFICATION` — acceptance criteria or scope is ambiguous; list the specific questions to resolve with the product owner.

## Output Sections

Return these sections:

1. **Complexity Summary**: one paragraph with the size category, overall risk level, and the primary sizing driver.
2. **Size Category**: XS / S / M / L / XL with the basis for the rating.
3. **Risk Factor Assessment**: table with each risk factor, its rating (LOW / MEDIUM / HIGH), and one-line rationale.
4. **Unknowns Blocking Design**: numbered list of specific unknowns that must be resolved before `/solution-design` can produce a reliable result.
5. **Recommended Approach**: `PROCEED_TO_DESIGN`, `SPIKE_FIRST`, or `NEEDS_CLARIFICATION` with rationale.
6. **Sprint Guidance**: relative effort indication only — not a commitment (e.g., "likely 1–3 developer days" or "likely multi-sprint"). Mark as advisory and unconfirmed.
7. **Sizing Assumptions**: list every assumption made in the absence of confirmed facts.

## Estimation Rules

- Base all estimates on Work Item artifacts and workspace indexes only; do not invent facts.
- Cite the specific acceptance criteria, metadata component, or knowledge note that drives each sizing decision.
- Do not assume KimbleOne/Kantata managed package behavior beyond what knowledge notes document.
- Mark every size category and risk rating as an advisory estimate requiring human validation.
- If context pack or schema cards are missing, note that the estimate is limited and flag this as a sizing risk.
