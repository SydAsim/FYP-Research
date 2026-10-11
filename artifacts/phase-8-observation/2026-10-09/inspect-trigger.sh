set -euo pipefail
umask 077
python3 - <<'PY'
import collections,json,sqlite3,subprocess
from pathlib import Path
root=Path('/var/lib/p8-combined-v4/run')
with sqlite3.connect(root.resolve().as_uri()+'/'+'campaign.sqlite3?mode=ro',uri=True) as db:
 db.row_factory=sqlite3.Row;db.execute('BEGIN')
 rows=[dict(x) for x in db.execute('SELECT * FROM slots ORDER BY sequence')]
 notices=[json.loads(x[0]) for x in db.execute('SELECT body FROM notices ORDER BY n')]
 result={'counts':dict(collections.Counter(r['state'] for r in rows)),'active':[r for r in rows if r['state'] in ('RUNNING','EXPORTED')],'pause':json.loads((root/'pause.json').read_text()),'around_stop':[n for n in notices if '2026-10-09T03:25'<=n['at']<='2026-10-09T04:00'],'latest_notices':notices[-10:],'next':next(r for r in rows if r['state']=='PLANNED')}
print(json.dumps(result))
for args in (['journalctl','-u','fyp-phase8-campaign.service','-u','fyp-phase8-watchdog.service','--since','2026-10-09 03:30:00 UTC','--until','2026-10-09 03:50:00 UTC','--no-pager','-o','short-iso-precise'],['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','--property=Id,ActiveState,SubState,MainPID,ExecMainStatus'],['docker','ps','-a','--format','{{.Names}} {{.Status}}'],['ps','-eo','pid,ppid,lstart,args']):
 p=subprocess.run(args,check=True,capture_output=True,text=True,timeout=20);print(p.stdout)
PY
