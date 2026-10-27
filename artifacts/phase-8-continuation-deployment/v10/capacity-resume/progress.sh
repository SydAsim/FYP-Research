set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v10
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v10:/opt/fyp-phase8-continuation-v10/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v10/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'PROGRESS'
import sys,json,subprocess,shutil,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from closed145 import snapshot
from controls import read,utc
root=Path('/var/lib/p8-continuation-v9/run');rows,notices=snapshot(root/'campaign.sqlite3')
counts={}
for row in rows:counts[row['state']]=counts.get(row['state'],0)+1
print(json.dumps({'at':utc().isoformat(),'counts':counts,'sequence146':rows[145],'admission_notice':[n for n in notices if n.get('kind')=='ADMITTED' and n.get('execution_id')==rows[145]['execution_id']],
    'pause':read(root/'pause.json') if (root/'pause.json').exists() else None,'service_state':subprocess.run(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','--property=Id,ActiveState,SubState,MainPID'],check=True,text=True,capture_output=True,timeout=10).stdout,
    'filesystem':{'total_bytes':shutil.disk_usage('/').total,'free_bytes':shutil.disk_usage('/').free,'required_free_bytes':145670462448},'ready':read(root/'continuation-readiness.json'),'capacity':read(Path('/var/lib/p8-continuation-v10/deployment/capacity-authorization-167.json')),'control_timers':subprocess.run(['systemctl','list-timers','fyp-phase8-hardstop.timer','fyp-p85-continuation-bootstrap-stop.timer','fyp-v10-root-cost-admission-167.timer','--no-pager'],check=True,text=True,capture_output=True,timeout=10).stdout,'retained_pause_sha256':hashlib.sha256((root/'retained-driver145-pause-v10.json').read_bytes()).hexdigest(),'first145_unchanged':rows[:145]==read(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete/closed-145/read-only-ledger.json')['rows'][:145],'prelaunch':read(root/'prelaunch-backup-proof.json'),'complete':read(root/'complete-backup-proof.json')}))
PROGRESS
