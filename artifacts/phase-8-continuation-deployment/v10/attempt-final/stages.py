"""Assemble the remaining external stages before boot, not a research amendment."""
import json
from pathlib import Path
from build import HERE,write

def main():
    h=(HERE/'HEADER.txt').read_text()
    oldheader=h.replace('cd /opt/fyp-phase8-continuation-v10','cd /opt/fyp-phase8-continuation-v9').replace('export PYTHONPATH=/opt/fyp-phase8-continuation-v10:', 'export PYTHONPATH=/opt/fyp-phase8-continuation-v9:')
    write('install-timer-files.sh',oldheader+'''.venv/bin/python -B - <<'OLD'
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,Policy,write_new,hash_file
from runner import campaign_unit,watchdog_unit,unit_text
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v10/deployment');out=dep/'prior-unit-files-final';out.mkdir(mode=0o700,exist_ok=False)
service,timer=unit_text(root,Policy.model_validate(read(root/'run.json')['policy']))
expected={'fyp-phase8-hardstop.service':service,'fyp-phase8-hardstop.timer':timer,'fyp-phase8-watchdog.service':watchdog_unit(root),'fyp-phase8-campaign.service':campaign_unit(root)}
for name,text in expected.items():
    p=Path('/etc/systemd/system')/name
    assert not p.is_symlink() and p.read_text()==text,'OLD_UNIT_OWNERSHIP_DRIFT:'+name
for u in ('fyp-phase8-campaign.service','fyp-phase8-watchdog.service'):
    assert subprocess.run(['systemctl','show',u,'--property=MainPID','--value'],check=True,text=True,capture_output=True,timeout=10).stdout.strip()=='0'
write_new(out/'manifest.json',{name:hash_file(Path('/etc/systemd/system')/name) for name in expected})
subprocess.run(['systemctl','stop','fyp-phase8-hardstop.timer'],check=True,timeout=10)
for name in expected:(Path('/etc/systemd/system')/name).rename(out/name)
OLD
'''+h+'''.venv/bin/python -B - <<'NEW'
import json,sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,write_new,utc,hash_file
from runner import unit_text,campaign_unit,watchdog_unit
from handover import ContinuationAuthority
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v10/deployment')
a=ContinuationAuthority(root,read(root/'run.json'));a.verify(prelaunch=True)
service,timer=unit_text(root,a.policy)
expected={'fyp-phase8-hardstop.service':service,'fyp-phase8-hardstop.timer':timer,'fyp-phase8-watchdog.service':watchdog_unit(root),'fyp-phase8-campaign.service':campaign_unit(root)}
for name,text in expected.items():
    with (Path('/etc/systemd/system')/name).open('x') as f:f.write(text)
bootstrap=Path('/etc/systemd/system/fyp-p85-continuation-bootstrap-stop.timer')
old=bootstrap.read_text()
assert not bootstrap.is_symlink() and old=='[Unit]\\nDescription=Original Phase 8 deadline also applies during bootstrap\\n[Timer]\\nOnCalendar=2026-10-22 15:24:23 UTC\\nPersistent=true\\nAccuracySec=1s\\nUnit=fyp-p85-continuation-bootstrap-stop.service\\n[Install]\\nWantedBy=timers.target\\n'
subprocess.run(['systemctl','stop',bootstrap.name],check=True,timeout=10)
bootstrap.rename(dep/'prior-unit-files-final'/bootstrap.name)
with bootstrap.open('x') as f:f.write(old.replace('2026-10-22','2026-10-25'))
subprocess.run(['systemctl','daemon-reload'],check=True,timeout=20)
subprocess.run(['systemctl','enable','--now','fyp-phase8-hardstop.timer',bootstrap.name],check=True,timeout=20)
for u in ('fyp-phase8-hardstop.timer',bootstrap.name):subprocess.run(['systemctl','is-active','--quiet',u],check=True,timeout=10)
write_new(dep/'timer-files-prepared-final.json',{'status':'PASS_TIMERS_ACTIVE_WATCHDOG_NOT_STARTED','at':utc().isoformat(),'units':{name:hash_file(Path('/etc/systemd/system')/name) for name in expected},'stop_at':a.policy.stop_at.isoformat(),'host_hours':a.policy.host_hours,'watchdog_active':False,'main_started':False})
print(json.dumps(read(dep/'timer-files-prepared-final.json')))
NEW
''')
    write('readiness.sh',h+'''.venv/bin/python -B - <<'READY'
import json,sys,hashlib,subprocess,socket
from datetime import datetime,timedelta
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import Journal,read,write_new,hash_file,canonical,guard,utc
from handover import ContinuationAuthority,CHECKS,closed_boundary
from closed145 import verify_retained_root
from runner import verify_clock,unit_text
from operational_limits import LIMITS_SHA256
from prelaunch_backup import verify_proof
from storage import S3Cloud
from transport import S3Store
from research.execution_linux_v1.platform import host
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v10/deployment')
external=read(dep/'external-preboot-final.json');assert datetime.fromisoformat(external['expires_at'])>utc(),'EXTERNAL_GATES_EXPIRED'
health=read(dep/'live-preparation-checks.json');meta=read(dep/'metadata-prepared-final.json');timers=read(dep/'timer-files-prepared-final.json')
assert health['status']=='PASS' and health['closed_originals']==145 and health['planned']==1355 and health['driver_calls']==0
assert meta['status']=='PASS' and meta['original_pause_preserved'] and timers['status']=='PASS_TIMERS_ACTIVE_WATCHDOG_NOT_STARTED'
a=ContinuationAuthority(root,read(root/'run.json'));proof=a.verify(prelaunch=True)
j=Journal(root);j.verify();rows=j.rows();closed_boundary(rows,read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows']);verify_retained_root(root)
verify_clock(root,a.policy)
assert rows[145]['execution_id']=='01a11705-11f1-772d-8190-c43552871801' and rows[145]['state']=='PLANNED'
cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/');verify_proof(root,'prelaunch',cloud)
store=S3Store('fyp-research');assert store.client.get_bucket_versioning(Bucket=a.policy.cloud_bucket).get('Status')=='Enabled'
cloud_bytes=cloud.inventory()
with j.connect() as db:reserved=db.execute("SELECT COALESCE(sum(bytes),0) FROM reservations WHERE state!='VERIFIED'").fetchone()[0]
assert reserved==0,'UNRECONCILED_RESERVATIONS'
sample=host(root,root.parent/'backup');sample.update(working_bytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),backup_bytes=sum(p.stat().st_size for p in root.parent.joinpath('backup').rglob('*.tar.gz')))
guard(a.policy,sample,utc(),cloud_bytes,extra_bytes=a.policy.slot_capacity_reserve_bytes)
assert sample['system_free_bytes']>=145670462448,'REVIEWED_PROJECTED_DISK_HEADROOM_STOP'
now=utc();finish=now+timedelta(hours=262.31642189586114+2.5);uncertain=finish+timedelta(hours=24)
assert uncertain<a.policy.stop_at-timedelta(seconds=a.policy.admission_cutoff_seconds) and a.policy.committed_cost(uncertain)<70 and a.policy.committed_cost(a.policy.stop_at)<75,'TIME_OR_COST_STOP'
latest=read(root/'prelaunch-backup-proof.json');base=Path(latest['archive']).stat().st_size
projected=83218519158.73685+max(0,cloud_bytes-3066593484)+max(0,base-37194083)*1500
assert projected+a.policy.slot_capacity_reserve_bytes<a.policy.cloud_limit_bytes,'UPDATED_METADATA_FUTURE_STORAGE_STOP'
owner=Path('/var/lib/fyp-owner');assert owner.stat().st_mode&0o777==0o700 and (owner/'owner.key').stat().st_mode&0o777==0o600
for port in (16432,16433,19100,19101,19102,19110):
    with socket.socket() as s:s.bind(('127.0.0.1',port))
for unit in ('fyp-phase8-campaign.service','fyp-phase8-watchdog.service'):
    assert subprocess.run(['systemctl','show',unit,'--property=MainPID','--value'],check=True,text=True,capture_output=True,timeout=10).stdout.strip()=='0'
service,timer=unit_text(root,a.policy)
assert Path('/etc/systemd/system/fyp-phase8-hardstop.service').read_text()==service and Path('/etc/systemd/system/fyp-phase8-hardstop.timer').read_text()==timer
for unit in ('fyp-phase8-hardstop.timer','fyp-p85-continuation-bootstrap-stop.timer'):subprocess.run(['systemctl','is-active','--quiet',unit],check=True,timeout=10)
assert external['guards']['absolute']['State']=='ENABLED' and external['guards']['preparation']['State']=='ENABLED'
assert json.loads(external['guards']['preparation']['Target']['Input'])=={'InstanceIds':[external['instance_id']]}
assert external['host_owned_stopped_before_boot'] and external['no_inbound_access'] and external['retention_authorized_until']=='2026-10-27T15:24:23.810674Z'
ready={'version':'phase85-continuation-v10','status':'PASS','at_utc':now.isoformat(),'run_id':a.policy.run_id,'instance_id':external['instance_id'],
    'policy_sha256':hashlib.sha256(canonical(a.policy.model_dump(mode='json'))).hexdigest(),'operational_limits_sha256':LIMITS_SHA256,
    'handover_sha256':hash_file(root/'handover.json'),'boot_anchor_sha256':hash_file(root/'host-clock.json'),'checks':dict.fromkeys(CHECKS,True),
    'evidence':{'external_preboot':hash_file(dep/'external-preboot-final.json'),'source_dependencies_archives':hash_file(dep/'live-preparation-checks.json'),
        'metadata':hash_file(dep/'metadata-prepared-final.json'),'timer_files':hash_file(dep/'timer-files-prepared-final.json'),'prelaunch':latest},
    'backed_up':145,'planned':1355,'active':0,'next_sequence':146,'next_execution_id':rows[145]['execution_id'],'host':sample,
    'cloud_all_versions_bytes':cloud_bytes,'future_storage_bytes':projected,'metadata_base_bytes':base,
    'budget':{'completion_usd':a.policy.committed_cost(finish),'uncertainty_usd':a.policy.committed_cost(uncertain),'full_deadline_usd':a.policy.committed_cost(a.policy.stop_at)},
    'stop_at':a.policy.stop_at.isoformat(),'driver_calls':0}
write_new(root/'continuation-readiness.json',ready);j.event('V10_ACTUAL_READINESS_VERIFIED',hash=hash_file(root/'continuation-readiness.json'),instance=external['instance_id'],main_admitted=False)
print(json.dumps({'status':'PASS','readiness_sha256':hash_file(root/'continuation-readiness.json'),'instance_id':external['instance_id'],'policy_sha256':ready['policy_sha256'],'checks':ready['checks'],'main_admitted':False}))
READY
''')
    write('activate-controls-and-launch.sh',h+'''.venv/bin/python -B - <<'VERIFY'
import json,sys,subprocess,socket
from datetime import timedelta
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import Journal,read,write_new,hash_file,utc,guard
from runner import verify_run,verify_host_timer,verify_clock,unit_text,watchdog_unit,campaign_unit
from handover import release_reviewed_boundary,closed_boundary
from prelaunch_backup import verify_proof
from storage import S3Cloud
from research.execution_linux_v1.platform import host
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v10/deployment')
a=verify_run(root);cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/')
for phase in ('prelaunch','complete'):verify_proof(root,phase,cloud)
service,timer=unit_text(root,a.policy)
expected={'fyp-phase8-hardstop.service':service,'fyp-phase8-hardstop.timer':timer,'fyp-phase8-watchdog.service':watchdog_unit(root),'fyp-phase8-campaign.service':campaign_unit(root)}
for name,text in expected.items():assert Path('/etc/systemd/system',name).read_text()==text,'CONTROL_UNIT_DRIFT'
subprocess.run(['systemctl','enable','--now','fyp-phase8-watchdog.service'],check=True,timeout=20)
verify_host_timer(root);verify_clock(root,a.policy)
j=Journal(root);rows=j.rows();closed_boundary(rows,read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows'])
assert rows[145]['execution_id']=='01a11705-11f1-772d-8190-c43552871801'
cloud_bytes=cloud.inventory();base=max(Path(read(root/(phase+'-backup-proof.json'))['archive']).stat().st_size for phase in ('prelaunch','complete'))
projected=83218519158.73685+max(0,cloud_bytes-3066593484)+max(0,base-37194083)*1500
assert projected+a.policy.slot_capacity_reserve_bytes<a.policy.cloud_limit_bytes,'FINAL_FUTURE_STORAGE_PROJECTION_STOP'
sample=host(root,root.parent/'backup');sample.update(working_bytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),backup_bytes=sum(p.stat().st_size for p in root.parent.joinpath('backup').rglob('*.tar.gz')))
assert sample['system_free_bytes']>=145670462448,'PROJECTED_DISK_HEADROOM_STOP'
guard(a.policy,sample,utc(),cloud_bytes,extra_bytes=a.policy.slot_capacity_reserve_bytes)
uncertain=utc()+timedelta(hours=262.31642189586114+2.5+24)
assert uncertain<a.policy.stop_at-timedelta(seconds=1800) and a.policy.committed_cost(uncertain)<70
for port in (16432,16433,19100,19101,19102,19110):
    with socket.socket() as s:s.bind(('127.0.0.1',port))
release_reviewed_boundary(root)
write_new(dep/'final-release-verification.json',{'status':'PASS_EXACT_BOUNDARY_RELEASED','at':utc().isoformat(),'backed_up':145,'planned':1355,'next':rows[145],'both_backup_proofs_verified':True,'future_storage_bytes':projected,'driver_calls':0})
print(json.dumps(read(dep/'final-release-verification.json')))
VERIFY
systemctl start fyp-phase8-campaign.service
systemctl is-active fyp-phase8-campaign.service fyp-phase8-watchdog.service fyp-phase8-hardstop.timer
''')
    write('progress.sh',h+'''.venv/bin/python -B - <<'PROGRESS'
import sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from closed145 import snapshot
from controls import read,utc
root=Path('/var/lib/p8-continuation-v9/run');rows,notices=snapshot(root/'campaign.sqlite3')
counts={}
for row in rows:counts[row['state']]=counts.get(row['state'],0)+1
print(json.dumps({'at':utc().isoformat(),'counts':counts,'sequence146':rows[145],'admission_notice':[n for n in notices if n.get('kind')=='ADMITTED' and n.get('execution_id')==rows[145]['execution_id']],
    'pause':read(root/'pause.json') if (root/'pause.json').exists() else None,'service_state':subprocess.run(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','--property=Id,ActiveState,SubState,MainPID'],check=True,text=True,capture_output=True,timeout=10).stdout,
    'prelaunch':read(root/'prelaunch-backup-proof.json'),'complete':read(root/'complete-backup-proof.json')}))
PROGRESS
''')
    print('Remaining external stages assembled, not executed.')

if __name__=='__main__':main()
