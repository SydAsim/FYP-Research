set -eu
export PYTHONDONTWRITEBYTECODE=1
/opt/fyp-phase8-continuation-v12/.venv/bin/python -B - <<'READONLY'
import json,sys,subprocess
from pathlib import Path
sys.path.insert(0,'/opt/fyp-phase8-continuation-v12/artifacts/phase-8-runner-amendment/v4-complete')
from closed145 import snapshot
root=Path('/var/lib/p8-continuation-v9/run')
rows,notices=snapshot(root/'campaign.sqlite3')
selected=[x for x in notices if '2026-10-23T15:10' <= str(x.get('at','')) <= '2026-10-23T15:18']
print(json.dumps({'notices':selected},ensure_ascii=True))
p=subprocess.run(['journalctl','-u','fyp-phase8-campaign.service','-u','fyp-phase8-watchdog.service','--since','2026-10-23 15:10:00 UTC','--until','2026-10-23 15:18:00 UTC','--no-pager','-n','100','-o','short-iso-precise'],capture_output=True,text=True,timeout=15,check=True)
print(p.stdout[-16000:])
READONLY