set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v7
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v7:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
timeout --signal=TERM --kill-after=5s 240s .venv/bin/python -B - <<'PRESERVE'
import json,collections,subprocess,sys,shutil,tarfile,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,write_new,hash_file,utc,Journal
from handover import ContinuationAuthority,ro_rows
from storage import S3Cloud,final_backup,upload
from postflight import recover
from transport import S3Store,Receipt
root=Path('/var/lib/p8-continuation-v7/run');dep=root.parent/'deployment'
rows=ro_rows(root)
assert collections.Counter(r['state'] for r in rows)=={'BACKED_UP':120,'PLANNED':1380}
pause=read(root/'pause.json');assert pause['reason']=='WALL_CLOCK_BACKWARD_STOP_ADMISSIONS'
before=subprocess.run(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','--property=Id,ActiveState,SubState,MainPID,Result'],check=True,capture_output=True,text=True,timeout=10).stdout
assert subprocess.run(['systemctl','show','fyp-phase8-campaign.service','--property=MainPID','--value'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()=='0'
out=dep/('stop-120-preservation-'+str(time.time_ns()));out.mkdir(mode=0o700)
write_new(out/'units-before-quiesce.json',{'at_utc':utc().isoformat(),'output':before})
subprocess.run(['systemctl','stop','fyp-phase8-watchdog.service'],check=True,timeout=20)
assert subprocess.run(['systemctl','show','fyp-phase8-watchdog.service','--property=MainPID','--value'],check=True,capture_output=True,text=True,timeout=10).stdout.strip()=='0'
assert read(root/'pause.json')==pause and ro_rows(root)==rows
for name,args in {
'campaign-journal':['journalctl','-u','fyp-phase8-campaign.service','-u','fyp-phase8-watchdog.service','--since','2026-10-09 23:05:00 UTC','--no-pager','-o','short-iso-precise'],
'clock-journal':['journalctl','-u','systemd-timesyncd.service','-u','chrony.service','-u','chronyd.service','--since','2026-10-09 16:00:00 UTC','--no-pager','-o','short-iso-precise'],
'time-status':['timedatectl','show'],
'containers':['docker','ps','-a','--format','{{.Names}} {{.Status}}'],
'units-after':['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','fyp-phase8-hardstop.timer','--property=Id,ActiveState,SubState,MainPID,Result']}.items():
    result=subprocess.run(args,capture_output=True,text=True,timeout=20)
    write_new(out/(name+'.json'),{'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
for name in ('host-clock.json','pause.json'):shutil.copyfile(root/name,out/name)
write_new(out/'read-only-ledger.json',{'rows':rows})
a=ContinuationAuthority(root,read(root/'run.json'));a.verify()
cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/');store=S3Store('fyp-research')
proofs=[]
for r in rows[:120]:
    file=root/'backups'/(r['execution_id']+'.json');assert hash_file(file)==r['backup_hash']
    proof=read(file);assert proof['execution_id']==r['execution_id'] and proof['sha256']==proof['cloud']['sha256']
    proofs.append(Receipt.model_validate(proof['cloud']))
with ThreadPoolExecutor(max_workers=4) as pool:
    futures=[pool.submit(store.head,proof) for proof in proofs]
    for f in futures:f.result()
archive=final_backup(Journal(root),root.parent/'backup')
master=upload(Journal(root),cloud,a.policy,archive)
recovered=recover(master,root.parent/'backup'/('stopped-120-readback-'+str(time.time_ns())))
assert ro_rows(recovered/'slot')==rows
shutil.copyfile(archive,out/'verified-master.tar.gz')
summary={'status':'PRESERVED_CLOSED_120_NO_ACTIVE','at_utc':utc().isoformat(),'counts':{'BACKED_UP':120,'PLANNED':1380},'pause':pause,'next':rows[120],'all_original_rows_preserved':True,'all_120_pinned_backups_verified':True,'master_backup':master.model_dump(),'full_readback':'PASS','host_still_running_pending_stop':True,'no_replay':True,'no_source_change':True}
write_new(out/'summary.json',summary)
write_new(out/'manifest.json',{'kind':'STOPPED_BOUNDARY_PRESERVATION_NOT_NEW_RESEARCH_OUTCOME','files':{p.relative_to(out).as_posix():hash_file(p) for p in out.rglob('*') if p.is_file()}})
inspection=out.with_suffix('.tar.gz')
with tarfile.open(inspection,'x:gz') as target:target.add(out,arcname='inspection')
assert cloud.inventory()+inspection.stat().st_size<a.policy.cloud_limit_bytes
proof=cloud.put(inspection,cloud.prefix+'observations/'+hash_file(inspection)+'.tar.gz');cloud.verify(proof)
print(json.dumps({'summary':summary,'inspection':proof.model_dump()}))
PRESERVE
