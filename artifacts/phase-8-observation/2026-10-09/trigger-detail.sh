set -eu
python3 - <<'PY'
import json,sqlite3,subprocess
from pathlib import Path
r=Path('/var/lib/p8-combined-v4/run')
with sqlite3.connect((r/'campaign.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as d:
 d.execute('BEGIN')
 n=[json.loads(x[0]) for x in d.execute('SELECT body FROM notices ORDER BY n')]
 print(json.dumps([x for x in n if '2026-10-09T03:30'<=x['at']<='2026-10-09T04:00' and x['kind']!='TRANSITION']))
p=subprocess.run(['journalctl','-u','fyp-phase8-campaign.service','-u','fyp-phase8-watchdog.service','--since','2026-10-09 03:38:00 UTC','--until','2026-10-09 03:45:00 UTC','--no-pager','-o','short-iso-precise'],check=True,capture_output=True,text=True,timeout=20);print(p.stdout)
PY
