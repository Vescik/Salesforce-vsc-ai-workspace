# Knowledge Base Runbook

> Platform note: this branch uses the Windows PowerShell command surface. VS Code Tasks are also available from `Ctrl+Shift+P` -> `Tasks: Run Task`. Mac/Linux equivalents are listed only where they materially help cross-platform operators.

## Purpose

Use this runbook to sync, create, review, validate, index, search, and maintain internal Knowledge Base notes for the Salesforce AI Workspace.

KimbleOne/Kantata is a closed managed package. The workspace cannot inspect package internals. The Knowledge Base gives the team a controlled way to reuse reviewed observations from visible behavior, Salesforce schema, anonymized configuration records, tests, documentation, and owner validation.

## When To Use

Use this runbook when you need to:

- Sync curated notes from the private external Knowledge Base repository.
- Convert a controlled PDF, CSV, Markdown, TXT, XML, or Salesforce metadata XML file into draft KB notes.
- Review generated knowledge before it is used in solution design, code review, testing, deployment planning, troubleshooting, or documentation.
- Rebuild local knowledge indexes, semantic graph data, or Work Item context packs.
- Prepare reviewed local notes for push back to the external Knowledge Base repository.

Do not use this runbook to deploy Salesforce metadata, apply configuration records, write Salesforce data, publish raw exports, or turn draft notes into confirmed facts without review.

## Inputs

| Input | Required | Notes |
| --- | --- | --- |
| Knowledge Base repository URL or local path | For sync/push | Configure once with `.\scripts\workspace.ps1 configure` or `KB_REPO`; use `-KbRepo` only as an override. |
| Knowledge Base branch | Optional | Defaults to the configured branch or `main`. |
| Source file under `.ai/knowledge/imports/` | For create | Import staging is ignored except `.gitkeep`; review source safety first. |
| Domain | For create | Use the domain registry in `.ai/knowledge/index.yaml` where possible. |
| Title | For create | Use a clear business or technical title, not a file dump name. |
| Owner | For approval | Defaults exist, but reviewed notes need a real accountable owner. |
| Work Item ID and query | For context use | Needed when rebuilding a Work Item context pack. |

## Preconditions

1. Run commands from the repository root.
2. Confirm local setup is healthy:

```powershell
.\scripts\workspace.ps1 doctor
```

3. Confirm source files are controlled and safe:

- No secrets, tokens, private keys, PATs, OAuth credentials, logs, raw production dumps, uncontrolled exports, or Salesforce record IDs as stable keys.
- No unsupported claims about KimbleOne/Kantata internals.
- No screenshots or data extracts containing sensitive customer data unless separately approved and controlled.

4. Confirm the source-of-truth model:

- The external private Knowledge Base Git repository is the source of truth.
- `.ai/knowledge/` is the local synchronized workspace copy.
- `.ai/vendor/knowledge-base/` is the ignored local vendor clone.
- Draft notes are discovery aids, not implementation authority.

## Operator Steps

### 1. Sync Existing Knowledge

Preview the sync first:

```powershell
.\scripts\workspace.ps1 knowledge-sync-dry-run
```

Expected output:

- `.ai/outputs/knowledge-sync/knowledge-sync.md`
- `.ai/outputs/knowledge-sync/knowledge-sync.json`

Review the report. If the source repository, branch, and skipped-file list are correct, sync:

```powershell
.\scripts\workspace.ps1 knowledge-sync
```

Expected output:

- Updated `.ai/knowledge/`
- Updated `.ai/knowledge/sync-state.json`
- Updated `.ai/vendor/knowledge-base/` clone cache
- Updated sync report under `.ai/outputs/knowledge-sync/`

Mac/Linux equivalent:

```bash
make knowledge-sync KB_REPO=<repo-url-or-local-path> KB_BRANCH=main
```

If local config is not set, rerun `.\scripts\workspace.ps1 configure`, set `KB_REPO`/`KB_BRANCH`, or pass `-KbRepo "<repo-url-or-local-path>" -KbBranch main` for a one-off override.

### 2. Stage A Source File For Knowledge Base Creator 2.0

Place controlled source files under:

```text
.ai/knowledge/imports/
```

Supported source types include PDF, CSV, Markdown, TXT, XML, and Salesforce metadata XML. The creator extracts readable text and structure locally, redacts likely sensitive values, splits large sources into logical notes, and generates draft/low-confidence Markdown with source references, semantic fields, search terms, and review actions.

