# Configuration Record Promotion Rules

This folder is reserved for future configuration record promotion guidance and artifacts.

GitHub Copilot is the only approved AI execution layer for this repository. Do not use external model APIs, LangChain, OpenAI API, Anthropic API, or similar model orchestration tooling.

## Scope

- Separate configuration record promotion from Salesforce metadata promotion.
- Do not promote transactional records.
- Use stable external keys where possible.
- Avoid `Id`, `OwnerId`, and `SystemModstamp` fields in configuration packs.
- DevOps Center remains the official Salesforce metadata promotion mechanism.
- IntDev is a Full Copy developer/discovery org without Git and is not the source of truth.
- Use curated context packs and anonymized indexes instead of uncontrolled dumps.
- Do not implement config apply, production writes, or Salesforce write tools in this workspace.
- Do not assume KimbleOne/Kantata managed package internals.

## Future Phases

- Generate dry-run, diff, and rollback support in later phases.
- Do not implement dry-run, diff, rollback, Salesforce API calls, MCP servers, CI workflows, or parser logic in this phase.
