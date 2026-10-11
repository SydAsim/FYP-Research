set -euo pipefail
umask 077
cd /opt/fyp-phase8-combined-v3
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B - <<'PY'
import json,socket,sys
from datetime import timedelta
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v3'))
from controls import Journal,guard,read,utc,write_new
from runner import verify_run,verify_host_timer,verify_clock
from handover import closed_boundary,verify_imported_first,verify_members,release_reviewed_boundary
from storage import ObjectProof,S3Cloud
from research.execution_linux_v1.platform import host
root=Path('/var/lib/p8-combined/run');dep=root.parent/'deployment';a=verify_run(root)
verify_host_timer(root);verify_imported_first(root);now=utc();verify_clock(root,a.policy,now)
j=Journal(root);j.verify();rows=j.rows();closed_boundary(rows,read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows'])
if rows[2]['execution_id']!='01a11705-11f0-7a68-8c68-4da5c8126c84' or rows[2]['state']!='PLANNED':raise ValueError('NEXT_ORIGINAL_DRIFT')
finish=now+timedelta(hours=290);cost=a.policy.committed_cost(finish+timedelta(minutes=30))
if finish>=a.policy.stop_at-timedelta(seconds=a.policy.admission_cutoff_seconds) or cost>=55:raise ValueError('UNCHANGED_PLAN_NO_LONGER_FITS')
cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/');cloud_bytes=cloud.inventory()
with j.connect() as db:reserved=db.execute("SELECT COALESCE(sum(bytes),0) FROM reservations WHERE state!='VERIFIED'").fetchone()[0]
sample=host(root,root.parent/'backup');sample.update(working_bytes=0,backup_bytes=0)
guard(a.policy,sample,now,cloud_bytes+reserved,extra_bytes=a.policy.slot_capacity_reserve_bytes)
proof=read(dep/'authorized-prelaunch-backup.json')
if proof['status']!='PASS' or not proof['watchdog_and_absolute_timer_verified']:raise ValueError('AUTHORIZED_BACKUP_GATE')
cloud.verify(ObjectProof.model_validate(proof['backup']))
verify_members(root.parent/'authorized-prelaunch-readback/x/slot');verify_imported_first(root.parent/'authorized-prelaunch-readback/x/slot')
for port in (16432,16433,19100,19101,19102,19110):
 with socket.socket() as s:s.bind(('127.0.0.1',port))
v={'status':'PASS','at_utc':now.isoformat(),'run_id':a.policy.run_id,'instance_id':'i-002b63326e1566005','next_execution_id':rows[2]['execution_id'],'remaining_originals':1498,'projected_finish_utc':finish.isoformat(),'projected_cost_usd':cost,'absolute_stop_utc':a.policy.stop_at.isoformat(),'headroom':sample,'cloud_bytes':cloud_bytes,'originals_replayed':False,'original_clock_reset':False,'authorized_backup':proof['backup']}
write_new(dep/'immediate-prelaunch-verification.json',v)
release_reviewed_boundary(root);print(json.dumps(v))
PY
systemctl start fyp-phase8-campaign.service
systemctl is-active fyp-phase8-campaign.service fyp-phase8-watchdog.service fyp-phase8-hardstop.timer fyp-p85-continuation-bootstrap-stop.timer
systemctl disable --now fyp-p85-continuation-preparation-stop.timer fyp-p85-combined-preparation-absolute.timer
.venv/bin/python -B - <<'PY'
import json,sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v3'))
from controls import write_new,utc
value={'kind':'ACTUAL_SERVICE_ACTIVATION_NOT_YET_ADMISSION_PROOF','at_utc':utc().isoformat(),'instance_id':'i-002b63326e1566005','service':subprocess.run(['systemctl','show','fyp-phase8-campaign.service','--property=ActiveState,SubState,ExecMainStartTimestamp,MainPID'],check=True,capture_output=True,text=True).stdout,'preparation_timers_disabled_after_active_service':True,'absolute_deadline_unchanged':True}
write_new(Path('/var/lib/p8-combined/deployment/service-activation.json'),value);print(json.dumps(value))
PY
