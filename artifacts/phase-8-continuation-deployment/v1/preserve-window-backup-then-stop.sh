set -eu
cd /opt/fyp-phase8-continuation-v1
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B - <<'PY'
import json,sys,tarfile,shutil,subprocess
from datetime import datetime,timezone,timedelta
from pathlib import Path
from threading import Event
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-continuation/v1'))
from controls import Journal,read,utc,hash_file,write_new
from runner import verify_run,cloud_for
from storage import ObjectProof,verify_local,final_backup,upload
from postflight import recover
from transport import S3Store
from handover import verify_members
root=Path('/var/lib/p8-continuation/run');dep=root.parent/'deployment';ex='01a11705-11f0-7826-bd9d-9066d82c4452';slot=root/'slots/0002';j=Journal(root)
until=datetime.fromisoformat('2026-10-07T21:10:24.632653+00:00')
while True:
 rows=j.rows()
 if rows[1]['state']=='BACKED_UP' and (slot/'retired.json').exists() and subprocess.run(['systemctl','is-active','--quiet','fyp-phase8-campaign.service']).returncode:
  break
 if utc()>=until:raise ValueError('BACKUP_OR_RETIREMENT_NOT_COMPLETE_RETAIN_HOST_DISK_NO_GUARD_BYPASS')
 Event().wait(10)
if rows[0]['state']!='BACKED_UP' or any(r['state']!='PLANNED' for r in rows[2:]):raise ValueError('ORIGINAL_PRESERVATION_OR_ADMISSION_STOP_VIOLATED')
a=verify_run(root);cloud=cloud_for(root);store=S3Store('fyp-research')
proof=read(root/'backups'/f'{ex}.json');verify_local(Path(proof['local']),proof['sha256']);cloud.verify(ObjectProof.model_validate(proof['cloud']))
recovered=recover(proof['cloud'],root.parent/'slot2-stop-readback',store);verify_members(recovered/'slot')
export=read(slot/'executions'/ex/'export.json')
j.event('CONTINUATION_DEFECT_STOP_FULL_WINDOW_BACKUP_VERIFIED',execution_id=ex,no_retry=True)
archive=final_backup(j,root.parent/'backup');master=upload(j,cloud,a.policy,archive)
master_readback=recover(master.model_dump(),root.parent/'defect-master-readback',store);verify_members(master_readback/'slot')
record={'status':'PAUSED_DEFECT_EVIDENCE_VERIFIED','at_utc':utc().isoformat(),'run_id':a.policy.run_id,'instance_id':'i-034252c3e9b083abf','original_deadline_utc':a.policy.stop_at.isoformat(),'execution_id':ex,'raw_status':export['status'],'failure':export.get('failure'),'original_slot_deadline':rows[1]['deadline'],'remaining_PLANNED':1498,'BACKED_UP':2,'slot_backup':proof,'master_backup':master.model_dump(),'export_sha256':hash_file(slot/'executions'/ex/'export.json'),'source_unchanged':True,'no_replay':True,'pause':read(root/'pause.json'),'retention_review_due_utc':(utc()+timedelta(hours=48)).isoformat(),'fresh_disk_delete_authorized':False,'compute_shutdown_requested':True}
write_new(dep/'defect-stop-backup-verification.json',record)
ops=root.parent/'backup/continuation-deployment-evidence';ops.mkdir()
for p in dep.rglob('*'):
 if p.is_file() and p.suffix in ('.json','.sh','.log') and 'source-extract' not in p.parts:
  target=ops/'deployment'/p.relative_to(dep);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
shutil.copyfile(root/'pause.json',ops/'retained-pause.json')
write_new(ops/'manifest.json',{'kind':'OPERATIONAL_DEFECT_STOP_NOT_NEW_EXECUTION','postgres_dumps':False,'files':{p.relative_to(ops).as_posix():hash_file(p) for p in ops.rglob('*') if p.is_file()}})
ops_archive=ops.with_suffix('.tar.gz')
with tarfile.open(ops_archive,'x:gz') as outgoing:outgoing.add(ops,arcname='slot')
ops_proof=upload(j,cloud,a.policy,ops_archive)
ops_readback=recover(ops_proof.model_dump(),root.parent/'operations-stop-readback',store);verify_members(ops_readback/'slot')
write_new(dep/'operational-evidence-backup.json',ops_proof.model_dump())
print(json.dumps({'stop':record,'operations_backup':ops_proof.model_dump()}),flush=True)
PY
systemctl stop fyp-phase8-watchdog.service
/sbin/shutdown -h +1 "Authorized stop after full slot 2 window and independently verified evidence backups"

