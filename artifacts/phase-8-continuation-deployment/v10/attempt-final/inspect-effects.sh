set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v9
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v9:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'READ_ONLY'
import json,sys,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,hash_file,utc
from handover import ro_rows
from runner import campaign_unit,watchdog_unit
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v10/deployment')
rows=ro_rows(root);assert len(rows)==1500
assert all(r['state']=='BACKED_UP' for r in rows[:145]) and all(r['state']=='PLANNED' for r in rows[145:])
assert rows[145]['execution_id']=='01a11705-11f1-772d-8190-c43552871801' and rows[145]['arm']=='P2' and rows[145]['attempt']==1
pause=read(root/'pause.json');assert pause['reason']=='DRIVER_FAILURE' and pause['at']=='2026-10-10T18:06:53.908883+00:00'
units=('fyp-phase8-campaign.service','fyp-phase8-watchdog.service')
contents={u:(Path('/etc/systemd/system')/u).read_text() for u in units}
expected={units[0]:campaign_unit(root),units[1]:watchdog_unit(root)}
assert all(contents[u]==expected[u] and not (Path('/etc/systemd/system')/u).is_symlink() for u in units),'OLD_UNIT_OWNERSHIP_DRIFT'
state=subprocess.run(['systemctl','show',*units,'--property=Id,ActiveState,SubState,MainPID,ExecStart,FragmentPath,Result,UnitFileState'],check=True,text=True,capture_output=True,timeout=20).stdout
effects={}
for name in ('quiesce-old-units.sh','old-unit-state-before-quiesce.json','old-units-quiesced.json'):
    path=dep/name
    if path.exists():
        effects[name]={'exists':True,'bytes':path.stat().st_size,'sha256':hash_file(path)}
        if name=='quiesce-old-units.sh':assert hash_file(path)=='7eefdb7535e94d39d39bc02facb54c7c97aeb9160f6ec16f8ae59b81ef3575ff','OLD_TRANSFER_HASH_DRIFT'
        else:effects[name]['record']=read(path)
    else:effects[name]={'exists':False}
processes=subprocess.run(['ps','-eo','pid,args'],check=True,capture_output=True,text=True,timeout=10).stdout
active=[line for line in processes.splitlines() if 'bash /var/lib/p8-continuation-v10/deployment/quiesce-old-units.sh' in line or "bash '/var/lib/p8-continuation-v10/deployment/quiesce-old-units.sh'" in line]
assert not active,'OLD_COMMAND_STILL_EXECUTING'
print(json.dumps({'status':'PASS_READ_ONLY_EFFECT_INSPECTION_NOT_QUIESCENCE','at':utc().isoformat(),
    'effects':effects,'pause':pause,'pause_sha256':hash_file(root/'pause.json'),'state':state,
    'unit_contents':contents,'backed_up':145,'planned':1355,'next':rows[145],
    'all_rows_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),
    'active_original_command_processes':active,'writes_performed':False,'historical_execution_unknown_if_no_original_proof':not (dep/'old-units-quiesced.json').exists()}))
READ_ONLY
