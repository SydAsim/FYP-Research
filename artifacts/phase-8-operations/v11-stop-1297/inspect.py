"""External read-only triggering error inspection, no admission/replay or code changes."""
from pathlib import Path
import importlib.util
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('read_only_transport',ROOT/'artifacts/phase-8-results-share/v3/download.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.HERE=HERE
body=r'''
import json,sys,subprocess,hashlib
from pathlib import Path
from datetime import datetime,UTC
sys.path.insert(0,'/opt/fyp-phase8-continuation-v11/artifacts/phase-8-runner-amendment/v4-complete')
from closed145 import snapshot
root=Path('/var/lib/p8-continuation-v9/run');rows,notices=snapshot(root/'campaign.sqlite3')
def read(p):return json.loads(p.read_bytes())
def command(args):return subprocess.run(args,check=True,capture_output=True,text=True,timeout=20).stdout
pause=read(root/'pause.json')
events=[n for n in notices if n.get('kind') in ('PROTOCOL_STOP','PAUSED','PAUSE','BACKUP_FAILURE','DRIVER_FAILURE')][-12:]
j=command(['journalctl','-u','fyp-phase8-campaign.service','--since','2026-10-23 06:10:00 UTC','--until','2026-10-23 06:20:00 UTC','--no-pager','-o','json'])
messages=[json.loads(s)['MESSAGE'] for s in j.splitlines()]
interesting=[s for s in messages if any(k in s for k in ['STOP:','Error','Failed','failed','Traceback','VERIFIED BACKUP'])]
units=command(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','--property=Id,MainPID,ActiveState,SubState,Result,ExecStart,FragmentPath'])
print(json.dumps({'at':datetime.now(UTC).isoformat(),'pause':pause,'counts':{s:sum(r['state']==s for r in rows) for s in set(r['state'] for r in rows)},'last_rows':rows[1294:1299],'trigger_notices':events,'last_notices':notices[-8:],'campaign_messages':interesting[-12:],'units':units,'last_backup':read(root/'backups'/(rows[1296]['execution_id']+'.json')),'root_directories':[str(p) for p in root.parent.iterdir() if p.is_dir()]}))
'''
command="cd /opt/fyp-phase8-continuation-v11\nexport PYTHONDONTWRITEBYTECODE=1\n.venv/bin/python -B - <<'INSPECT_ONLY'\n"+body+"\nINSPECT_ONLY\n"
result=json.loads(m.run('inspect1297',command,90))
m.save('inspection-summary.json',result)
print(json.dumps(result,indent=2))
