param()
$ErrorActionPreference = 'Stop'
$phase8Cli = 'C:\Program Files\Amazon\AWSCLIV2\aws.exe'
if (-not (Test-Path -LiteralPath $phase8Cli)) { throw 'AWS CLI v2 is required. Use AWS Console > Systems Manager > Session Manager instead.' }
$phase8Parameters = '{"commands":["/var/lib/p8-deployment/progress.sh"],"executionTimeout":["60"]}'
$phase8CommandJson = & $phase8Cli ssm send-command --instance-ids i-0a6196aff6f8098ac --document-name AWS-RunShellScript --parameters $phase8Parameters --comment 'Read-only frozen Phase 8 campaign progress' --profile fyp-research --region ap-southeast-2 --output json --no-cli-pager
if ($LASTEXITCODE -ne 0) { throw 'Progress request failed. Do not restart the server or replay any original.' }
$phase8CommandId = ($phase8CommandJson | ConvertFrom-Json).Command.CommandId
$phase8Deadline = [DateTime]::UtcNow.AddSeconds(90)
while ([DateTime]::UtcNow -lt $phase8Deadline) {
    Start-Sleep -Seconds 3
    $phase8Reply = & $phase8Cli ssm get-command-invocation --command-id $phase8CommandId --instance-id i-0a6196aff6f8098ac --profile fyp-research --region ap-southeast-2 --output json --no-cli-pager 2>$null
    if ($LASTEXITCODE -ne 0) { continue }
    $phase8Invocation = $phase8Reply | ConvertFrom-Json
    if ($phase8Invocation.Status -in @('Pending','InProgress','Delayed')) { continue }
    $phase8Invocation.StandardOutputContent
    if ($phase8Invocation.StandardErrorContent) { Write-Warning $phase8Invocation.StandardErrorContent }
    if ($phase8Invocation.Status -ne 'Success') { throw "Progress command ended with $($phase8Invocation.Status). Preserve evidence and inspect; do not reset the campaign." }
    return
}
throw "Progress reply timed out. Request ID: $phase8CommandId. Retrieve that same request later; this did not replay any execution."
