# Prepared fallback — NOT AUTHORIZED OR EXECUTED

## Route and concrete prerequisites

Keep campaign instance `i-057344e5372faf62f` stopped throughout. Read its existing
root `vol-09dbb42bbf607f5de` as a **secondary disk on a clean maintenance helper**.
Do not boot the campaign root, chroot into it, enable its units, start Docker,
run its Python modules, replay requests, or clear its durable pause. This avoids
the unqualified assumption that stopping campaign/watchdog units after boot
prevents autostart: those units must never be loaded by the helper's systemd.

This route is NOT yet qualified. It requires separate maintenance authorization,
working AWS connectivity, fresh prices/spending/credits and a passing cost gate,
confirmed current stopped state, ownership/root mapping, and an identified clean
**already stopped** helper in the root's actual Availability Zone. Its trusted
AMI/user-data/image provenance must establish that no campaign/watchdog units or
research autostart jobs are present **before boot**. It needs SSM, Python >=3.11,
encryption-key access, enough disk for <64 MiB diagnostics, and an independently
owned Scheduler role that can stop that exact helper. The existing campaign
shutdown role must not be assumed to cover another instance. If no such helper
exists, a separately reviewed creation procedure is required; do not improvise
one or boot the campaign host instead.

The present EC2 status request failed with ConnectTimeout. Therefore helper ID,
current AZ/permissions and an independently verified timer are unresolved live
prerequisites. These commands are parameterized for those exact values, not a
claim that deployment is ready. No AWS mutation below was run.

## Bounded protection and accounting

Maximum helper compute: 15 minutes after an externally read-back shutdown guard;
maximum extraction command: 300 seconds; aim to finish within ten minutes.
Overall maintenance/reattachment allowance: 30 minutes, with one attempt and no
automatic reboot/retry. Guard delivery has service latency; an operator must also
verify stop at expiry and issue StopInstances if necessary. Preserve any failed
transfer, local diagnostics and SSM output. Never delete an evidence disk.

The reviewed **campaign** forecast already fails time and the US$60 admission
guard (see REPORT.md); this procedure has no current cost-feasibility PASS.
Do not reuse the old US$1.25 preparation reserve as new approval. Before any
maintenance, account for sunk spend, retained root/S3, helper rate/disk/IP, request
costs and a stop-latency reserve within the unchanged US$65 ceiling. If the helper
were priced at the last verified campaign compute/IP rates, 15 minutes alone
would be US$0.031175, excluding its root, requests and delays. This is only an
illustration, not a current-price quote or approved allowance. Existing 160-GiB
root retention is about US$0.505/day at the last verified .096/GiB-month rate.

## Future PowerShell control commands

Run only after all prerequisites and explicit maintenance authority are recorded.
Use one new maintenance evidence folder for metadata/small records, not a second
full archive. Stop on any command error. Save/read back every response privately.

