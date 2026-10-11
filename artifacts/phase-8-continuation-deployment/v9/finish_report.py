"""Retain exact authority, gate proofs and actual admission; no campaign writes."""
from __future__ import annotations
import hashlib
import json
from datetime import UTC,datetime
from pathlib import Path
from ops import HERE
from controls import hash_file,read,write_new

def records(name: str) -> list[dict]:
    response=read(HERE/name)['result']
    assert response['Status']=='Success' and response['ResponseCode']==0,name
    return [json.loads(line) for line in response['StandardOutputContent'].splitlines() if line.startswith('{')]

def main() -> None:
    data=read(HERE/'deployment-manifest.json');pkg=data['candidate'];freeze=data['freeze']
    progress=records('progress-admission-v2-status1-result.json')[0]
    admitted=next(e for e in progress['latest_admissions'] if e['execution_id']==data['next_execution_id'])
    immediate=next(e for e in records('launch-service-lf-status1-result.json') if e.get('both_backups_verified'))
    assert progress['pause'] is None and admitted['kind']=='ADMITTED'
    assert read(HERE/'preparation-guard-retired-after-admission.json')['status']=='PASS'
    timers=next(e for e in records('verify-preparation-timers-status1-result.json') if e.get('owned_preparation_timers_disabled'))
    authority=read(HERE/'human-acceptance.json')
    assert authority['conditional_human_authorization'] and not authority['personal_review_of_unseen_final_code_claimed']
    root=HERE.parents[1]/'phase-8-continuation-freeze/v9'
    assert hash_file(root/'freeze-manifest.json')==freeze['freeze_manifest_sha256']
    qualification=read(HERE.parents[1]/'phase-8-continuation/v9/qualification-result.json')
    assert qualification['status']=='PASS'
    final={'status':'ACTUAL_CONTINUATION_STARTED','at_utc':datetime.now(UTC).isoformat(),
      'run_id':progress['run_id'],'host_id':'i-057344e5372faf62f','host_state':'running',
      'root_volume':'vol-09dbb42bbf607f5de','root_deleted':False,'package':pkg,'freeze':freeze,
      'actual_admission':admitted,'sequence121':progress['sequence121'],'counts_at_snapshot':progress['counts'],
      'snapshot_at':progress['at_utc'],'pause':None,'services':progress['services'],
      'backups':{'prelaunch':progress['prelaunch_backup'],'complete':progress['complete_backup'],
                 'independent_readbacks':'PASS','120_original_references':'PASS'},
      'preparation_stop':'DISABLED_AND_READ_BACK_ONLY_AFTER_ACTUAL_ADMISSION',
      'owned_local_preparation_timers':timers,'original_absolute_deadline':progress['deadline'],
      'admission_guard_usd':60,'total_ceiling_usd':65,'cloud_and_dedicated_local_caps_GiB':80,
      'projected_cost_at_admission':immediate['conservative_projected_usd'],
      'projected_shutdown_utc':immediate['projected_shutdown_utc'],
      'capacity_projection_at_admission_bytes':immediate['live_capacity_projection_bytes'],
      'live_disk_and_ram_before_admission':immediate['host'],
      'windows_or_analysis_or_application_changes':0,'original_replays':0,
      'historical_evidence_deleted':False,'new_control_tests':8,'reused_v8_distinct_checks':18,
      'actual_new_execution_not_yet_graded_or_backed_up':True,
      'private_key_included':False,'personal_unseen_code_review_claimed':False}
    write_new(HERE/'final-status.json',final)
    write_new(HERE/'document-label-discrepancies.json',{
      'candidate_inventory_flags':'Preserved prefreeze candidate flags; signed freeze/launch receipts govern actual authorization.',
      'deployment_order_intro':'Inherited exact-hash review wording predates latest conditional human authorization. The verbatim instruction recorded in acceptance-statement.json governs; no personal unseen-code review claimed.',
      'external_binding_kind':'Copied EXPLICIT_HUMAN_AUTHORIZED_RETAINED_HOST_V7_DEPLOYMENT label retained. Its concrete package/archive/freeze/overlay hashes, host, 120/1380 counts and sequence121 bind v9. No V7 replay or alternate authority inferred.',
      'other_legacy_labels':'Existing v6 backup headings, CLOUD_30GIB_LIMIT error label and attempt3 operational filenames are retained. Executable caps are the signed v9 80GiB overlay; no silent historical relabeling.'})
    pre=progress['prelaunch_backup'];complete=progress['complete_backup']
    command="& '"+str(HERE/'Check-Progress.ps1')+"'"
    report=f'''# v9 deployment — actual sequence 121 continuation

Run `{progress['run_id']}` actually admitted **sequence121/P1/attempt1** at
**{admitted['at']}** on retained host `i-057344e5372faf62f`.
Saved execution: `{data['next_execution_id']}`. Its original 600-second window
ends **{progress['sequence121']['deadline']}**. At **{progress['at_utc']}**:
**120 BACKED_UP / 1 RUNNING / 1,379 PLANNED**, no pause; campaign service and
watchdog running, absolute timer active. This is actual admission, not a grade
or completed backup for sequence121. The standalone service needs no Codex chat.

## Exact authority and preservation

- Package: `{pkg['package_hash']}`
- Archive SHA-256: `{pkg['archive_sha256']}`
- Freeze manifest SHA-256: `{freeze['freeze_manifest_sha256']}`
- Parent frozen v7: `3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46`
- Reused v8 package: `715881dec6368acc40d89fa0a772e8fa285f7a40018002b566fbe8b0a5eed051`

Conditional user authority was recorded verbatim, with no claim of personal
review of unseen final code. Exact archive/source closure and parent signatures
passed before freezing. Freeze verified {freeze['verified_members']} members.
New launch receipt binds genuine readiness, exact package, actual run/host,
original policy, overlay and all saved identities. Historical packages,
receipts, raw FAILED statuses/grades, sidecars and pinned S3 versions unchanged.
Imported exactly 120 closed +1,380 planned identities; no SQL restore, replay,
replacement or historical deletion. The old durable clock pause remains.

## Narrow change and checks

Five runtime differences from qualified v8: 80GiB allowed literal; versioned
operational overlay and full 80GiB monthly reserve; overlay/provenance/path
bindings in handover/closed_restart. Clock, runner, reuse preparation, refusal,
permissive-response and backup logic reused unchanged. All application,
fixture, oracle, analysis, endpoints and 600-second windows unchanged.

Eight focused pinned-Linux controls passed ({qualification['wall_seconds']:.2f}s);
v8's eighteen distinct controls and all unsuccessful attempts reused. Ruff
passed. Strict mypy passed with third-party missing-import boundary isolated;
the earlier Windows SDK import failures remain documented. No broad pilot,
research calibration, model API or dependency install was added.

Live source/dependency RECORDs/versions, old-unit ownership/quiescence, all120
local archive/member hashes and pinned S3 heads passed. Metadata handover,
permissions, RAM/disk, complete all-version inventory, paired clock samples,
original deadline and current-price/credit gates passed.

PRELAUNCH backup/readback passed before genuine readiness/new launch. COMPLETE
backup/readback then passed before admission:

- PRELAUNCH `{pre['sha256']}`, version `{pre['version_id']}`
- COMPLETE `{complete['sha256']}`, version `{complete['version_id']}`

Both proofs include required restart boundary/history and original identities.
The independent two-hour preparation Scheduler was established/read back before
boot (15:11:23UTC stop), and only verified owned obsolete guards disabled.
After actual admission, this preparation-only guard and owned local preparation
timers were disabled/read back. Original absolute timers/watchdog remain.

## Cost, storage and limits

Current-price/credit reads: FREE/ACTIVE, US$113.55 reported credits; compute
US$0.1197/hour, IPv4 US$0.005/hour, 160GiB gp3 US$0.096/GiB-month, conservative
S3 US$0.025/GiB-month. No plan upgrade. Full80GiB S3 month reserves US$2.00,
US$0.50 above the previous overlay; existing US$1.25 handover reserve included.

Unchanged reviewed remaining allowance **267.1562082777036 hours**, plus two-hour
preparation and 30-minute shutdown, projected **{immediate['projected_shutdown_utc']}**.
Conservative projected total **US${immediate['conservative_projected_usd']:.2f}**,
including original elapsed paused time and retained-storage reserves; within
**US$60 admission / US$65 total**. Not an invoice guarantee; reporting can lag.

Actual measured live backup size superseded calibration size conservatively.
All-version/local archive projection at admission:
**{immediate['live_capacity_projection_bytes']/1024**3:.2f}GiB**, plus1GiB reserve,
below80GiB. Source/temporary/evidence allowances and doubled ledger growth kept.
Actual free disk before admission **{immediate['host']['system_free_bytes']/1024**3:.2f}GiB**;
available RAM **{immediate['host']['available_memory_bytes']/1024**3:.2f}GiB**.
The maximum measured raw payload for all remaining slots projects35.67GiB working
growth including2GiB allowance; full50GiB working cap remains unchanged. Initial
simultaneous-cap and doubled-raw-payload stress estimates failed and are retained.
Larger future payloads can still force a safe pause before completion; passing
checks do not guarantee a defect-free campaign. No caps grow automatically.

Stop deadline remains **22 October2026 15:24:23.810674UTC**. Admission cutoff,
disk20/10GiB, RAM2/1GiB, working50GiB, 1GiB reservation, eight reconciliation
**attempts** and thirty drain **passes** unchanged. Retained root protected;
ongoing retention beyond reviewed reserves requires a decision. Pause alone
does not stop compute; existing preservation/operator shutdown and absolute
timers remain. No new automatic pause-shutdown policy is claimed.

## Retained failures and operational notes

Retained initial simultaneous-cap stress assertion; doubled raw-payload
sensitivity; Windows SDK static-import failure; one malformed local Python
quoting command; one invalid diagnostic SSM poll; external Bash CRLF failure.
The failed launch wrapper returned before any Python gate, pause release or
service start. A separate LF transport copy preserved the failed wrapper and
re-executed every gate; frozen source unchanged. No campaign outcome was replaced.
Local/host launch receipt raw hashes differ through line endings; canonical
signed content is identical and the host bytes are pinned in COMPLETE backup.
Other preserved heading/label discrepancies are explicit in
`document-label-discrepancies.json`; they do not override signed authority.

## Progress command

```powershell
{command}
```

This command passed from a normal PowerShell terminal. It only reads AWS/ledger
state; it cannot start the host, clear a pause or admit/replay an execution.
On a later failed safety/evidence gate preserve and use the existing bounded
shutdown procedure. Do not patch frozen code or restart through a durable pause.
'''
    with (HERE/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
    write_new(HERE/'deployment-evidence-inventory.json',{
      'kind':'ACTUAL_V9_DEPLOYMENT_EVIDENCE','at_utc':datetime.now(UTC).isoformat(),
      'files':{p.relative_to(HERE).as_posix():hash_file(p) for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'},
      'private_key_included':False,'frozen_candidate_changed':False})
    print(json.dumps({k:final[k] for k in ('status','host_state','actual_admission','counts_at_snapshot','projected_cost_at_admission','original_absolute_deadline')},indent=2))

if __name__=='__main__':main()
