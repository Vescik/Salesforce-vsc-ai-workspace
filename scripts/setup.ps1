$ErrorActionPreference = "Stop"
$python = Get-Command python3.11 -ErrorAction SilentlyContinue
if ($python) {
  & $python.Source scripts/setup.py @args
} else {
  python scripts/setup.py @args
}