```powershell
$ErrorActionPreference = 'Stop'
$campaignId = 'i-057344e5372faf62f'
$rootId = 'vol-09dbb42bbf607f5de'
$helperId = '<VERIFIED_STOPPED_CLEAN_HELPER_ID>'
$stopRole = '<VERIFIED_HELPER_SPECIFIC_SCHEDULER_ROLE_ARN>'
$maintenance = '<NEW_SHORT_METADATA_ONLY_EVIDENCE_DIRECTORY>'
$maintenanceDeadline = [DateTime]::UtcNow.AddMinutes(30)
# The strings above must be resolved and verified, never guessed.
function Invoke-AwsChecked {
    param([string[]]$AwsArguments)
    $operation = $AwsArguments[0..1] -join ' '
    # Expiry forbids more preparation; stopping compute and reading its state
    # remain permitted so the deadline cannot suppress emergency shutdown.
    if ([DateTime]::UtcNow -ge $maintenanceDeadline -and $operation -notin @('ec2 stop-instances','ec2 describe-instances','ec2 describe-volumes')) { throw 'MAINTENANCE_DEADLINE_STOP' }
    $result = & aws @AwsArguments --profile fyp-research --region ap-southeast-2 --cli-connect-timeout 5 --cli-read-timeout 10 --no-cli-pager
    if ($LASTEXITCODE -ne 0) { throw 'AWS_MAINTENANCE_COMMAND_FAILED_STOP' }
    return ($result -join "`n")
}
function Wait-VolumeAvailableBounded {
    $waitDeadline = [DateTime]::UtcNow.AddSeconds(60)
    do {
        $state = Invoke-AwsChecked @('ec2','describe-volumes','--volume-ids',$rootId,'--query','Volumes[0].State','--output','text')
        if ($state.Trim() -eq 'available') { return }
        Start-Sleep -Seconds 3
    } while ([DateTime]::UtcNow -lt $waitDeadline)
    throw 'VOLUME_WAIT_EXHAUSTED_PRESERVE_ATTACHMENT_STATE'
}
function Wait-HelperStoppedBounded {
    $waitDeadline = [DateTime]::UtcNow.AddSeconds(60)
    do {
        $state = Invoke-AwsChecked @('ec2','describe-instances','--instance-ids',$helperId,'--query','Reservations[0].Instances[0].State.Name','--output','text')
        if ($state.Trim() -eq 'stopped') { return }
        Start-Sleep -Seconds 3
    } while ([DateTime]::UtcNow -lt $waitDeadline)
    throw 'STOP_WAIT_EXHAUSTED_VERIFY_AND_ESCALATE_NO_REBOOT'
}
$before = Invoke-AwsChecked @('ec2','describe-instances','--instance-ids',$campaignId,$helperId,'--output','json')
$before | Set-Content -LiteralPath "$maintenance/instances-before.json" -Encoding utf8
$volume = Invoke-AwsChecked @('ec2','describe-volumes','--volume-ids',$rootId,'--output','json')
$volume | Set-Content -LiteralPath "$maintenance/root-before.json" -Encoding utf8
# REQUIRED: validate ownership tags, both instances stopped, matching actual AZ,
# /dev/sda1 root mapping and DeleteOnTermination=false; retain pristine helper
# provenance and independently verified prior master/S3 receipts. No mutation
# until those checks pass. Do not alter original root data or clone live DB state.
$guardName = 'p85-diagnostic145-helper-' + [DateTime]::UtcNow.ToString('yyyyMMddHHmmss')
$stopAt = [DateTime]::UtcNow.AddMinutes(15)
$guard = @{
  Name=$guardName; GroupName='fyp-p85-v5'; State='ENABLED'
  ScheduleExpression=('at('+$stopAt.ToString('yyyy-MM-ddTHH:mm:ss')+')')
  ScheduleExpressionTimezone='UTC'; FlexibleTimeWindow=@{Mode='OFF'}
  ActionAfterCompletion='NONE'
  Target=@{Arn='arn:aws:scheduler:::aws-sdk:ec2:stopInstances';RoleArn=$stopRole;
    Input=(@{InstanceIds=@($helperId)} | ConvertTo-Json -Compress);
    RetryPolicy=@{MaximumRetryAttempts=2;MaximumEventAgeInSeconds=60}}
}
$guard | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$maintenance/guard-request.json" -Encoding utf8
Invoke-AwsChecked @('scheduler','create-schedule','--cli-input-json',"file://$maintenance/guard-request.json") | Set-Content "$maintenance/guard-create.json"
Invoke-AwsChecked @('scheduler','get-schedule','--group-name','fyp-p85-v5','--name',$guardName) | Set-Content "$maintenance/guard-readback.json"
# REQUIRED before boot: compare ENABLED, UTC absolute time, helper ID, role,
# retry policy and verified role permission. If insufficient preparation time
# remains, stop; do not reset this timer automatically.
Invoke-AwsChecked @('ec2','detach-volume','--volume-id',$rootId,'--instance-id',$campaignId) | Set-Content "$maintenance/detach.json"
Wait-VolumeAvailableBounded
Invoke-AwsChecked @('ec2','attach-volume','--volume-id',$rootId,'--instance-id',$helperId,'--device','/dev/sdf') | Set-Content "$maintenance/attach.json"
# Re-read guard and attachment; require at least ten minutes until stopAt.
if ([DateTime]::UtcNow.AddMinutes(10) -ge $stopAt) { throw 'GUARD_TOO_CLOSE_NO_BOOT' }
Invoke-AwsChecked @('ec2','start-instances','--instance-ids',$helperId) | Set-Content "$maintenance/helper-start.json"
```

The helper's clean root boots; the attached campaign filesystem is not its OS.
Before reading, use SSM on the helper to run the commands below with a 300-second
command timeout. Save the AWS-RunShellScript request as a JSON body file, dispatch
once using `aws ssm send-command --cli-input-json file://<request.json>`, and retain
`get-command-invocation` output. The script is the prepared standard-library
`extract_required.py` in this directory: transfer only that small reviewed script
using the SSM request body, never install dependencies. Its exact file hash must
be recorded in the maintenance request.

## Future helper Linux command body

