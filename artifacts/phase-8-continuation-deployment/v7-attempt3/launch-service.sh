set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v7
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v7:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'VERIFY'
import json,socket,sys,subprocess
from datetime import timedelta
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import Journal,read,write_new,utc,guard
from runner import verify_run,verify_host_timer,verify_clock
from handover import verify_imported_first,release_reviewed_boundary
from closed_restart import boundary
from prelaunch_backup import verify_proof
from storage import S3Cloud
from research.execution_linux_v1.platform import host
root=Path('/var/lib/p8-continuation-v7/run');dep=root.parent/'deployment'
a=verify_run(root);verify_host_timer(root);verify_imported_first(root);verify_clock(root,a.policy,utc())
j=Journal(root);rows=j.rows();boundary(rows,read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows'])
assert rows[82]['state']=='PLANNED' and rows[82]['execution_id']=='01a11705-11f1-792b-ae1e-36bfc6773842'
assert read(dep/'controls-installed-attempt3.json')['status']=='PASS'
cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/')
for phase in ('prelaunch','complete'):verify_proof(root,phase,cloud)
cloud_bytes=cloud.inventory()
with j.connect() as db:reserved=db.execute("SELECT COALESCE(sum(bytes),0) FROM reservations WHERE state!='VERIFIED'").fetchone()[0]
assert reserved==0
now=utc();finish=now+timedelta(hours=274.51268357810414+2+.5)
assert finish<a.policy.stop_at-timedelta(seconds=a.policy.admission_cutoff_seconds) and a.policy.committed_cost(finish)<60
sample=host(root,root.parent/'backup');guard(a.policy,sample,now,cloud_bytes,extra_bytes=a.policy.slot_capacity_reserve_bytes)
for port in (16432,16433,19100,19101,19102,19110):
    with socket.socket() as s:s.bind(('127.0.0.1',port))
assert read(Path('/var/lib/p8-combined-v4/run/pause.json'))['reason']=='PROTOCOL_STOP'
v={'status':'PASS','at_utc':now.isoformat(),'next_sequence':83,'next_execution_id':rows[82]['execution_id'],'both_backups_verified':True,'active_watchdog_and_absolute_timer':True,'remaining_before_admission':1418,'conservative_projected_usd':a.policy.committed_cost(finish),'projected_shutdown_utc':finish.isoformat(),'host':sample,'cloud_all_versions_bytes':cloud_bytes,'original_deadline':a.policy.stop_at.isoformat(),'main_admitted':False}
write_new(dep/'immediate-prelaunch-verification-attempt3.json',v)
release_reviewed_boundary(root)
print(json.dumps(v))
VERIFY
systemctl start fyp-phase8-campaign.service
systemctl is-active fyp-phase8-campaign.service fyp-phase8-watchdog.service fyp-phase8-hardstop.timer fyp-p85-continuation-bootstrap-stop.timer
.venv/bin/python -B - <<'ACTIVE'
import json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import utc,write_new
v={'kind':'ACTUAL_SERVICE_ACTIVATION_NOT_ADMISSION_PROOF','at_utc':utc().isoformat(),'state':subprocess.run(['systemctl','show','fyp-phase8-campaign.service','--property=ActiveState,SubState,MainPID,ExecMainStartTimestamp'],check=True,text=True,capture_output=True,timeout=10).stdout}
write_new(Path('/var/lib/p8-continuation-v7/deployment/service-activation-attempt3.json'),v);print(json.dumps(v))
ACTIVE
