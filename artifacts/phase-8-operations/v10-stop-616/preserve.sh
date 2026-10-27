set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v10
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v10:/opt/fyp-phase8-continuation-v10/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v10/.venv-transport/lib/python3.12/site-packages
timeout --signal=TERM --kill-after=5s 240s .venv/bin/python -B - <<'PRESERVE'
import json,collections,subprocess,sys,shutil,time,sqlite3,hashlib,tarfile
from datetime import timedelta,datetime
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,write_new,hash_file,utc,Journal,guard
from closed145 import snapshot
from handover import ContinuationAuthority
from storage import S3Cloud,final_backup,upload
from postflight import recover
from runner import meter
root=Path('/var/lib/p8-continuation-v9/run')
rows,notices=snapshot(root/'campaign.sqlite3')
assert collections.Counter(r['state'] for r in rows)=={'BACKED_UP':616,'PLANNED':884}
pause=read(root/'pause.json');assert pause=={'reason':'DRIVER_FAILURE','at':'2026-10-16T13:49:16.475780+00:00'}
assert rows[616]['execution_id']=='01a11705-11f2-7276-8d5f-0277ced1a5f5'
units=['fyp-phase8-campaign.service','fyp-phase8-watchdog.service']
for unit in units:
    text=(Path('/etc/systemd/system')/unit).read_text()
    assert '/opt/fyp-phase8-continuation-v10/' in text and '--root /var/lib/p8-continuation-v9/run' in text
assert subprocess.run(['systemctl','show',units[0],'--property=MainPID','--value'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()=='0'
out=Path('/var/lib/p8-continuation-v10/deployment')/('stop-616-'+str(time.time_ns()));out.mkdir(mode=0o700)
for name,args in {
    'units-before':['systemctl','show',*units,'--property=Id,ActiveState,SubState,MainPID,Result,ExecStart'],
    'campaign-journal':['journalctl','-u',units[0],'-u',units[1],'--since','2026-10-16 13:35:00 UTC','--no-pager','-o','short-iso-precise'],
    'containers':['docker','ps','-a','--format','{{.Names}} {{.Status}}']}.items():
    p=subprocess.run(args,capture_output=True,text=True,check=True,timeout=20)
    write_new(out/(name+'.json'),{'stdout':p.stdout,'stderr':p.stderr})
subprocess.run(['systemctl','stop',units[1]],check=True,timeout=20)
assert all(subprocess.run(['systemctl','show',u,'--property=MainPID','--value'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()=='0' for u in units)
assert snapshot(root/'campaign.sqlite3')[0]==rows and read(root/'pause.json')==pause
write_new(out/'read-only-ledger.json',{'rows':rows})
write_new(out/'historical-notices.json',{'notices':notices})
with sqlite3.connect((root/'campaign.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as incoming:
    with sqlite3.connect(out/'consistent-master.sqlite3') as target:incoming.backup(target)
for name in ['pause.json','host-clock.json']:shutil.copyfile(root/name,out/name)
a=ContinuationAuthority(root,read(root/'run.json'));a.verify()
cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/')
inventory=cloud.inventory()
sample=meter(root);at=utc();guard(a.policy,sample,at,inventory)
receipts=[]
for r in rows[:616]:
    p=root/'backups'/(r['execution_id']+'.json');assert hash_file(p)==r['backup_hash']
    proof=read(p);assert proof['execution_id']==r['execution_id'] and proof['sha256']==proof['cloud']['sha256']
    receipts.append(proof)
from storage import ObjectProof
cloud.verify(ObjectProof.model_validate(receipts[-1]['cloud']))
last=Path(receipts[-1]['local']);assert hash_file(last)==receipts[-1]['sha256']
with tarfile.open(last) as tf:
    manifest=json.load(tf.extractfile('slot/manifest.json'))
    for name in ['executions/'+rows[615]['execution_id']+'/export.json','ledger.sqlite3','setup_app.sql.gz','setup_truth.sql.gz']:
        f=tf.extractfile('slot/'+name);assert f is not None
        assert hashlib.file_digest(f,'sha256').hexdigest()==manifest['files'][name],name
remaining=884
accepted_hours_per_slot=262.31642189586114/1355
completion=at+timedelta(hours=remaining*accepted_hours_per_slot+2.5)
uncertain=completion+timedelta(hours=24)
extra_storage=0.32696506334326947
cloud_projection=inventory+remaining*60*1024**2+1024**3
backup_projection=sample['backup_bytes']+remaining*60*1024**2+1024**3
forecast={'at':at.isoformat(),'original_start':a.policy.host_started_at.isoformat(),'stop_at':a.policy.stop_at.isoformat(),'remaining':remaining,'accepted_hours_per_slot':accepted_hours_per_slot,'remaining_execution_hours':remaining*accepted_hours_per_slot,'preparation_shutdown_hours':2.5,'uncertainty_hours':24,'completion_at':completion.isoformat(),'uncertainty_completion_at':uncertain.isoformat(),'deadline_shortfall_hours':max(0,(uncertain-a.policy.stop_at).total_seconds()/3600),'completion_forecast_usd':a.policy.committed_cost(completion)+extra_storage,'uncertainty_forecast_usd':a.policy.committed_cost(uncertain)+extra_storage,'full_deadline_forecast_usd':a.policy.committed_cost(a.policy.stop_at)+extra_storage,'admission_guard':70,'total_ceiling':75,'cloud_bytes_all_versions':inventory,'cloud_projection_bytes':cloud_projection,'backup_bytes':sample['backup_bytes'],'backup_projection_bytes':backup_projection,'cap_bytes':80*1024**3,'sample':sample,'actual_billed_spend':'NOT_QUERIED; accepted conservative elapsed-clock accounting retained','time_gate':uncertain<=a.policy.stop_at,'admission_forecast_gate':a.policy.committed_cost(uncertain)+extra_storage<70,'storage_projection_gate':cloud_projection<80*1024**3 and backup_projection<80*1024**3,'current_live_guard':'PASS; progress-script required_free_bytes is a static prelaunch comparison'}
write_new(out/'feasibility.json',forecast)
archive=final_backup(Journal(root),root.parent/'backup')
proof=upload(Journal(root),cloud,a.policy,archive)
readback=root.parent/'backup'/('stop616-readback-'+str(time.time_ns()))
recovered=recover(proof,readback)
assert snapshot(recovered/'slot/campaign.sqlite3')[0]==rows
assert read(root/'pause.json')==pause and snapshot(root/'campaign.sqlite3')[0]==rows
summary={'status':'CLOSED616_PRESERVED_NO_ADMISSION','at':utc().isoformat(),'counts':{'BACKED_UP':616,'PLANNED':884},'next':rows[616],'pause':pause,'pause_sha256':hash_file(root/'pause.json'),'master_backup':proof.model_dump(),'readback_record':str(readback/'postflight-verified.json'),'readback_sha256':hash_file(readback/'postflight-verified.json'),'all616_receipt_bindings_verified':True,'slot616_archive_and_required_members_verified':True,'slot616_pinned_cloud_verified':True,'feasibility':forecast,'diagnostic_directory':str(out),'units_quiesced':True,'host_shutdown_pending':True}
write_new(out/'summary.json',summary)
write_new(out/'manifest.json',{'files':{p.relative_to(out).as_posix():hash_file(p) for p in out.rglob('*') if p.is_file()}})
print(json.dumps(summary))
PRESERVE
