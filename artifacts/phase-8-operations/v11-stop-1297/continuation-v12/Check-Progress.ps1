$ErrorActionPreference = 'Stop'
& python -B (Join-Path $PSScriptRoot 'check_progress.py')
if ($LASTEXITCODE -ne 0) { throw 'Read-only progress check failed. Evidence was retained; the campaign was not changed.' }
