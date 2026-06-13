# GitHub Copilot Instructions

GitHub Copilot is the only approved AI execution layer for this repository.

## AI Provider Rules

- Do not suggest, scaffold, or add integrations with external LLM APIs, including OpenAI API, Anthropic API, LangChain, or similar model orchestration tools.
- Do not create autonomous deployment agents.
- Keep Copilot assistance focused on solution design, review, documentation, context indexing, QA how-to-test generation, and deployment precheck support.

## Salesforce Delivery Rules

- Treat DevOps Center as the Salesforce metadata deployment mechanism.
- Work in small work packets that map clearly to Work Items and acceptance criteria.
- Do not generate production deployment steps unless explicitly requested.
- Do not modify Salesforce metadata unless a Work Item and acceptance criteria justify the change.

## OOTB Setup And Configuration

- Prefer values from `.ai/config/workspace.local.json` or approved environment variables for local paths, Salesforce org aliases, and Knowledge Base settings.
- Do not hardcode employee-specific paths, Salesforce usernames, org aliases, or private repository URLs.
- Do not ask users to commit `.ai/config/workspace.local.json`.
- Salesforce auth is handled by Salesforce CLI, not stored configuration.
- Keep setup deterministic and local.
- Do not add external model APIs, deployment automation, config apply tools, or Salesforce write tools.
- Configure the Knowledge Base repository locally or through `KB_REPO` and `KB_BRANCH`.

## Release And Deployment Guidance

- Do not claim deployment, validation, promotion, or production release success unless a human provides that evidence.
- Prepare reports, checklists, release-readiness reviews, and pre-promote summaries only.
- Treat DevOps Center as the official Salesforce metadata promotion path.
- Do not create deployment automation, config apply scripts, or autonomous release agents.
- Do not write to Salesforce, apply configuration records, or create production write tools.
- Do not invent real branch names; use DevOps Center/team-provided branch mappings or placeholders.
- Treat IntDev as a Full Copy developer/discovery org, not the source of truth.
- Treat config record changes as a separate sidecar review from Salesforce metadata promotion.
- State that production config apply is not implemented and requires future controlled tooling/manual approval when config records are in scope.

## KimbleOne/Kantata Rules

- Do not assume access to KimbleOne/Kantata managed package source or internals.
- Treat KimbleOne/Kantata configuration records separately from Salesforce metadata.
- Reason from ADO requirements, repository metadata, Salesforce schema, anonymized configuration records, tests, and human-provided facts.

## Documentation And QA Rules

- Documentation and QA outputs must be traceable to Work Item artifacts, context packs, solution designs, Git diffs, precheck reports, config-impact summaries, or human-provided facts.
- Use curated context packs and approved local indexes instead of uncontrolled dumps.
- Do not invent managed package behavior or implementation details.
- Mark missing artifacts, assumptions, and uncertainty explicitly.
- Treat generated documentation and QA how-to-test files as drafts requiring human review.

## Azure Wiki Documentation Rules

- Azure DevOps Wiki publication must be draft-first.
- Inspect existing wiki structure before choosing a target path.
- Prefer existing object, functionality, process, or module documentation sections.
- If no matching section exists, route to `_Proposed` or `_Unclassified` and require review.
- You may prepare draft pages and feature-branch changes only.
- Do not push without explicit human approval.
- Never push directly to the wiki default branch.
- Do not merge wiki PRs.
- Do not overwrite existing wiki pages without review, diff evidence, and approval.
- Cite source artifacts from this workspace in every wiki draft.
- AI-generated wiki drafts require human review before publication.
- Do not store Azure DevOps Wiki PATs, tokens, or credentials in repository config.

## MCP Context Rules

- Prefer the `salesforce-context` MCP server for Work Item context, schema cards, metadata indexes, config impact artifacts, and solution design artifacts when it is available.
- Do not request raw org exports when curated context indexes or context packs are available.
- Do not use MCP context to infer KimbleOne/Kantata managed package internals beyond the provided local evidence.
- Use Azure DevOps MCP only for read-only Work Item retrieval through `/fetch-us`.
- Never use ADO MCP tools to create, update, assign, transition, comment on, or link Work Items.
- Do not store ADO tokens, PATs, credentials, or employee secrets in committed configuration.
- Treat fetched ADO Work Item content as local planning context, not source code, deployment evidence, or promotion approval.

## Internal Knowledge Base Usage

- Internal managed package knowledge lives under `.ai/knowledge/`.
- The external Knowledge Base Git repository is the source of truth.
- `.ai/knowledge/` may contain a synchronized local copy for this workspace.
- Instructions define rules and guardrails; knowledge notes define sourced facts and internal observations.
- Do not load the entire KB for every task.
- Prefer Work Item context packs, `knowledge-cards.jsonl`, and selected KB notes over uncontrolled raw documents.
- Claims based on KB notes must reference the source file path or knowledge note path.
- Draft, low-confidence, stale, or unowned KB notes require human validation.
- If KB conflicts with Salesforce schema, anonymized config records, tests, or human-provided facts, mark the conflict for human validation.
- Do not assume KimbleOne/Kantata internals beyond documented knowledge, schema, config records, tests, or human-confirmed facts.
