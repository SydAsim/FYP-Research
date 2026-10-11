set -eu
cd /opt/fyp-phase8-continuation-v1
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B - <<'PY'
import json,sys,subprocess
from datetime import timedelta
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-continuation/v1'))
from controls import Journal,guard,read,utc,write_new
from runner import verify_run,verify_host_timer,meter,cloud_for
from handover import closed_boundary
from storage import ObjectProof
root=Path('/var/lib/p8-continuation/run');dep=root.parent/'deployment'
a=verify_run(root);verify_host_timer(root);j=Journal(root)
closed_boundary(j.rows(),read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows'])
now=utc();finish=now+timedelta(hours=314);cost=a.policy.committed_cost(finish+timedelta(minutes=30))
if cost>=55 or finish>=a.policy.stop_at-timedelta(seconds=a.policy.admission_cutoff_seconds):raise ValueError('UNCHANGED_COST_OR_TIME_PLAN_DOES_NOT_FIT')
cloud=cloud_for(root);cloud_bytes=cloud.inventory();sample=meter(root)
with j.connect() as db:reserved=db.execute("SELECT COALESCE(sum(bytes),0) FROM reservations WHERE state!='VERIFIED'").fetchone()[0]
guard(a.policy,sample,now,cloud_bytes+reserved,extra_bytes=a.policy.slot_capacity_reserve_bytes)
proof=ObjectProof.model_validate(read(dep/'authorized-prelaunch-backup.json')['cloud']);cloud.verify(proof)
subprocess.run(['systemctl','is-active','--quiet','fyp-p85-continuation-preparation-absolute.timer'],check=True)
timer=subprocess.run(['systemctl','show','fyp-p85-continuation-preparation-absolute.timer','--property=NextElapseUSecRealtime'],capture_output=True,text=True,check=True).stdout
if '2026-10-07 22:26:52' not in timer:raise ValueError('ORIGINAL_PREPARATION_BOUND_DRIFT')
write_new(dep/'immediate-prelaunch-verification.json',{'status':'PASS','at_utc':now.isoformat(),'conservative_314h_finish':finish.isoformat(),'cost_at_finish_plus_30min_usd':cost,'policy_unchanged':True,'resources':sample,'cloud_bytes_all_versions':cloud_bytes,'unverified_reservations':reserved,'backup':proof.model_dump(),'next_execution_id':j.rows()[1]['execution_id'],'original_deadline':a.policy.stop_at.isoformat()})
print(json.dumps(read(dep/'immediate-prelaunch-verification.json')))
PY
.venv/bin/python -B artifacts/phase-8-continuation/v1/handover.py release-reviewed-boundary --root /var/lib/p8-continuation/run
systemctl start fyp-phase8-campaign.service
systemctl is-active fyp-phase8-campaign.service fyp-phase8-watchdog.service fyp-phase8-hardstop.timer fyp-p85-continuation-bootstrap-stop.timer

