set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd /opt/fyp-phase8-continuation-v9
export PYTHONPATH=/opt/fyp-phase8-continuation-v9:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'READ_ONLY'
import json,sys,hashlib,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,hash_file,utc
from handover import ro_rows
root=Path('/var/lib/p8-continuation-v9/run');rows=ro_rows(root);first=rows[0]
receipt=read(root/'backups'/(first['execution_id']+'.json'))
locations={}
for name in ('exports','historical','restart-history'):
    p=root/name
    locations[name]={'exists':p.exists(),'direct_names':sorted(q.name for q in p.iterdir())[:20] if p.is_dir() else []}
paths={}
for p in (root/'exports/0001/export.json',root/'exports'/f'{first["execution_id"]}.json',
    root/'exports/0001.json',Path(receipt['local']),
    Path('/opt/fyp-phase8-combined-v4/artifacts/phase-8-runner-amendment/v4-complete/retained-archives/0001.tar.gz'),
    root/'historical/first-slot/executions'/first['execution_id']/'export.json'):
    paths[str(p)]={'exists':p.is_file(),'bytes':p.stat().st_size if p.is_file() else None}
    if p.is_file() and p.suffix=='.json':paths[str(p)]['sha256']=hash_file(p)
print(json.dumps({'kind':'READ_ONLY_FAILED_GATE_LAYOUT','at':utc().isoformat(),'first':first,'receipt':receipt,'locations':locations,'paths':paths,
    'backed_up':sum(r['state']=='BACKED_UP' for r in rows),'planned':sum(r['state']=='PLANNED' for r in rows),
    'next':rows[145],'pause':read(root/'pause.json'),'pause_sha256':hash_file(root/'pause.json'),
    'root_source':read(root/'run.json')['source'],'original_clock_renamed':(root/'retained-host-clock-before-v10.json').exists(),
    'metadata_stage_wrote_history':(root/'restart-history/v9-before-v10').exists(),
    'units':subprocess.run(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','--property=Id,ActiveState,MainPID'],check=True,text=True,capture_output=True,timeout=10).stdout,'outcome_writes':0}))
READ_ONLY
