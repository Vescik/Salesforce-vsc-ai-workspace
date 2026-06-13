$ErrorActionPreference = "Stop"
$python = Get-Command python3.11 -ErrorAction SilentlyContinue
if ($python) {
  & $python.Source scripts/doctor.py @args
} else {
  python scripts/doctor.py @args
}
