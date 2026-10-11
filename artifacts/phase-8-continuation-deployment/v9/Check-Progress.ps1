param([string]$Profile = 'fyp-research')
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$region = 'ap-southeast-2'
$instance = 'i-057344e5372faf62f'
$state = (& aws ec2 describe-instances --profile $Profile --region $region --instance-ids $instance --query 'Reservations[0].Instances[0].State.Name' --output text)
if ($LASTEXITCODE -ne 0) { throw 'AWS read failed. This command never restarts the host.' }
Write-Host "Host: $instance; state: $state"
if ($state -ne 'running') { Write-Host 'Inspect REPORT.md and retained backup proofs. No campaign action taken.'; return }
$taskProgressBody = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'progress-v2.sh')).Replace("`r`n", "`n")
$taskBashCommand = "bash -s <<'FYP_READ_ONLY_PROGRESS'`n" + $taskProgressBody + "`nFYP_READ_ONLY_PROGRESS`n"
$payload = @{ commands = @($taskBashCommand); executionTimeout = @('60') }
$requestPath = Join-Path ([IO.Path]::GetTempPath()) ('fyp-v9-progress-' + [guid]::NewGuid().ToString() + '.json')
[IO.File]::WriteAllText($requestPath, ($payload | ConvertTo-Json -Depth 4), [Text.UTF8Encoding]::new($false))
$sent = (& aws ssm send-command --profile $Profile --region $region --instance-ids $instance --document-name AWS-RunShellScript --comment 'Read-only progress; no admission or restart' --parameters ("file://" + $requestPath) --output json)
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
