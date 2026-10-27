set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v12:/opt/fyp-phase8-continuation-v12/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v12/.venv-transport/lib/python3.12/site-packages
timeout 60s /opt/fyp-phase8-continuation-v12/.venv/bin/python -B - <<'READ_ONLY'
import json,sys,subprocess
from pathlib import Path
sys.path.insert(0,'/opt/fyp-phase8-continuation-v12/artifacts/phase-8-runner-amendment/v4-complete')
from closed145 import snapshot
root=Path('/var/lib/p8-continuation-v9/run');rows,notices=snapshot(root/'campaign.sqlite3')
selected=[x for x in notices if x.get('at','')>='2026-10-23T19:34:19' and x.get('kind') not in ('TRANSITION','HOST_CLOCK_SAMPLE')]
print(json.dumps({'notices':selected[-12:]},default=str))
p=subprocess.run(['journalctl','-u','fyp-phase8-campaign.service','--since','2026-10-23 19:34:19 UTC','--no-pager','-o','short-iso-precise','-n','45'],capture_output=True,text=True,check=True,timeout=15)
print('\n'.join(line for line in p.stdout.splitlines() if 'HOST_CLOCK_SAMPLE' not in line)[-10000:])
READ_ONLY
