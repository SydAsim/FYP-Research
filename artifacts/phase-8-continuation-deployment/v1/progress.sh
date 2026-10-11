set -eu
cd /opt/fyp-phase8-continuation-v1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B - <<'PY'
import json,sqlite3,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
root=Path('/var/lib/p8-continuation/run')
db=sqlite3.connect(f'file:{root}/campaign.sqlite3?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('BEGIN')
counts=dict(db.execute('SELECT state,count(*) FROM slots GROUP BY state').fetchall())
active=[dict(x) for x in db.execute("SELECT * FROM slots WHERE state IN ('RUNNING','EXPORTED') ORDER BY sequence")]
nextrow=db.execute("SELECT sequence,case_id,arm,execution_id FROM slots WHERE state='PLANNED' ORDER BY sequence LIMIT 1").fetchone()
recent=[json.loads(x[0]) for x in db.execute('SELECT body FROM notices ORDER BY n DESC LIMIT 8')]
admission=db.execute("SELECT body FROM notices WHERE body LIKE '%ADMITTED%' ORDER BY n DESC LIMIT 1").fetchone();db.close()
units={}
for unit in ('fyp-phase8-campaign.service','fyp-phase8-watchdog.service','fyp-phase8-hardstop.timer','fyp-p85-continuation-bootstrap-stop.timer','fyp-p85-continuation-preparation-stop.timer','fyp-p85-continuation-preparation-absolute.timer'):
 p=subprocess.run(['systemctl','show',unit,'--property=ActiveState,SubState,ExecMainStartTimestamp,ExecMainStatus'],capture_output=True,text=True);units[unit]=p.stdout.strip()
value={'at_utc':datetime.now(timezone.utc).isoformat(),'run_id':'p85-01a116f7-3b82-7a79-8653-3aee62dc99e9','host_id':'i-034252c3e9b083abf','counts':counts,'active':active,'next_planned':dict(nextrow) if nextrow else None,'last_admission':json.loads(admission[0]) if admission else None,'units':units,'pause':json.loads((root/'pause.json').read_text()) if (root/'pause.json').exists() else None,'recent_notices':recent,'absolute_stop_utc':'2026-10-22T15:24:23.810674Z'}
for row in active:
 folder=root/'slots'/f"{row['sequence']:04d}"
 value['active_files']=[str(x.relative_to(folder)) for x in folder.rglob('*') if x.is_file() and '.sqlite' not in x.name][:60]
 logs=list(folder.glob('collector-*.log'))
 if logs:value['collector_tail']=logs[-1].read_text(errors='replace')[-3000:]
print(json.dumps(value))
PY

