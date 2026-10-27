set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v10
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v10:/opt/fyp-phase8-continuation-v10/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v10/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'INSPECT'
import json,sys,subprocess,hashlib,shutil
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from closed145 import snapshot
from controls import read,utc
root=Path('/var/lib/p8-continuation-v9/run')
rows,notices=snapshot(root/'campaign.sqlite3')
counts={}
for r in rows: counts[r['state']]=counts.get(r['state'],0)+1
journal=subprocess.run(['journalctl','-u','fyp-phase8-campaign.service','--since','2026-10-16 13:35:00 UTC','--until','2026-10-16 14:00:00 UTC','--no-pager','-o','short-iso-precise'],capture_output=True,text=True,check=True,timeout=15).stdout
state=subprocess.run(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','--property=Id,ActiveState,SubState,MainPID,Result,ExecStart,FragmentPath'],capture_output=True,text=True,check=True,timeout=10).stdout
print(json.dumps({'at':utc().isoformat(),'counts':counts,'pause':read(root/'pause.json') if (root/'pause.json').exists() else None,'boundary':rows[614:618],'notices':notices[-12:],'journal':journal[-12000:],'state':state,'disk':shutil.disk_usage('/')._asdict(),'last_files':{str(p.relative_to(root)):p.stat().st_size for folder in ['executions','backups'] for p in (root/folder).glob('*') if rows[615]['execution_id'] in p.name}},default=str))
INSPECT
