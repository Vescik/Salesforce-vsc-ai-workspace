# Troubleshooting

## Python not found

Install Python 3.11 or newer and make sure `python` is on `PATH`.

Download from [python.org](https://www.python.org/downloads/).

## Wrong Python version

Check your version:
```powershell
python --version
```
The workspace requires Python 3.11 or newer.

## `sf` (Salesforce CLI) not found

Install Salesforce CLI:
```powershell
npm install -g @salesforce/cli
```
Then confirm with `sf --version` in a new terminal.

## Salesforce org alias not authenticated

```powershell
sf org login web --alias IntDev
```

Use your local alias if it differs from `IntDev`, then update `.ai/config/workspace.local.json`.

## `workspace.local.json` missing

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 setup
```
```bash
# Mac / Linux
make setup
```

The local config file is intentionally ignored by Git.

## `make` not available (Windows)

On Windows, use the PowerShell wrapper instead of `make`:

```powershell
.\scripts\workspace.ps1 <command>        # e.g. .\scripts\workspace.ps1 doctor
.\scripts\workspace.ps1 help             # list all available commands
```

All commands are also available via VS Code Tasks: `Ctrl+Shift+P` → `Tasks: Run Task`

## PowerShell script blocked by execution policy

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then re-run your command.

## `ai_workspace` import error / module not found

Run:
```powershell
pip install -e .
```

This registers the `ai_workspace` package. All workspace commands run it automatically. Only needed once per Python environment.

## Knowledge Base repo access denied

Confirm your credentials can clone the private Knowledge Base repository. Run dry-run first:

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 knowledge-sync-dry-run -KbRepo "<repo-url>"
```
```bash
# Mac / Linux
make knowledge-sync-dry-run KB_REPO=<repo-url>
```

## Git not found

Install Git from [git-scm.com](https://git-scm.com/) and confirm `git --version` works.

## Doctor check for all issues

```powershell
# Windows (PowerShell)
.\scripts\workspace.ps1 doctor
```
```bash
# Mac / Linux
make doctor
```

The doctor report is written to `.ai/outputs/doctor/doctor.md`.
