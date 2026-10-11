set -euo pipefail
cd /opt/fyp-phase8-continuation-v9
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v9:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'PROGRESS'
import json,sys,subprocess,sqlite3,collections
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from handover import ro_rows
from controls import read,utc
from operational_limits import effective_policy
root=Path('/var/lib/p8-continuation-v9/run');rows=ro_rows(root)
active=[x for x in rows if x['state'] not in ('PLANNED','BACKED_UP')]
with sqlite3.connect((root/'campaign.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as db:
    db.execute('BEGIN');admissions=[]
    for record, in db.execute('SELECT body FROM notices ORDER BY n'):
        event=json.loads(record)
        if event.get('kind') in ('ORIGINAL_ADMITTED','SLOT_ADMITTED','ADMITTED') or ('ADMIT' in event.get('kind','')):admissions.append(event)
v={'at_utc':utc().isoformat(),'run_id':read(root/'run.json')['policy']['run_id'],'counts':dict(collections.Counter(x['state'] for x in rows)),'sequence121':rows[120],'active':active,'latest_admissions':admissions[-3:],'pause':read(root/'pause.json') if (root/'pause.json').exists() else None,'services':subprocess.run(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','fyp-phase8-hardstop.timer','--property=Id,ActiveState,SubState,MainPID,Result'],check=True,text=True,capture_output=True,timeout=10).stdout,'prelaunch_backup':read(root/'prelaunch-backup-proof.json')['cloud'],'complete_backup':read(root/'complete-backup-proof.json')['cloud'],'deadline':effective_policy(read(root/'run.json')['policy']).stop_at.isoformat()}
print(json.dumps(v))
PROGRESS