Before creating notes, run a dry run:

```powershell
.\scripts\workspace.ps1 knowledge-create-dry-run -KnowledgeSource ".ai/knowledge/imports/example.txt" -KnowledgeDomain "general" -KnowledgeTitle "Example Knowledge Note"
```

Expected output:

- Console preview of generated note metadata, semantic fields, warnings, and skipped content.
- No KB note files written.

### 3. Create Draft Notes

Create from one source file:

```powershell
.\scripts\workspace.ps1 knowledge-create -KnowledgeSource ".ai/knowledge/imports/example.txt" -KnowledgeDomain "general" -KnowledgeTitle "Example Knowledge Note" -KnowledgeOwner "Salesforce Platform Team"
```

Create from a manifest:

```powershell
.\scripts\workspace.ps1 knowledge-create-manifest -KnowledgeManifest ".ai/templates/knowledge-import-manifest.yaml"
```

Expected output:

- Draft note files under `.ai/knowledge/domains/<domain>/` or another configured KB location.
- Import report files under `.ai/outputs/knowledge-import/`.
- Generated notes with `status: draft` and `confidence: low`.

`knowledge-import` and `knowledge-import-manifest` remain backward-compatible aliases for existing prompts and tasks.

### 4. Review Draft Notes

Open each generated note and review:

- Title, purpose, summary, source file, source format, source checksum, owner, status, confidence, and `last_reviewed`.
- Usage context, tags, aliases, key concepts, keywords, and search terms.
- Salesforce objects, fields, metadata components, Apex classes, triggers, Flow elements, validation rules, automation logic, dependencies, integrations, and business rules where detected.
- Review notes, warnings, parse status, duplicate suppression, and low-value-content warnings.
- Any redaction warnings or possible sensitive content.

Use Copilot review support when useful:

```text
/review-knowledge-note .ai/knowledge/domains/<domain>/<note>.md
```

Keep generated notes as draft/low-confidence until the accountable owner has reviewed the content.

### 5. Validate, Index, And Build The Graph

Validate note schema, freshness, quality, secrets, and Salesforce ID rules:

```powershell
.\scripts\workspace.ps1 knowledge-validate
```

Expected output:

- `.ai/outputs/knowledge-import/validation-report.md`
- `.ai/outputs/knowledge-import/validation-report.json`

Build the search index:

```powershell
.\scripts\workspace.ps1 knowledge-index
```

Expected output:

- `.ai/context/index/knowledge-cards.jsonl`
- `.ai/context/index/knowledge-index-summary.json`

Build the semantic graph:

```powershell
.\scripts\workspace.ps1 knowledge-graph
```

Expected output:

- `.ai/context/index/knowledge-graph.json`
- `.ai/context/index/metadata-knowledge-cards.jsonl`
- `.ai/context/index/metadata-knowledge-summary.json`
- `.ai/context/index/knowledge-index-files.yaml`

### 6. Search And Verify Retrieval

Search by business topic:

```powershell
.\scripts\workspace.ps1 knowledge-search -Query "invoice approval"
```

Search with semantic filters:

```powershell
.\scripts\workspace.ps1 knowledge-search -Query "approval status" -KnowledgeSearchFlags "--object Invoice__c --field Status__c --usage-context 'Solution Design'"
```

Expected output:

- Ranked search results in the terminal.
- Match explanations and risk flags where available.

### 7. Rebuild Work Item Context

After a sync, note creation, or review status change, rebuild the relevant Work Item context pack:

```powershell
.\scripts\workspace.ps1 ai-context -WorkItem KIM-1234 -Query "invoice approval"
```

Expected output:

- `.ai/context/work-items/KIM-1234/context-pack.md`
- `.ai/context/work-items/KIM-1234/relevant-knowledge.yaml` when knowledge is selected.

Knowledge is supporting evidence only. Prompts still require Work Item acceptance criteria and source artifacts.

### 8. Push Reviewed Notes To The External KB Repository

Preview push changes first:

```powershell
.\scripts\workspace.ps1 knowledge-push-dry-run
```

Expected output:

- Push preview report showing changed files and skipped files.
- No remote push.

Only after review, push curated notes:

