param([Parameter(Mandatory=$true)][string]$Attempt)
$ErrorActionPreference = 'Stop'
if ($Attempt -notmatch '^attempt[0-9]+$') { throw 'Use a separate numbered attempt ID.' }
$taskCandidate = $PSScriptRoot
$taskRoot = "E:\FYP Project\phase85-runner-amendment-v1"
$taskName = "p85a-$Attempt"
$taskNetwork = "p85a-$Attempt-net"
$taskImage = 'sha256:5faee27d3793882b26aa166de48fc26d7939710ac9435b0fe7f988c8765497d8'
$taskStats = [ordered]@{
    at_utc = (Get-Date).ToUniversalTime().ToString('o')
    scope = 'LOCAL_CALIBRATION_ONLY'
    free_C_bytes = (Get-PSDrive C).Free
    free_E_bytes = (Get-PSDrive E).Free
    available_RAM_bytes = (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory * 1024
    cloud_operations = 0
    main_executions = 0
}
$taskPreflight = Join-Path $taskCandidate "$Attempt-windows-preflight.json"
if (Test-Path -LiteralPath $taskPreflight) { throw 'Existing preflight retained; use a new attempt ID.' }
$taskStats | ConvertTo-Json | Set-Content -LiteralPath $taskPreflight
if ($taskStats.free_C_bytes -lt 10GB -or $taskStats.free_E_bytes -lt 20GB -or
    $taskStats.available_RAM_bytes -lt 1.5GB) { throw 'RESOURCE_STOP: retain preflight; no driver admitted.' }
if (Test-Path -LiteralPath (Join-Path $taskRoot $Attempt)) { throw 'Retain existing attempt; no replacement.' }
if ((docker image inspect fyp-phase84-v2:final-review --format '{{.Id}}').Trim() -ne $taskImage) {
    throw 'CACHED_IMAGE_DRIFT'
}
New-Item -ItemType Directory -Path $taskRoot -Force | Out-Null
docker network create --internal --label research.linux.validation=v1 $taskNetwork
if ($LASTEXITCODE -ne 0) { throw 'Local network failed' }
docker run --pull=never --name $taskName --network $taskNetwork --memory 3g --cpus 2 `
    -e P8_DOCKER_DATA_PATH=/calibration -e "P85_CALIBRATION_NETWORK=$taskNetwork" `
    -v /var/run/docker.sock:/var/run/docker.sock `
    -v "${taskCandidate}:/opt/fyp-phase8-linux-v1/artifacts/phase-8-runner-amendment/v1:ro" `
    -v "${taskRoot}:/calibration" -d $taskImage python -c 'import time; time.sleep(4000)'
if ($LASTEXITCODE -ne 0) { throw 'Local capsule failed; retain network.' }
# Intentionally detached. No Codex conversation, AWS credentials, or paid providers.
docker exec -d $taskName sh -c "python artifacts/phase-8-runner-amendment/v1/qualify.py /calibration/$Attempt > /calibration/$Attempt-console.log 2>&1"
if ($LASTEXITCODE -ne 0) { throw 'Qualification dispatch failed; retain resources.' }
Write-Output "Local qualification dispatched: $taskRoot\$Attempt-console.log"
Write-Output 'Stop on a retained failure; do not repeat scientific commands automatically.'
