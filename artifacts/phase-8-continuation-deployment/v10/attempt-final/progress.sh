set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v10
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v10:/opt/fyp-phase8-continuation-v10/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v10/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'PROGRESS'
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
