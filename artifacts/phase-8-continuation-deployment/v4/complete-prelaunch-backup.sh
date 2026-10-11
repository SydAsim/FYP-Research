set -euo pipefail
umask 077
cd /opt/fyp-phase8-combined-v4
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B - <<'PY'
import hashlib,json,shutil,sqlite3,sys,tarfile,time
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import Journal,guard,hash_file,read,utc,write_new
from handover import ContinuationAuthority,closed_boundary,verify_imported_first,verify_members
from storage import ObjectProof,S3Cloud,upload,verify_local
from postflight import recover
from transport import S3Store
from research.execution_linux_v1.platform import host
root=Path('/var/lib/p8-combined-v4/run');dep=root.parent/'deployment';owner=Path('/var/lib/fyp-owner');runtime=Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'
a=ContinuationAuthority(root,read(root/'run.json'));a.verify(prelaunch=True);verify_imported_first(root)
j=Journal(root);j.verify();rows=j.rows();closed_boundary(rows,read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows'])
if rows[38]['execution_id']!='01a11705-11f0-73c0-af15-dd9f1d590b08' or rows[38]['state']!='PLANNED' or read(root/'pause.json')['reason']!='CONTINUATION_REVIEW_REQUIRED':raise ValueError('PREPARATION_BOUNDARY_OR_PAUSE_DRIFT')
failed=list((root.parent/'backup').glob('final-*'))
if len(failed)!=1 or not failed[0].is_dir() or (failed[0]/'manifest.json').exists():raise ValueError('UNEXPECTED_PREPARATION_FAILURE_STATE')
j.event('PREPARATION_BACKUP_FAILURE_RETAINED',reason='Operational helper invoked final_backup before readiness existed',failed_directory=str(failed[0]),driver_calls=0,protocol_changed=False)
cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/');store=S3Store('fyp-research')
proofs=read(runtime/'retained-slot-proofs.json')
for obj in proofs:cloud.verify(ObjectProof.model_validate(obj['cloud']))
cloud.verify(ObjectProof.model_validate(read(runtime/'stopped-boundary-reference.json')))
sample=host(root,root.parent/'backup');sample.update(working_bytes=0,backup_bytes=0);cloud_bytes=cloud.inventory()
guard(a.policy,sample,utc(),cloud_bytes,extra_bytes=a.policy.slot_capacity_reserve_bytes)
probe=ObjectProof.model_validate(cloud.find(cloud.prefix+'combined-v4/deployment/permission-probe.json',hash_file(dep/'permission-probe.json'),(dep/'permission-probe.json').stat().st_size).model_dump())
cloud.verify(probe)
folder=root.parent/'backup'/('prelaunch-attempt-'+str(time.time_ns()));folder.mkdir(exist_ok=False)
with j.connect() as source,sqlite3.connect(folder/'campaign.sqlite3') as target:
 source.backup(target)
 if target.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('PRELAUNCH_LEDGER_CORRUPTION')
for n in ('run.json','bindings.json','binding-seal.json','cloud.json','host-clock.json','handover.json','saved-identities.json','historical-evidence.tar.gz'):
 shutil.copyfile(root/n,folder/n)
for prefix,names in [('receipts',('REVIEW_ACCEPTED','FREEZE','LAUNCH')),('combined-v4-receipts',('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'))]:
 d=folder/'public-authority'/prefix;d.mkdir(parents=True)
 for n in names:shutil.copyfile(owner/prefix/(n+'.json'),d/(n+'.json'))
shutil.copytree(root/'backups',folder/'backups');shutil.copyfile(dep/'source-ready.json',folder/'source-ready.json')
write_new(folder/'manifest.json',{'kind':'PRELAUNCH_CLOSED38_MASTER_NOT_EXECUTION','postgres_dumps':False,'files':{p.relative_to(folder).as_posix():hash_file(p) for p in folder.rglob('*') if p.is_file()}})
archive=folder.with_suffix('.tar.gz')
with tarfile.open(archive,'x:gz') as t:t.add(folder,arcname='slot')
verify_local(archive,hash_file(archive));p=upload(j,cloud,a.policy,archive);cloud.verify(p)
back=recover(p,root.parent/'prelaunch-readback',store);verify_members(back/'slot');verify_imported_first(back/'slot')
j.event('V4_PRELAUNCH_BACKUP_VERIFIED',proof=p.model_dump(),failed_preparation_attempt_preserved=True)
write_new(dep/'import-and-backup-readiness.json',{'status':'PASS','at_utc':utc().isoformat(),'instance_id':read(dep/'actual-deployment-binding.json')['instance_id'],'identities':1500,'backed_up':38,'planned':1462,'next_sequence':39,'next_arm':'B3','next_attempt':1,'next_execution_id':rows[38]['execution_id'],'driver_calls':0,'old_live_state_restored':False,'original_backups':[x['cloud'] for x in proofs],'boundary_backup':read(runtime/'stopped-boundary-reference.json'),'prelaunch_backup':p.model_dump(),'permission_probe':probe.model_dump(),'host':sample,'cloud_bytes':cloud_bytes,'owner_mode':'0700/0600','operational_clock_reset':False,'original_deadline':a.policy.stop_at.isoformat(),'cost_at_now_usd':a.policy.committed_cost(utc()),'failed_initial_preparation_directory':str(failed[0]),'reviewed_pre_readiness_snapshot_procedure_used':True})
print(json.dumps({'status':'PASS','backed_up':38,'planned':1462,'next_sequence':39,'prelaunch_backup':p.model_dump(),'failed_attempt_preserved':True,'driver_calls':0}))
PY
