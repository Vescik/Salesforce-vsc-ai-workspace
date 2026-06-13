---
name: import-knowledge
description: Guide a human through importing an internal knowledge source file.
agent: knowledge-curator
argument-hint: <SOURCE_FILE> <DOMAIN> <TITLE>
---

# Import Knowledge

## Scope

Guide a human through importing a local internal knowledge file into `.ai/knowledge/`.

## Rules

- Do not rewrite imported source content as confirmed fact.
- Do not treat raw imported documents as reviewed truth.
- Do not call Salesforce, ADO, external model APIs, deployment tools, or config apply tools.
- Use the deterministic importer.
- Imported notes default to `status: draft` and `confidence: low`.
- Imported notes require human review before use as confirmed knowledge.
- Do not include secrets, credentials, raw exports, or uncontrolled sensitive data.

## Recommended Steps

1. Confirm the source file is safe to import and is under `.ai/knowledge/imports/`.
2. Run:

```bash
make knowledge-import KNOWLEDGE_SOURCE="<SOURCE_FILE>" KNOWLEDGE_DOMAIN="<DOMAIN>" KNOWLEDGE_TITLE="<TITLE>"
```

3. Review the generated markdown note under `.ai/knowledge/domains/<DOMAIN>/`.
4. Run:

```bash
make knowledge-index
```

5. Rebuild the relevant Work Item context pack:

```bash
make ai-context WORK_ITEM=<WORK_ITEM_ID> QUERY="<business topic>"
```

## Output

Return a short import checklist, the exact command to run, expected output paths, and review reminders.
