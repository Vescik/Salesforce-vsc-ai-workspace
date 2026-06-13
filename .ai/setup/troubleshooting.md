# Troubleshooting

## Python not found

Install Python 3.11 or newer and make sure `python` or `python3` is on `PATH`.

## Wrong Python version

Run `python --version` or `python3 --version`. The workspace expects Python 3.11 or newer.

## `sf` not found

Install Salesforce CLI and confirm `sf --version` works in a new terminal.

## Salesforce org alias is not authenticated

Run:

```bash
sf org login web --alias IntDev
```

Use your local alias if it differs from `IntDev`, then update `.ai/config/workspace.local.json`.

## Knowledge Base repo access denied

Confirm your SSH key or HTTPS credentials can clone the private Knowledge Base repository. Run `make knowledge-sync-dry-run KB_REPO=<repo-url>` before syncing.

## Git not found

Install Git and confirm `git --version` works.

## VS Code task cannot find `make`

On Windows, `make` may not be installed. Use the Python wrappers directly:

```powershell
python scripts/setup.py
python scripts/doctor.py
```

## `PYTHONPATH` issues

Run commands through `make` or the wrapper scripts. They set `.ai/skills/python` for local tools.

## `.ai/config/workspace.local.json` missing

Run:

```bash
make setup
```

The local config file is intentionally ignored by Git.
