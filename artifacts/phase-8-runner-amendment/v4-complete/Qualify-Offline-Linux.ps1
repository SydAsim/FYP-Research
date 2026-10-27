param([Parameter(Mandatory=$true)][string]$Attempt)
$ErrorActionPreference = 'Stop'
if ($Attempt -notmatch '^attempt[0-9]+$') { throw 'A separate numbered attempt is required.' }
$taskDir = $PSScriptRoot
$taskEvidence = 'E:/FYP Project/phase85-combined-v3'
$taskName = "p85-v3-offline-$Attempt"
if (Test-Path -LiteralPath "$taskDir/linux-$Attempt.txt") { throw 'Retain existing attempt.' }
New-Item -ItemType Directory -Path $taskEvidence -Force | Out-Null
$taskStats = [ordered]@{
    utc=(Get-Date).ToUniversalTime().ToString('o')
    available_memory_bytes=(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory*1024
    free_C_bytes=(Get-PSDrive C).Free
    free_E_bytes=(Get-PSDrive E).Free
    scope='OFFLINE_CONTROL_TESTS_NO_APPLICATION_EXECUTIONS'
}
$taskStats | ConvertTo-Json | Set-Content -LiteralPath "$taskDir/linux-$Attempt-resources.json"
if ($taskStats.available_memory_bytes -lt 1.5GB -or $taskStats.free_C_bytes -lt 2GB -or $taskStats.free_E_bytes -lt 2GB) { throw 'Bounded offline resource stop.' }
docker run --pull never --name $taskName --network none --memory 1g --cpus 1 `
    -e P85_MASTER=/retained/master -e P85_FIRST=/retained/first -e P85_SECOND=/retained/second `
    -e P85_FIRST_ARCHIVE=/retained/first.tar.gz -e P85_SECOND_ARCHIVE=/retained/second.tar.gz `
    -v "${taskDir}:/opt/fyp-phase8-linux-v1/artifacts/phase-8-runner-amendment/v3:ro" `
    -v 'C:/p8c1/m/x/slot:/retained/master:ro' `
    -v 'C:/fyp-p85/stopped-attempt1/slot1/x/slot:/retained/first:ro' `
    -v 'C:/p8c1/s/x/slot:/retained/second:ro' `
    -v 'C:/fyp-p85/stopped-attempt1/slot1/t/e.tar.gz:/retained/first.tar.gz:ro' `
    -v 'C:/p8c1/s/t/e.tar.gz:/retained/second.tar.gz:ro' `
    -v "${taskEvidence}:/cal" `
    sha256:5faee27d3793882b26aa166de48fc26d7939710ac9435b0fe7f988c8765497d8 `
    timeout --signal=TERM --kill-after=10s 540s python -m pytest `
    artifacts/phase-8-runner-amendment/v3/test_combined.py `
    artifacts/phase-8-runner-amendment/v3/test_collector.py -q --basetemp "/cal/linux-$Attempt" `
    *> "$taskDir/linux-$Attempt.txt"
if ($LASTEXITCODE -ne 0) { throw "Qualification failed; retained $taskName and all evidence." }
Get-Content -LiteralPath "$taskDir/linux-$Attempt.txt" -Tail 5
