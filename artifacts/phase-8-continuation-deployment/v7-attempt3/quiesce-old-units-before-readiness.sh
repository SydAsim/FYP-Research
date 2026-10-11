set -euo pipefail
umask 077
cd /opt/fyp-phase8-combined-v4
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-combined-v4:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'PY'
import json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,hash_file,write_new,utc
dep=Path('/var/lib/p8-continuation-v7/deployment');root=Path('/var/lib/p8-combined-v4/run')
units=('fyp-phase8-campaign.service','fyp-phase8-watchdog.service')
state=subprocess.run(['systemctl','show',*units,'--property=Id,ActiveState,SubState,MainPID,ExecStart,FragmentPath,Result'],check=True,text=True,capture_output=True,timeout=20).stdout
content={name:(Path('/etc/systemd/system')/name).read_text() for name in units}
pause=read(root/'pause.json');pause_hash=hash_file(root/'pause.json')
write_new(dep/'old-unit-state-before-quiesce-attempt3.json',{'at_utc':utc().isoformat(),'state':state,'unit_text':content,'pause':pause,'pause_sha256':pause_hash})
assert pause['reason']=='PROTOCOL_STOP'
parent=read(Path('/opt/fyp-phase8-continuation-v7/artifacts/phase-8-runner-amendment/v4-complete/parent-v4-inventory.json'))
for name,digest in parent['files'].items():
    if hash_file(Path.cwd()/name)!=digest:raise ValueError('OLD_FROZEN_SOURCE_DRIFT:'+name)
from runner import campaign_unit,watchdog_unit
expected={units[0]:campaign_unit(root),units[1]:watchdog_unit(root)}
for name in units:
    p=Path('/etc/systemd/system')/name
    if p.is_symlink() or content[name]!=expected[name]:raise ValueError('OLD_UNIT_OWNERSHIP_DRIFT:'+name)
from handover import ro_rows
rows=ro_rows(root)
pinned=read(Path('/opt/fyp-phase8-continuation-v7/artifacts/phase-8-runner-amendment/v4-complete/closed-82/ledger-read-only.json'))['rows']
assert rows==pinned
write_new(dep/'old-unit-ownership-attempt3.json',{'status':'PASS','unit_sha256':{name:hash_file(Path('/etc/systemd/system')/name) for name in units},'original_rows_unchanged':True,'units_owned_by_exact_original_run':True})
subprocess.run(['systemctl','stop',*units],check=True,timeout=40)
for name in units:
    pid=subprocess.run(['systemctl','show',name,'--property=MainPID','--value'],check=True,text=True,capture_output=True,timeout=10).stdout.strip()
    active=subprocess.run(['systemctl','is-active',name],text=True,capture_output=True,timeout=10)
    if pid!='0' or active.stdout.strip()!='inactive':raise ValueError('OLD_UNIT_NOT_INACTIVE:'+name)
assert hash_file(root/'pause.json')==pause_hash and read(root/'pause.json')==pause
assert ro_rows(root)==pinned
write_new(dep/'old-unit-quiescence-attempt3.json',{'status':'PASS','at_utc':utc().isoformat(),'units':list(units),'all_MainPID_zero':True,'all_inactive':True,'pause_sha256':pause_hash,'old_pause_preserved':True,'all_1500_original_rows_unchanged':True})
print(json.dumps(read(dep/'old-unit-quiescence-attempt3.json')))
PY
