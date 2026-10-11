#!/bin/bash
set -euo pipefail
umask 077
cd /opt/fyp-phase8-linux-v1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
.venv/bin/python -B - <<'PY'
import hashlib,json,shutil,sqlite3,sys,tarfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-review-freeze/v2'))
from controls import Journal,guard,hash_file,read,utc,write_new
from runner import cloud_for,meter,verify_host_timer,verify_run
from storage import upload,verify_local
root=Path('/var/lib/p8/run'); journal=Journal(root); authority=verify_run(root)
verify_host_timer(root)
rows=journal.rows()
if len(rows)!=1500 or any(r['state']!='PLANNED' for r in rows): raise ValueError('MAIN_ADMITTED_BEFORE_READINESS')
if (root/'pause.json').exists(): raise ValueError('PRELAUNCH_PAUSE_RETAIN_AND_REVIEW')
cloud=cloud_for(root); sample=meter(root); cloud_bytes=cloud.inventory()
guard(authority.policy,sample,utc(),cloud_bytes,extra_bytes=authority.policy.slot_capacity_reserve_bytes)
expected={'launch-policy.json':'80831c99b3def500b86335ef038142148f8f04025ca530e38673de2ef573e61d','receipts/REVIEW_ACCEPTED.json':'95e337416773c6ed99cc8bc1caa82736c30ee829c606317a8837b51c4c0d1461','receipts/FREEZE.json':'0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2','receipts/LAUNCH.json':'35b9d06c9676baadffd4561bf2489b2bc1b08afce28fca5f1e259657f841bcd9'}
owner=Path('/var/lib/fyp-owner')
for name,digest in expected.items():
    if hash_file(owner/name)!=digest: raise ValueError('ORIGINAL_RECEIPT_BYTES_DRIFT: '+name)
if owner.stat().st_mode&0o777!=0o700 or (owner/'owner.key').stat().st_mode&0o777!=0o600: raise ValueError('PRIVATE_OWNER_PERMISSIONS')
folder=Path('/var/lib/p8/backup/prelaunch-attempt1');folder.mkdir(exist_ok=False)
with journal.connect() as source,sqlite3.connect(folder/'campaign.sqlite3') as target:
    source.backup(target)
    if target.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('PRELAUNCH_SQLITE_BACKUP')
for name in ('run.json','bindings.json','binding-seal.json','cloud.json','host-clock.json'):shutil.copyfile(root/name,folder/name)
for name in expected:
    dest=folder/'owner-public'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(owner/name,dest)
for name in ('dependencies-ready.json','source-download.json','image-identities.json','preinitialize-readiness.json'):
    shutil.copyfile(Path('/var/lib/p8-deployment')/name,folder/name)
files={p.relative_to(folder).as_posix():hash_file(p) for p in folder.rglob('*') if p.is_file()}
write_new(folder/'manifest.json',{'kind':'PRELAUNCH_MASTER_BACKUP_NOT_EXECUTION_OR_COMPLETION','postgres_dumps':False,'files':files})
archive=folder.with_suffix('.tar.gz')
with tarfile.open(archive,'x:gz') as f:f.add(folder,arcname='slot')
digest=hash_file(archive);verify_local(archive,digest)
proof=upload(journal,cloud,authority.policy,archive);cloud.verify(proof)
write_new(Path('/var/lib/p8-deployment/prelaunch-backup.json'),{'classification':'PRELAUNCH_NOT_SCIENTIFIC_OUTCOME','local':str(archive),'sha256':digest,'cloud':proof.model_dump()})
journal.event('PRELAUNCH_BACKUP_VERIFIED',proof=proof.model_dump())
write_new(Path('/var/lib/p8-deployment/final-readiness.json'),{'status':'PASS','at_utc':utc().isoformat(),'run_id':authority.policy.run_id,'operational_clock_start_utc':authority.policy.host_started_at.isoformat(),'deadline_utc':authority.policy.stop_at.isoformat(),'host':sample,'cloud_bytes_before_backup':cloud_bytes,'backup':proof.model_dump(),'source_and_receipt_chain':'PASS','original_receipt_file_hashes':expected,'active_independent_timers':'PASS','serial_originals_reserved':len(rows),'main_executions_admitted':0,'pause_present':False,'estimated_committed_usd_now':authority.policy.committed_cost(utc())})
print(json.dumps(read(Path('/var/lib/p8-deployment/final-readiness.json'))))
PY
systemctl is-active fyp-phase8-hardstop.timer fyp-phase8-watchdog.service
printf '%s\n' VERIFIED_READY_FOR_SEPARATE_MAIN_SERVICE_START
