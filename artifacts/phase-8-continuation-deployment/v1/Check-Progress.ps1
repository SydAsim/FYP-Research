param([string]$Profile = 'fyp-research')
$ErrorActionPreference = 'Stop'
$region = 'ap-southeast-2'
$instance = 'i-034252c3e9b083abf'
$state = (& aws ec2 describe-instances --profile $Profile --region $region --instance-ids $instance --query 'Reservations[0].Instances[0].State.Name' --output text)
if ($LASTEXITCODE -ne 0) { throw 'AWS read failed. Do not restart or replace the host.' }
Write-Host "Host: $instance; state: $state"
if ($state -ne 'running') {
    Write-Host 'Campaign is not running. Inspect REPORT.md and the pinned backup proofs. This command never starts AWS.'
    return
}
$payload = @{ commands = @([IO.File]::ReadAllText((Join-Path $PSScriptRoot 'progress.sh')).Replace("`r`n", "`n")); executionTimeout = @('60') }
$requestPath = Join-Path ([IO.Path]::GetTempPath()) ('fyp-progress-' + [guid]::NewGuid().ToString() + '.json')
[IO.File]::WriteAllText($requestPath, ($payload | ConvertTo-Json -Depth 4), [Text.UTF8Encoding]::new($false))
$sent = (& aws ssm send-command --profile $Profile --region $region --instance-ids $instance --document-name AWS-RunShellScript --comment 'Read-only campaign progress; no admission or restart' --parameters ("file://" + $requestPath) --output json)
if ($LASTEXITCODE -ne 0) { throw "Progress request failed; retained request: $requestPath" }
$command = ($sent | ConvertFrom-Json).Command.CommandId
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    $raw = (& aws ssm get-command-invocation --profile $Profile --region $region --command-id $command --instance-id $instance --output json 2>$null)
    if ($LASTEXITCODE -ne 0) { continue }
    $response = $raw | ConvertFrom-Json
    if ($response.Status -eq 'Success') { Write-Output $response.StandardOutputContent; return }
    if ($response.Status -in @('Failed','Cancelled','TimedOut')) { throw ($response | ConvertTo-Json -Depth 8) }
}
throw "Progress read unfinished; retained request $requestPath, command $command. No campaign action taken."
