param()
$ErrorActionPreference = 'Stop'
$phase8Cli = 'C:\Program Files\Amazon\AWSCLIV2\aws.exe'
if (-not (Test-Path -LiteralPath $phase8Cli)) { throw 'AWS CLI v2 and the fyp-research profile are required.' }
$phase8State = & $phase8Cli ec2 describe-instances --instance-ids i-0a6196aff6f8098ac --query 'Reservations[0].Instances[0].State.Name' --output text --profile fyp-research --region ap-southeast-2 --no-cli-pager
if ($LASTEXITCODE -ne 0) { throw 'Status lookup failed; this command did not start a server or execution.' }
Write-Output "AWS server state: $phase8State"
if ($phase8State.Trim() -eq 'running') { & (Join-Path $PSScriptRoot 'Check-Progress.ps1'); return }
Write-Output 'Campaign failure pause retained. Do not restart or replay the first original.'
Write-Output 'Last verified saved count: 1 original collected/backed up; 1,499 unstarted. This is a saved status, not a live ledger query.'
Write-Output 'Run: p85-01a116f7-3b82-7a79-8653-3aee62dc99e9'
Get-Content -LiteralPath (Join-Path $PSScriptRoot 'stop-preserved.json')
