set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v11
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v11:/opt/fyp-phase8-continuation-v11/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v11/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'RELEASE'
import sys,json,subprocess
from pathlib import Path
from datetime import timedelta
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,write_new,hash_file,guard,utc
from runner import verify_run,verify_host_timer,verify_clock,meter,campaign_unit,watchdog_unit
from handover import release_reviewed_boundary
from closed616 import verify
from prelaunch_backup import verify_proof
from storage import S3Cloud
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v11/deployment')
assert read(dep/'complete-stage.json')['status']=='PASS_INDEPENDENT_READBACK'
a=verify_run(root);verify(root,closed=True)
cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/')
for phase in ('prelaunch','complete'):verify_proof(root,phase,cloud)
assert not (root/'retained-driver616-pause-v11.json').exists(),'PAUSE_RELEASE_ALREADY_ATTEMPTED_RECONCILE'
sample=meter(root);cloudbytes=cloud.inventory();guard(a.policy,sample,utc(),cloudbytes,extra_bytes=a.policy.slot_capacity_reserve_bytes)
backup_projection=sample['backup_bytes']+884*60*1024**2+1024**3
cloud_projection=cloudbytes+884*60*1024**2+1024**3
required=(backup_projection-sample['backup_bytes'])+(50*1024**3-sample['working_bytes'])+20*1024**3+1024**3
assert backup_projection<80*1024**3 and cloud_projection<80*1024**3 and sample['system_free_bytes']>=required,'FINAL_CAPACITY_STOP'
extra=read(dep/'root-resize-plan.json')['total_extra_storage_reserve_usd']
uncertain=utc()+timedelta(hours=884*262.31642189586114/1355+2.5+24)
assert uncertain<a.policy.stop_at-timedelta(minutes=30) and a.policy.committed_cost(uncertain+timedelta(minutes=30))+extra<74 and a.policy.committed_cost(a.policy.stop_at)+extra<75,'FINAL_FEASIBILITY_STOP'
for name,text in [('fyp-phase8-campaign.service',campaign_unit(root)),('fyp-phase8-watchdog.service',watchdog_unit(root))]:assert Path('/etc/systemd/system',name).read_text()==text
physical=read(dep/'root-resize-verified.json')
assert hash_file(dep/'admission-cutoff.py')==physical['fence_script_sha256'] and hash_file(Path('/etc/systemd/system/fyp-v11-admission-cutoff.timer'))==physical['fence_timer_sha256']
subprocess.run(['systemctl','enable','--now','fyp-phase8-watchdog.service'],check=True,timeout=20)
verify_host_timer(root);verify_clock(root,a.policy)
release_reviewed_boundary(root)
write_new(dep/'actual-release.json',{'status':'PASS_RELEASED_CLOSED616_NOT_YET_ADMISSION','at':utc().isoformat(),'next_sequence':617,'next_execution_id':'01a11705-11f2-7276-8d5f-0277ced1a5f5','first616_preserved':True,'pause_sha256':hash_file(root/'retained-driver616-pause-v11.json'),'both_backup_readbacks_verified':True,'backup_full_projection_bytes':backup_projection,'cloud_full_projection_bytes':cloud_projection,'required_physical_free_bytes':required,'free_bytes':sample['system_free_bytes'],'stop_at':a.policy.stop_at.isoformat()})
print(json.dumps(read(dep/'actual-release.json')))
RELEASE
systemctl start fyp-phase8-campaign.service
systemctl is-active fyp-phase8-campaign.service fyp-phase8-watchdog.service fyp-phase8-hardstop.timer
