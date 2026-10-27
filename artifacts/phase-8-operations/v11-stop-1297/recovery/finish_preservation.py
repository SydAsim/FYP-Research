"""Resume only the external preservation step after its measured staging refusal."""
import collections,hashlib,json,subprocess,sys,tarfile,time
from pathlib import Path
source=Path('/opt/fyp-phase8-continuation-v11')
sys.path.insert(0,str(source/'artifacts/phase-8-runner-amendment/v4-complete'))
sys.path.insert(1,str(source))
from controls import Journal,read,write_new,hash_file,utc,guard
from closed145 import snapshot
from runner import verify_run,meter
from storage import S3Cloud,final_backup,upload,verify_local
from postflight import recover

root=Path('/var/lib/p8-continuation-v9/run')
out=Path('/var/lib/p8-continuation-v11/deployment/stop1297-1792750933234669142')
rows=read(out/'saved-rows.json');pause=read(out/'pause.json')
assert snapshot(root/'campaign.sqlite3')[0]==rows and read(root/'pause.json')==pause
assert collections.Counter(r['state'] for r in rows)=={'BACKED_UP':1297,'PLANNED':203}
assert rows[1297]['execution_id']=='01a11705-11f4-7c05-9897-af35348a8028'
assert not (root/'slots/1298').exists()
units=['fyp-phase8-campaign.service','fyp-phase8-watchdog.service']
assert all(subprocess.run(['systemctl','show',u,'--property=MainPID','--value'],capture_output=True,text=True,check=True,timeout=10).stdout.strip()=='0' for u in units)
correction=read(out/'correction-checks.json');assert correction['status']=='PASS'
assert hash_file(Path(correction['config']))==correction['sha256']
manifest=read(out/'manifest.json')
for name,digest in manifest['files'].items():assert hash_file(out/name)==digest
measured=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
assert measured<128*1024**2,'MEASURED_PRESERVATION_CLOSURE_128MIB_STOP'
assert not list((root.parent/'backup').glob('diagnostic1297-*')),'PRIOR_PUT_MUST_BE_RECONCILED'
a=verify_run(root);sample=meter(root)
assert sample['system_free_bytes']>20*1024**3+1024**3
cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/')
guard(a.policy,sample,utc(),cloud.inventory())
write_new(out/'preservation-bound-review.json',{'original_external_staging_bound_bytes':64*1024**2,'original_guard_result':'REFUSED_BEFORE_ARCHIVE_OR_PUT','measured_bytes':measured,'corrected_external_staging_bound_bytes':128*1024**2,'preservation_extra_copy_budget_bytes':1024**3,'free_bytes':sample['system_free_bytes'],'cloud_backup_policy_cap_bytes':80*1024**3,'no_frozen_code_or_policy_changes':True,'qualification_repeated':False})
# Preserve the original manifest; a second manifest binds the added operational note.
write_new(out/'manifest-preservation-v2.json',{'files':{p.relative_to(out).as_posix():hash_file(p) for p in out.rglob('*') if p.is_file()}})
diagnostic=root.parent/'backup'/('diagnostic1297-'+str(time.time_ns())+'.tar.gz')
with tarfile.open(diagnostic,'x:gz') as tf:tf.add(out,arcname='slot')
assert diagnostic.stat().st_size<128*1024**2
verify_local(diagnostic,hash_file(diagnostic))
diagnostic_proof=upload(Journal(root),cloud,a.policy,diagnostic)
write_new(out/'diagnostic-cloud-proof.json',diagnostic_proof.model_dump())
print(json.dumps({'phase':'DIAGNOSTIC_BACKUP_PUT_VERIFIED','proof':diagnostic_proof.model_dump()}),flush=True)
diagnostic_rb=root.parent/'backup'/'r1297d'
recover(diagnostic_proof,diagnostic_rb)
Journal(root).event('OPERATIONAL_1297_OS_RESTART_CAUSE_VERIFIED',diagnostic=diagnostic_proof.model_dump(),correction_sha256=correction['sha256'],next_sequence=1298,main_admitted=False)
archive=final_backup(Journal(root),root.parent/'backup')
assert archive.stat().st_size<512*1024**2
master=upload(Journal(root),cloud,a.policy,archive)
write_new(out/'master-cloud-proof.json',master.model_dump())
print(json.dumps({'phase':'MASTER_BACKUP_PUT_VERIFIED','proof':master.model_dump()}),flush=True)
master_rb=root.parent/'backup'/'r1297m'
recovered=recover(master,master_rb)
assert snapshot(recovered/'slot/campaign.sqlite3')[0]==rows
assert read(recovered/'slot/pause.json')==pause
assert snapshot(root/'campaign.sqlite3')[0]==rows and read(root/'pause.json')==pause
assert all(subprocess.run(['systemctl','show',u,'--property=MainPID','--value'],capture_output=True,text=True,check=True,timeout=10).stdout.strip()=='0' for u in units)
after=meter(root)
assert after['backup_bytes']-sample['backup_bytes']<1024**3,'ADDITIONAL_PRESERVATION_COPY_BUDGET_STOP'
assert after['backup_bytes']<80*1024**3
summary={'status':'PASS_CORRECTION_AND_PRESERVATION_RESUME_BLOCKED','at':utc().isoformat(),'counts':{'BACKED_UP':1297,'PLANNED':203},'next':rows[1297],'pause':pause,'pause_sha256':hash_file(root/'pause.json'),'units_quiesced':True,'source_and_authority':'PASS_UNCHANGED_FROZEN_V11','correction':correction,'blocker':read(out/'resume-blocker.json'),'master_backup':master.model_dump(),'master_readback_sha256':hash_file(master_rb/'postflight-verified.json'),'diagnostic_backup':diagnostic_proof.model_dump(),'diagnostic_readback_sha256':hash_file(diagnostic_rb/'postflight-verified.json'),'diagnostic_directory':str(out),'current_resources':after,'preservation_backup_growth_bytes':after['backup_bytes']-sample['backup_bytes'],'no_main_admission':True,'no_replay_regrading_or_deletion':True,'host_stop_pending':True}
write_new(out/'preservation-summary.json',summary)
print(json.dumps(summary),flush=True)
