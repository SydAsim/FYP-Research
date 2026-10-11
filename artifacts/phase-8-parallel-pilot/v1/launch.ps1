# Run from the project root. Supplies the repository import root without editing
# sealed research code. This controller wrapper is not main-study launch authority.
$ErrorActionPreference = 'Stop'
$pilotPreviousPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = (Get-Location).Path
    & .venv/Scripts/python.exe artifacts/phase-8-parallel-pilot/v1/deploy.py --approval artifacts/phase-8-parallel-pilot/v1/approval.json
    if ($LASTEXITCODE -ne 0) { throw 'Pilot deployment failed; retain original journals and reconcile any launch intent before retrying.' }
} finally {
    $env:PYTHONPATH = $pilotPreviousPythonPath
}
