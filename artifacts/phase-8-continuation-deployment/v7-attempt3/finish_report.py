"""Save actual admission and readiness provenance; no campaign mutation."""
import hashlib,json
from pathlib import Path
from datetime import UTC,datetime
from ops import HERE
from controls import read,write_new,hash_file,canonical

def json_reply(name):
    r=read(HERE/name)['result']
    assert r['Status']=='Success' and r['ResponseCode']==0
    return json.loads(r['StandardOutputContent'].splitlines()[-1])

def main():
    actual=json_reply('progress-admission-v2-status1-result.json')
    ready=json_reply('final-readiness-status1-result.json')
    before=json_reply('prelaunch-backup-status1-result.json')['proof']
    complete=json_reply('complete-backup-status1-result.json')['proof']
    controls=json_reply('install-controls-status1-result.json')
    timers=json_reply('disable-preparation-timers-status1-result.json')
    schedule=read(HERE/'preparation-guard-retired-after-admission.json')
    assert schedule['status']=='PASS' and schedule['host_state']=='running'
    assert controls['status']=='PASS' and timers['status']=='PASS'
    assert actual['counts']=={'BACKED_UP':82,'RUNNING':1,'PLANNED':1417} and actual['pause'] is None
    admission=next(x for x in actual['latest_admissions'] if x['execution_id']==actual['sequence83']['execution_id'])
    archive=HERE.parents[1]/'phase-8-continuation/v7/v7-complete-continuation-review-candidate.tar.gz'
    assert hash_file(archive)=='c5a90f1830b1b53a5cdafbe88daf909cb028382a281a10ecbac299016355d152'
    assert read(HERE/'../v7-attempt2/final-status.json')['host_state']=='stopped'
    write_new(HERE/'actual-host-launch-receipt-byte-provenance.json',{'status':'VALID_SIGNED_CANONICAL_BODY_SAME_SERIALIZATION_NEWLINE_DIFFERS','local_receipt_sha256':hash_file(HERE/'CONTINUATION_LAUNCH.json'),'host_receipt_sha256':complete['bindings']['CONTINUATION_LAUNCH.json'],'canonical_receipt_sha256':hashlib.sha256(canonical(read(HERE/'CONTINUATION_LAUNCH.json'))).hexdigest(),'explanation':'Local JSON was written with Windows line endings; text transport writes LF on Linux. Canonical signed body and signature are unchanged. Host bytes are pinned by COMPLETE backup; frozen receipts/archive unchanged.'})
    terminal=(HERE/'terminal-progress-v3-output.txt').read_text(encoding='utf-8')
    terminal_json=json.loads(terminal[terminal.index('{'):])
    assert terminal_json['pause'] is None and terminal_json['sequence83']['execution_id']==actual['sequence83']['execution_id']
    write_new(HERE/'terminal-progress-command-verified.json',{'status':'PASS','at_utc':datetime.now(UTC).isoformat(),'command':'Check-Progress-v3.ps1','output_sha256':hash_file(HERE/'terminal-progress-v3-output.txt'),'current':terminal_json})
    final={'status':'V7_ACTUAL_SEQUENCE83_ADMITTED_STANDALONE_RUNNING','recorded_at_utc':datetime.now(UTC).isoformat(),'run_id':actual['run_id'],'instance_id':'i-057344e5372faf62f','host_state':'running','package_hash':'9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817','archive_sha256':hash_file(archive),'actual_admission_utc':admission['at'],'execution':actual['sequence83'],'counts':actual['counts'],'pause':None,'campaign_and_watchdog':'ACTIVE_VERIFIED','prelaunch_backup':before,'complete_backup':complete,'owned_preparation_guards':'DISABLED_AND_READ_BACK_AFTER_ADMISSION','original_deadline':actual['deadline'],'guard_usd':60,'total_usd':65,'cloud_and_local_backup_cap_gib':60,'conservative_projected_usd_at_readiness':ready['conservative_projected_usd'],'original_82_preserved':True,'remaining_identities_and_order_unchanged':True,'driver_replay':False,'frozen_code_changes':False,'dependency_install':False,'completed_qualification_repeated':False,'evidence_deleted':False,'old_durable_pause_preserved':True,'progress_command':'Check-Progress-v3.ps1','progress_display_failure_retained':'progress-admission-status1-result.json','terminal_shell_failure_retained':'terminal-progress-failed-status1-result.json','latest_terminal_snapshot':terminal_json['at_utc']}
    write_new(HERE/'final-status.json',final)
    report=f'''# v7 preparation attempt 3 — actual continuation at sequence 83

## Actual result

Run `{actual['run_id']}` resumed through the standalone service on retained host
`i-057344e5372faf62f`. Sequence **83**, B3, attempt 1,
`{actual['sequence83']['execution_id']}`, was actually admitted at
**{admission['at']}**. Its unchanged 600-second observation deadline is
**{actual['sequence83']['deadline']}**.

Snapshot: **82 BACKED_UP; 1 RUNNING; 1,417 PLANNED; no campaign pause**.
Host, campaign service, watchdog and absolute stop timer were verified running/
active. The current execution has not completed or been backed up yet; the runner
must finish its full window, grade, verify the per-slot backup, and only then admit
the next saved identity. This report claims actual launch, not a successful study
outcome. Execution does not require an active Codex conversation.

## Narrow external order correction

The already completed v7 download/extraction was reused. No dependency install or
qualification campaign was repeated. After boot, the external wrapper first saved
the old campaign/watchdog state and unit text, checked exact unit definitions
against the owned frozen v4 run, checked source/ledger ownership, stopped both
units, and verified zero MainPID/inactive state before host readiness. The old
durable `PROTOCOL_STOP` and every original row remained unchanged. The original
live readiness check was reused without weakening it.

Only separately retained deployment scripts and attempt records were created.
The old service files were moved into an owned retained unit-history directory
before installing the reviewed frozen v7 unit definitions. No source, application,
study fixture, analysis method, original result or frozen package was patched.

Accepted v7 package: `{final['package_hash']}`.
Accepted archive SHA-256: `{final['archive_sha256']}`.
Signed freeze: `3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46`.
Original policy/receipts retain their 55/30 commitments; the accepted signed
continuation overlay applies the 60/60 operational limits explicitly.

## Live gates and evidence

1. Fresh AWS prices, FREE/ACTIVE plan, credits, ownership, permissions and
   unchanged-clock feasibility passed before boot.
2. A fresh independent preparation stop, due **18:02:52 UTC on 9 October**, was
   created/read back and region-context IAM simulation passed before boot. Only
   then were exact owned superseded preparation schedules disabled/read back.
3. Current source/archive/signature integrity, pinned Python/dependency RECORD
   hashes, all 82 local archives and pinned S3 backup versions, resource headroom,
   empty application ports and original absolute timer passed.
4. Exact metadata import passed: 82 BACKED_UP and 1,418 PLANNED, all 1,500 original
   identities/order/notices/sidecars preserved, no old live application state
   restored, no command replay. New boot segment did not reset original policy
   start/deadline. Old root remains untouched.
5. PRELAUNCH backup → independent version-specific readback passed **before** real
   readiness or new launch receipt. Real readiness and separately authorized
   actual-host launch binding then passed. COMPLETE backup/readback passed.
6. Frozen watchdog/absolute timer verification and immediate resource, capacity,
   source/authority, backup, clock and planning-feasibility gates passed before
   releasing only the accepted import pause and starting the service.
7. Actual ADMITTED notice and active service states were observed. Owned local
   preparation timers and the fresh preparation Scheduler were then disabled and
   read back. Original absolute timers/watchdog remain active.

PRELAUNCH SHA-256: `{before['cloud']['sha256']}`;
pinned S3 version `{before['cloud']['version_id']}`.
COMPLETE SHA-256: `{complete['cloud']['sha256']}`;
pinned S3 version `{complete['cloud']['version_id']}`.
Both master backups passed archive/member and continuation-closure readbacks.
All original backup references remain pinned. The two earlier failed v7
preparation attempts, their archives and partial transfers remain separate.

The first read-only progress display used a non-existent raw `stop_at` field and
failed after service activation. Its invocation/output is retained. The separate
display v2 reads the validated policy's computed deadline, and confirmed actual
admission. This did not alter an admission gate, campaign classification, window,
grade, or frozen code. New launch-receipt local/host raw file hashes differ due to
Windows/LF text serialization; the signed canonical receipt is identical. Both
raw hashes are traced separately, and the host bytes are pinned in COMPLETE
backup. No historical or frozen receipt was changed.

The reused terminal wrapper separately sent Bash syntax to default SSM /bin/sh;
that read-only query failed before reading or changing campaign data. Its command
and output remain retained. Separate terminal wrapper v3 invokes Bash explicitly;
the underlying progress body is unchanged and the exact PowerShell command passed.

## Limits and current plan

Latest immediate-prelaunch conservative projection: **US$56.25**, within the
accepted **US$60 admission guard / US$65 total ceiling**. The reviewed remaining
allowance remains **274.512683578 hours** plus two-hour preparation and 30-minute
shutdown, without reducing it to pass. Prices, previous spending, retained storage
and the earlier preparation boots were included. Estimates are not a real-time
invoice cap or an assurance of defect-free completion. The original deadline is
**22 October 2026, 15:24:23.810674 UTC**; no clock or limit reset occurred.
60-GiB cloud all-version/local-backup caps and the accepted redundant-future-
staging safeguards remain active. No evidence or root storage was deleted.

The root remains encrypted/attached/protected. The previously recorded stopped-
root retention decision bound remains 11 October 2026, 09:33:51.252814 UTC; this
continuation uses the explicitly accepted retained-host route. On a later pause,
follow the reviewed bounded preservation/shutdown and retention-decision policy.
Pause alone does not stop compute. Main outcomes, refusals, failures, timeouts and
UNKNOWN values must remain recorded and independently graded under frozen v7.

## Progress

Run the absolute-path `Check-Progress-v3.ps1` in this directory from PowerShell.
It only reads host/ledger/service state; it never starts AWS, clears a pause,
replays a command or admits an execution. Frozen runner controls remain
responsible for serial execution, full observation, verified backups and stops.
'''
    with (HERE/'REPORT.md').open('x',encoding='utf-8') as out:out.write(report)
    write_new(HERE/'deployment-evidence-inventory.json',{'at_utc':datetime.now(UTC).isoformat(),'kind':'EXTERNAL_DEPLOYMENT_EVIDENCE_NOT_NEW_RESEARCH_FREEZE','files':{p.name:hash_file(p) for p in HERE.iterdir() if p.is_file() and p.name!='deployment-evidence-inventory.json'}})
    print(json.dumps({'status':final['status'],'admitted_at':admission['at'],'counts':actual['counts'],'report':str(HERE/'REPORT.md')},indent=2))

if __name__=='__main__':main()