```powershell
.\scripts\workspace.ps1 knowledge-push -KnowledgePushMessage "Update reviewed billing knowledge"
```

Expected output:

- Local vendor clone commit.
- Remote branch push to the external Knowledge Base repository.

Do not push notes with `possible_secret`, raw dumps, unsupported package claims, missing owner, or unresolved conflict findings.

## Expected Outputs

| Procedure | Primary outputs |
| --- | --- |
| Sync | `.ai/knowledge/`, `.ai/knowledge/sync-state.json`, `.ai/outputs/knowledge-sync/` |
| Create | `.ai/knowledge/**/*.md`, `.ai/outputs/knowledge-import/` |
| Validate | `.ai/outputs/knowledge-import/validation-report.md`, `.ai/outputs/knowledge-import/validation-report.json` |
| Index | `.ai/context/index/knowledge-cards.jsonl`, `.ai/context/index/knowledge-index-summary.json` |
| Graph | `.ai/context/index/knowledge-graph.json`, metadata knowledge cards, YAML index |
| Context | `.ai/context/work-items/<WORK_ITEM>/context-pack.md`, `relevant-knowledge.yaml` |
| Push | External KB Git branch update after review |

## Review Gates

| Gate | Required decision |
| --- | --- |
| Source intake | Source is controlled, safe, and appropriate for KB creation. |
| Draft note review | Owner confirms purpose, summary, source, semantic fields, warnings, and business meaning. |
| Validation | Blocking findings are resolved; low-severity quality warnings are accepted or corrected. |
| Context use | Draft, low-confidence, stale, or unowned notes are marked and confirmed before design use. |
| External KB push | Human reviewer approves changed notes and push target. |

Status and confidence rules:

| Status | Confidence | Operator handling |
| --- | --- | --- |
| `reviewed` or `approved` | `high` | Can be cited with note path. |
| `reviewed` | `medium` | Can be cited with a validation note. |
| `draft` | any | Discovery only; require explicit confirmation. |
| any | `low` | Surface to human; do not use as design basis. |

## Troubleshooting

| Symptom | Check | Safe fix | Escalate when |
| --- | --- | --- | --- |
| Sync cannot clone | `git ls-remote <kb-repo-url>` | Confirm Git credentials, repo URL, branch, and team access. | Access is denied for a valid repo and branch. |
| Created note is missing useful content | Review import warnings and parse status. | Improve source file quality or create a curated note manually. | The source requires interpretation by a domain owner. |
| Validation blocks on sensitive content | Open the validation report. | Remove secrets, raw data, logs, or record IDs before retrying. | Sensitive content may already have been committed. |
| Search misses a known note | Confirm `knowledge-index` was run and keywords/aliases exist. | Add aliases, key concepts, related objects, fields, and keywords, then re-index. | The note conflicts with schema, config, tests, or owner facts. |
| Context pack omits relevant knowledge | Check `relevant-knowledge.yaml` and query terms. | Rebuild context with a better query or update note semantic fields. | The selected note is stale, draft, or low-confidence and the user needs design evidence. |

## Escalation

Escalate to the domain owner or Salesforce Platform Team when:

- A note conflicts with Salesforce schema, anonymized config records, tests, or human-provided facts.
- A source file contains secrets, production data, logs, or uncontrolled exports.
- A managed-package behavior claim cannot be traced to approved evidence.
- A generated note is too ambiguous to review safely.
- External Knowledge Base push target, branch, or ownership is unclear.

Keep a working record in the Work Item context or review notes: command run, output path, finding, decision, owner, and next action.

## Safety Boundaries

- Do not use external model APIs or model orchestration tools.
- Do not deploy Salesforce metadata.
- Do not apply configuration records.
- Do not write Salesforce data.
- Do not commit `.ai/knowledge/imports/` source files, raw dumps, secrets, logs, or local config.
- Do not treat imported raw documents as reviewed truth.
- Do not assume KimbleOne/Kantata internals beyond sourced, reviewed evidence.

## Maintenance

- Re-run `knowledge-validate`, `knowledge-index`, and `knowledge-graph` after KB note changes.
- Review stale notes at least every 180 days or earlier when related metadata/config changes.
- Keep the domain registry aligned with actual KB folder structure.
- Update this runbook when command names, output paths, or approval gates change.
- Use `docs/workspace/runbook-2.0-quality-checklist.md` for future runbook reviews.
