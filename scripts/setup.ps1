$ErrorActionPreference = "Stop"
$python = if (Get-Command python3.11 -ErrorAction SilentlyContinue) { "python3.11" } else { "python" }
& $python -m pip install -e . --quiet
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python scripts/setup.py @args
