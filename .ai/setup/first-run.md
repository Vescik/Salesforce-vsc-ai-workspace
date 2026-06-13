# First Run

1. Clone the Salesforce project repository.
2. Install prerequisites from `.ai/setup/prerequisites.md`.

3. Install the workspace package and run setup:

   ```powershell
   # Windows (PowerShell)
   pip install -e .
   .\scripts\workspace.ps1 setup
   ```
   ```bash
   # Mac / Linux
   pip install -e .
   make setup
   ```

4. Configure local values:

   ```powershell
   # Windows (PowerShell)
   .\scripts\workspace.ps1 configure
   ```
   ```bash
   # Mac / Linux
   make configure
   ```

5. Authenticate the developer org with Salesforce CLI:

   ```powershell
   sf org login web --alias IntDev
   ```

6. Run doctor:

   ```powershell
   # Windows (PowerShell)
   .\scripts\workspace.ps1 doctor
   ```
   ```bash
   # Mac / Linux
   make doctor
   ```

7. Build the local repository metadata index:

   ```powershell
   # Windows (PowerShell)
   .\scripts\workspace.ps1 ai-index-repo
   ```
   ```bash
   # Mac / Linux
   make ai-index-repo
   ```

8. Fetch Work Item context:

   ```text
   /fetch-us EXAMPLE-WI
   ```

   This uses read-only Azure DevOps MCP when available. If MCP is unavailable, paste the Work Item content when prompted so the same local artifact shape is created.

9. Optionally sync and index the Knowledge Base:

   ```powershell
   # Windows (PowerShell)
   .\scripts\workspace.ps1 knowledge-sync -KbRepo "<repo-url-or-local-path>"
   .\scripts\workspace.ps1 knowledge-index
   ```
   ```bash
   # Mac / Linux
   make knowledge-sync KB_REPO=<repo-url-or-local-path>
   make knowledge-index
   ```

10. Build a Work Item context pack:

    ```powershell
    # Windows (PowerShell)
    .\scripts\workspace.ps1 ai-context -WorkItem EXAMPLE-WI -Query "example"
    ```
    ```bash
    # Mac / Linux
    make ai-context WORK_ITEM=EXAMPLE-WI QUERY="example"
    ```

11. Use Copilot prompt files such as `/solution-design`, `/solution-design-review`, and `/create-how-to-test`.

DevOps Center remains the official Salesforce metadata promotion mechanism. These commands do not deploy metadata or apply configuration records.

> **All commands are also available as VS Code Tasks:** `Ctrl+Shift+P` → `Tasks: Run Task`
