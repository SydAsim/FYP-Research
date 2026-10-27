set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v11
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v11:/opt/fyp-phase8-continuation-v11/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v11/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'READ'
import sys,json,subprocess,shutil
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from closed145 import snapshot
from closed616 import REL
from controls import read,utc,hash_file
from operational_limits import effective_policy
root=Path('/var/lib/p8-continuation-v9/run');rows,notices=snapshot(root/'campaign.sqlite3');counts={}
for row in rows:counts[row['state']]=counts.get(row['state'],0)+1
active=[r for r in rows if r['state'] not in ('BACKED_UP','PLANNED')]
pending=[r for r in rows if r['state']=='PLANNED']
policy=effective_policy(read(root/'run.json')['policy'])
extra_root_reserve=read(Path('/var/lib/p8-continuation-v11/deployment/root-resize-plan.json'))['total_extra_storage_reserve_usd']
proofs={}
for name in ['prelaunch','complete']:
    p=root/(name+'-backup-proof.json')
    if p.exists():
        raw=read(p);proofs[name]={'status':raw['status'],'sha256':raw['cloud']['sha256'],'version_id':raw['cloud']['version_id'],'bytes':raw['cloud']['bytes'],'readback_sha256':raw['readback_sha256']}
print(json.dumps({'at':utc().isoformat(),'run_id':policy.run_id,'version':'phase85-continuation-v11','counts':counts,'active':active,'next_planned':pending[0] if pending else None,'sequence617':rows[616],'sequence617_admission':[n for n in notices if n.get('kind')=='ADMITTED' and n.get('execution_id')==rows[616]['execution_id']],'pause':read(root/'pause.json') if (root/'pause.json').exists() else None,'first616_unchanged':rows[:616]==read(root/REL)['rows'][:616],'service_state':subprocess.run(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','--property=Id,ActiveState,SubState,MainPID'],check=True,capture_output=True,text=True,timeout=10).stdout,'free_disk_bytes':shutil.disk_usage('/').free,'actual_filesystem_bytes':shutil.disk_usage('/').total,'resource_guard_thresholds':{'admission_free_bytes':policy.admission_disk_bytes,'active_free_bytes':policy.active_disk_bytes,'note':'Full remaining-capacity projection is retained in continuation-readiness.json; the old static prelaunch estimate is not a live threshold'},'stop_at':policy.stop_at.isoformat(),'admission_guard_usd':policy.admission_committed_usd,'budget_ceiling_usd':policy.budget_usd,'current_formula_forecast_usd':policy.committed_cost(utc())+extra_root_reserve,'accounting':'Conservative elapsed-clock policy including additional root reserve; not actual billed spending','backups':proofs,'timers':subprocess.run(['systemctl','list-timers','fyp-phase8-hardstop.timer','fyp-p85-continuation-bootstrap-stop.timer','fyp-v11-admission-cutoff.timer','--no-pager'],check=True,capture_output=True,text=True,timeout=10).stdout}))
READ
