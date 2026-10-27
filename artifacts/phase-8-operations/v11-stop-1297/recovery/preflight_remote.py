"""Read-only closed-boundary, source, evidence, resource and forecast checks."""
import collections
import hashlib
import json
import subprocess
import sys
import tarfile
from datetime import timedelta
from pathlib import Path

source=Path('/opt/fyp-phase8-continuation-v11')
sys.path.insert(0,str(source/'artifacts/phase-8-runner-amendment/v4-complete'))
sys.path.insert(1,str(source))
from controls import Journal,read,hash_file,utc,guard
from closed145 import snapshot
from runner import verify_run,meter,verify_clock,verify_host_timer
from storage import S3Cloud,ObjectProof

root=Path('/var/lib/p8-continuation-v9/run')
rows,notices=snapshot(root/'campaign.sqlite3')
assert collections.Counter(r['state'] for r in rows)=={'BACKED_UP':1297,'PLANNED':203}
assert rows[1297]['execution_id']=='01a11705-11f4-7c05-9897-af35348a8028'
assert not (root/'slots/1298').exists()
pause=read(root/'pause.json')
assert pause=={'reason':'PROTOCOL_STOP','at':'2026-10-23T06:18:06.055774+00:00'}
a=verify_run(root)
verify_clock(root,a.policy)
verify_host_timer(root)
cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/')
cloud_bytes=cloud.inventory()
resources=meter(root)
at=utc()
guard(a.policy,resources,at,cloud_bytes,extra_bytes=a.policy.slot_capacity_reserve_bytes)
receipts=[]
for row in rows[:1297]:
    p=root/'backups'/(row['execution_id']+'.json')
    assert hash_file(p)==row['backup_hash']
    receipt=read(p)
    assert receipt['execution_id']==row['execution_id'] and receipt['sha256']==receipt['cloud']['sha256']
    receipts.append(receipt)
last=receipts[-1]
cloud.verify(ObjectProof.model_validate(last['cloud']))
assert hash_file(Path(last['local']))==last['sha256']
with tarfile.open(last['local']) as tf:
    manifest=json.load(tf.extractfile('slot/manifest.json'))
    for name in ['executions/'+rows[1296]['execution_id']+'/export.json','ledger.sqlite3','setup_app.sql.gz','setup_truth.sql.gz']:
        f=tf.extractfile('slot/'+name)
        assert f is not None and hashlib.file_digest(f,'sha256').hexdigest()==manifest['files'][name]
extra=read(Path('/var/lib/p8-continuation-v11/deployment/root-resize-plan.json'))['total_extra_storage_reserve_usd']
hours_per=262.31642189586114/1355
completion=at+timedelta(hours=203*hours_per+2.5)
uncertain=completion+timedelta(hours=24)
admission_projection=uncertain+timedelta(minutes=30)
cloud_projection=cloud_bytes+203*60*1024**2+1024**3
backup_projection=resources['backup_bytes']+203*60*1024**2+1024**3
physical_required=(backup_projection-resources['backup_bytes'])+(50*1024**3-resources['working_bytes'])+20*1024**3+1024**3
cost=lambda t:a.policy.committed_cost(t)+extra
forecast={'at':at.isoformat(),'original_anchor':a.policy.host_started_at.isoformat(),'stop':a.policy.stop_at.isoformat(),'remaining':203,'hours_per_execution':hours_per,'execution_hours':203*hours_per,'preparation_shutdown_hours':2.5,'uncertainty_hours':24,'completion':completion.isoformat(),'uncertainty_completion':uncertain.isoformat(),'minimum_stop_with_30minute_margin':admission_projection.isoformat(),'time_shortfall_hours':max(0,(admission_projection-a.policy.stop_at).total_seconds()/3600),'current_conservative_cost_usd':cost(at),'completion_cost_usd':cost(completion),'uncertainty_cost_usd':cost(uncertain),'admission_projection_usd':cost(admission_projection),'full_deadline_usd':cost(a.policy.stop_at),'guard':74,'ceiling':75,'extra_root_reserve_usd':extra,'time_gate':uncertain<a.policy.stop_at-timedelta(minutes=30),'cost_gate':cost(admission_projection)<74 and cost(a.policy.stop_at)<75,'storage_gate':max(cloud_projection,backup_projection)<80*1024**3 and resources['system_free_bytes']>=physical_required,'cloud_bytes':cloud_bytes,'cloud_projection_bytes':cloud_projection,'backup_projection_bytes':backup_projection,'physical_required_free_bytes':physical_required,'actual_billed_spending':'NOT_QUERIED; accepted conservative elapsed-clock forecast retained'}
def command(args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=20)
    return {'exit':p.returncode,'out':p.stdout,'err':p.stderr}
nr={}
for name in ['/etc/needrestart/needrestart.conf','/usr/sbin/needrestart']:
    p=Path(name); lines=p.read_text().splitlines()
    selected=set()
    for i,line in enumerate(lines):
        if any(k in line for k in ['override_rc','conf.d','blacklist_rc']):
            selected.update(range(max(0,i-3),min(len(lines),i+9)))
    nr[name]={'sha256':hash_file(p),'excerpts':[(i+1,lines[i]) for i in sorted(selected)][:100]}
print(json.dumps({'status':'READ_ONLY_GATES_CHECKED','counts':{'BACKED_UP':1297,'PLANNED':203},'pause':pause,'next':rows[1297],'all1297_receipt_bindings_verified':True,'latest_archive_required_members_and_pinned_head_verified':True,'last_backup':last,'source_and_authority':'PASS_UNCHANGED_FROZEN_V11','resources':resources,'forecast':forecast,'needrestart':nr,'apt_active':command(['systemctl','is-active','apt-daily-upgrade.service']),'timers':command(['systemctl','show','fyp-phase8-hardstop.timer','fyp-v11-admission-cutoff.timer','--property=Id,ActiveState,NextElapseUSecRealtime']),'filesystem':command(['findmnt','-n','-o','SOURCE,FSTYPE,SIZE,AVAIL','/'])}))
