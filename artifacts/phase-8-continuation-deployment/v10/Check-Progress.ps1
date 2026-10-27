param([string]$Profile = 'fyp-research')
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:AWS_MAX_ATTEMPTS = '1'
$env:AWS_RETRY_MODE = 'standard'
$instance = 'i-057344e5372faf62f'
$region = 'ap-southeast-2'
$common = @('--profile', $Profile, '--region', $region, '--cli-connect-timeout','5','--cli-read-timeout','10','--no-cli-pager')
$state = (& aws ec2 describe-instances --instance-ids $instance --query 'Reservations[0].Instances[0].State.Name' --output text @common)
if ($LASTEXITCODE -ne 0) { throw 'AWS state read failed. No restart or admission was requested.' }
Write-Host "Host: $instance; state: $state"
if ($state.Trim() -ne 'running') { return }
$body = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'capacity-resume/progress.sh')).Replace("`r`n", "`n")
$commandText = "bash -s <<'READ_ONLY_V10_PROGRESS'`n" + $body + "`nREAD_ONLY_V10_PROGRESS`n"
$recordDirectory = Join-Path $PSScriptRoot ('capacity-resume/progress-reads/' + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $recordDirectory | Out-Null
$requestPath = Join-Path $recordDirectory 'request.json'
[IO.File]::WriteAllText($requestPath, (@{commands=@($commandText);executionTimeout=@('60')} | ConvertTo-Json -Depth 4), [Text.UTF8Encoding]::new($false))
$sent = (& aws ssm send-command --instance-ids $instance --document-name AWS-RunShellScript --comment 'Read-only frozen-v10 progress; never restart or admit' --parameters ("file://" + $requestPath) --timeout-seconds 60 --output json @common)
[IO.File]::WriteAllText((Join-Path $recordDirectory 'send-response.json'), ($sent -join "`n"), [Text.UTF8Encoding]::new($false))
if ($LASTEXITCODE -ne 0) { throw "Request was not acknowledged; reconcile before resending. Evidence: $recordDirectory" }
$commandId = ($sent | ConvertFrom-Json).Command.CommandId
for ($i = 1; $i -le 8; $i++) {
    Start-Sleep -Seconds 2
    $raw = (& aws ssm get-command-invocation --command-id $commandId --instance-id $instance --output json @common)
    if ($LASTEXITCODE -ne 0) { throw "Read failed. Command $commandId was not resent; evidence: $recordDirectory" }
    [IO.File]::WriteAllText((Join-Path $recordDirectory "read-$i.json"), ($raw -join "`n"), [Text.UTF8Encoding]::new($false))
    $response = $raw | ConvertFrom-Json
    if ($response.Status -eq 'Success') { Write-Output $response.StandardOutputContent; return }
    if ($response.Status -in @('Failed','Cancelled','TimedOut')) { throw ($response | ConvertTo-Json -Depth 8) }
}
throw "Read remains unresolved. Retain command $commandId and $recordDirectory. No campaign state was changed."
