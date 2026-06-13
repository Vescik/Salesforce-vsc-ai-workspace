# Salesforce Metadata Rules

These rules apply to local Salesforce metadata under `force-app`.

- Do not edit KimbleOne/Kantata managed package internals.
- Use `with sharing`, `without sharing`, or `inherited sharing` intentionally in Apex.
- Check CRUD/FLS when accessing user or business data.
- Do not hardcode Salesforce record IDs.
- Keep Apex, Flow, LWC, object, permission, and layout changes traceable to a Work Item and acceptance criteria.
- Treat DevOps Center as the official metadata promotion mechanism.
- Do not generate production deployment steps unless explicitly requested.
