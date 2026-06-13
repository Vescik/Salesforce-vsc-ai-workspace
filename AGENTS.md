# AI Assistant Rules

This repository supports Salesforce development on top of a closed managed package: KimbleOne/Kantata. All AI assistants must follow these rules.

GitHub Copilot is the only approved AI execution layer for this repository.

## Source Boundaries

- Do not assume access to KimbleOne/Kantata managed package source.
- Do not use, suggest, scaffold, or integrate external model APIs, including OpenAI API, Anthropic API, LangChain, or similar model orchestration tools.
- Reason only from Azure DevOps requirements, repository metadata, Salesforce schema, anonymized configuration records, tests, and human-provided facts.
- Treat IntDev as a Full Copy developer org without Git. IntDev is not the source of truth.
- Treat Work Item branches as created and managed through DevOps Center.
- Use curated context packs and approved local indexes instead of uncontrolled dumps.

## Delivery Rules

- Do not generate production deployment steps unless explicitly requested.
- DevOps Center remains the official Salesforce metadata promotion mechanism.
- Treat configuration records as separate from Salesforce metadata deployment.
- Do not apply configuration records or write to production from the AI workspace.
- Prefer solution design, solution design review, documentation, QA how-to-test guidance, and implementation work packets over direct development.
- Every implementation recommendation must map to a Work Item and acceptance criteria.

## Data And Security Rules

- Do not hardcode Salesforce record IDs.
- Do not commit raw data dumps, secrets, logs, or uncontrolled exports.
- Use only controlled, anonymized configuration examples when documentation or review requires sample records.

## OOTB Setup And Configuration

- Prefer values from `.ai/config/workspace.local.json` or approved environment variables when local paths, org aliases, or Knowledge Base settings are needed.
- Do not hardcode employee-specific filesystem paths, Salesforce usernames, org aliases, or Knowledge Base repository URLs.
- Do not ask users to commit `.ai/config/workspace.local.json`.
- Salesforce authentication is handled by Salesforce CLI and must not be stored in workspace config.
- Setup and doctor tooling must remain deterministic, local, and standard-library Python where possible.
- Do not add external model APIs, deployment automation, config apply tools, or Salesforce write tools as part of setup.
- Knowledge Base repository settings are configured locally or through environment variables such as `KB_REPO` and `KB_BRANCH`.

## Azure DevOps MCP Usage

- Azure DevOps MCP is approved only for read-only Work Item retrieval through `/fetch-us`.
- Never use Azure DevOps MCP tools to create, update, assign, transition, comment on, or link Work Items.
- Do not store ADO tokens, PATs, credentials, or employee secrets in committed configuration.
- ADO Work Item content becomes local planning context only; it is not source code, deployment evidence, or approval to promote.
- Documentation, QA, solution design, and implementation recommendations must trace to normalized local Work Item artifacts and acceptance criteria.

## Azure Wiki Documentation Rules

- Azure DevOps Wiki publication must be draft-first.
- Always inspect existing wiki structure before selecting a target path.
- Prefer existing object, functionality, process, or module documentation sections.
- If no matching section exists, route to `_Proposed` or `_Unclassified` and require review.
- AI may prepare draft pages and branch changes only.
- AI must not push without explicit human approval.
- AI must never push directly to the wiki default branch.
- AI must not merge wiki PRs.
- AI must not overwrite existing wiki pages without review, diff evidence, and approval.
- All wiki docs must cite source artifacts from this workspace.
- AI-generated draft docs require human review before publication.
- Do not store Azure DevOps Wiki PATs, tokens, or credentials in repository config.

## Internal Knowledge Base Usage

- Internal managed package knowledge lives under `.ai/knowledge/`.
- The external Knowledge Base Git repository is the source of truth.
- `.ai/knowledge/` may contain a synchronized local copy for this workspace.
- Instructions define rules and guardrails; knowledge notes define sourced facts and internal observations.
- Do not load the entire knowledge base for every task.
- Prefer Work Item context packs, `knowledge-cards.jsonl`, and selected KB notes over uncontrolled raw documents.
- Claims based on KB notes must reference the source file path or knowledge note path.
- Draft, low-confidence, stale, or unowned KB notes require human validation.
- If KB conflicts with Salesforce schema, anonymized config records, tests, or human-provided facts, mark the conflict for human validation.
- Do not assume KimbleOne/Kantata internals beyond documented knowledge, schema, config records, tests, or human-confirmed facts.