```bash
set -euo pipefail
test "$(systemctl list-unit-files 'fyp-phase8-*' --no-legend | wc -l)" -eq 0
# Resolve the actual NVMe device by EBS SERIAL, never by enumeration order.
dev=$(lsblk -dn -o NAME,SERIAL | awk '$2=="vol09dbb42bbf607f5de" {print "/dev/"$1}')
test -n "$dev"; test "$(printf '%s\n' "$dev" | wc -l)" -eq 1
# Require exactly one ext4 filesystem on this device's partition tree.
part=$(lsblk -nr -o PATH,FSTYPE "$dev" | awk '$2=="ext4" {print $1}')
test -n "$part"; test "$(printf '%s\n' "$part" | wc -l)" -eq 1
mkdir -p /mnt/p85-diagnostic-root
# noload prevents ext4 journal replay on the evidence filesystem.
mount -t ext4 -o ro,noload,nodev,nosuid,noexec "$part" /mnt/p85-diagnostic-root
findmnt -no SOURCE,OPTIONS /mnt/p85-diagnostic-root
findmnt -no OPTIONS /mnt/p85-diagnostic-root | tr ',' '\n' | grep -qx ro
root=/mnt/p85-diagnostic-root
pause="$root/var/lib/p8-continuation-v9/run/pause.json"
sha256sum "$pause" > /var/tmp/p145-pause-before.sha256
python3 -c 'import json,sys;x=json.load(open(sys.argv[1]));assert x["reason"]=="DRIVER_FAILURE";assert x["at"]=="2026-10-10T18:06:53.908883+00:00"' "$pause"
archive="$root/var/lib/p8-continuation-v9/backup/0145/attempt-1791655613965046913.tar.gz"
# This hash/size/member verifier writes ONLY small required records to helper.
timeout 300 python3 /var/tmp/extract_required.py "$archive" /var/tmp/p145-required
sha256sum -c /var/tmp/p145-pause-before.sha256
tar -C /var/tmp -czf /var/tmp/p145-required.tar.gz p145-required p145-pause-before.sha256
sha256sum /var/tmp/p145-required.tar.gz
umount /mnt/p85-diagnostic-root
```

Required output: original failure type/detail/full traceback, HTTP observations,
checkpoints, slot ledger/schema, original manifest, exact member hashes and full
original archive hash. Independently verify the master pause/counts via a
read-only SQLite transaction if needed. Do not confuse current helper logs with
the original exception. Package only diagnostic records; retain originals in place.

Use a single version-pinned S3 PUT for this small derived bundle to the existing
owned observations prefix (not a research slot); record checksum, bytes and VersionId.
Ambiguous PUT: retain file/reservation, reconcile read-only, do not automatically
repeat PUT. Retain helper root if independent readback cannot be verified; stop
compute and escalate retention instead of deleting the only diagnostic copy.
S3 local readback can still fail on this network; an SSM stdout copy of the small
failure/notice excerpt is supplementary, not a substitute for hashed raw records.

## Mandatory shutdown and original mapping restoration

Stop helper explicitly even if extraction fails; do not depend only on Scheduler.

```powershell
Invoke-AwsChecked @('ec2','stop-instances','--instance-ids',$helperId) | Set-Content "$maintenance/helper-stop.json"
Wait-HelperStoppedBounded
Invoke-AwsChecked @('ec2','detach-volume','--volume-id',$rootId,'--instance-id',$helperId) | Set-Content "$maintenance/helper-detach.json"
Wait-VolumeAvailableBounded
Invoke-AwsChecked @('ec2','attach-volume','--volume-id',$rootId,'--instance-id',$campaignId,'--device','/dev/sda1') | Set-Content "$maintenance/campaign-reattach.json"
Invoke-AwsChecked @('ec2','modify-instance-attribute','--instance-id',$campaignId,'--block-device-mappings','[{"DeviceName":"/dev/sda1","Ebs":{"DeleteOnTermination":false}}]')
Invoke-AwsChecked @('ec2','describe-instances','--instance-ids',$campaignId,$helperId) | Set-Content "$maintenance/instances-after.json"
Invoke-AwsChecked @('ec2','describe-volumes','--volume-ids',$rootId) | Set-Content "$maintenance/root-after.json"
```

Read back both STOPPED states, original root attachment, DeleteOnTermination=false,
pause hash and independent diagnostic copy. If any step fails, preserve disks,
stop compute, record exact attachment/resource state and escalate. No root/evidence
deletion and no campaign boot. The 48-hour retained-root decision remains
**2026-10-13T16:04:13.525847Z**; maintenance does not extend it or the study deadline.

**Not a continuation authorization:** diagnose the original cause first; a
demonstrated defect would need its own narrow reviewed version and focused
checks. No corrective candidate is justified by present retrieval failures.
