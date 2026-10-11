#!/bin/bash
set -euo pipefail
python3 - <<'PY'
import datetime,json,sqlite3,subprocess
from pathlib import Path
root=Path('/var/lib/p8/run')
config=json.loads((root/'run.json').read_text())
with sqlite3.connect('file:/var/lib/p8/run/campaign.sqlite3?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    counts={r['state']:r['n'] for r in db.execute('SELECT state,COUNT(*) n FROM slots GROUP BY state')}
    active=[dict(r) for r in db.execute("SELECT sequence,case_id,arm,execution_id,state,deadline,error FROM slots WHERE state IN ('RUNNING','EXPORTED') ORDER BY sequence")]
    last=[json.loads(r[0]) for r in db.execute('SELECT body FROM notices ORDER BY n DESC LIMIT 4')]
pause=json.loads((root/'pause.json').read_text()) if (root/'pause.json').exists() else None
print(json.dumps({'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run_id':config['policy']['run_id'],'clock_start':config['policy']['host_started_at'],'host_deadline_hours':config['policy']['host_hours'],'counts':counts,'active':active,'pause':pause,'completion':json.loads((root/'completion.json').read_text()) if (root/'completion.json').exists() else None,'last_events':last},indent=2))
PY
systemctl show fyp-phase8-campaign.service -p ActiveState -p SubState -p ActiveEnterTimestamp -p Restart
systemctl is-active fyp-phase8-hardstop.timer fyp-phase8-watchdog.service || true
journalctl -u fyp-phase8-campaign.service -n 5 --no-pager
