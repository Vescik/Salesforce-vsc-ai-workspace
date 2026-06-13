# First Run

1. Clone the Salesforce project repository.
2. Install prerequisites from `.ai/setup/prerequisites.md`.
3. Run setup:

```bash
make setup
```

4. Configure local values:

```bash
make configure
```

5. Authenticate the developer org with Salesforce CLI:

```bash
sf org login web --alias IntDev
```

6. Run doctor:

```bash
make doctor
```

7. Build the local repository metadata index:

```bash
make ai-index-repo
```

8. Fetch Work Item context:

```text
/fetch-us EXAMPLE-WI
```

This uses read-only Azure DevOps MCP when available. If MCP is unavailable, paste the Work Item content when prompted so the same local artifact shape is created.

9. Optionally sync and index the Knowledge Base:

```bash
make knowledge-sync KB_REPO=<repo-url-or-local-path>
make knowledge-index
```

Alternatively, set the ignored `.ai/config/workspace.local.json` value before syncing:

```json
{
  "knowledge_base": {
    "enabled": true,
    "repo_url": "git@github.com:<ORG>/<KB_REPO>.git",
    "branch": "main",
    "sync_on_setup": false
  }
}
```

10. Build a Work Item context pack:

```bash
make ai-context WORK_ITEM=EXAMPLE-WI QUERY="example"
```

11. Use Copilot prompt files such as `/solution-design`, `/solution-design-review`, and `/create-how-to-test`.

DevOps Center remains the official Salesforce metadata promotion mechanism. These commands do not deploy metadata or apply configuration records.
