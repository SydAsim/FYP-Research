set -euo pipefail
umask 077
install -d -m 700 /var/lib/p8-continuation-v10/deployment
cd /opt/fyp-phase8-continuation-v9
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v9:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'PY'
import json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,write_new,hash_file,utc
from runner import campaign_unit,watchdog_unit
from handover import ro_rows
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v10/deployment')
units=('fyp-phase8-campaign.service','fyp-phase8-watchdog.service')
state=subprocess.run(['systemctl','show',*units,'--property=Id,ActiveState,SubState,MainPID,ExecStart,FragmentPath,Result,UnitFileState'],check=True,text=True,capture_output=True,timeout=20).stdout
contents={u:(Path('/etc/systemd/system')/u).read_text() for u in units}
pause_hash=hash_file(root/'pause.json');pause=read(root/'pause.json')
write_new(dep/'attempt-final-unit-state-before-quiesce.json',{'at_utc':utc().isoformat(),'state':state,'contents':contents,'pause':pause,'pause_sha256':pause_hash})
assert pause['reason']=='DRIVER_FAILURE' and pause['at']=='2026-10-10T18:06:53.908883+00:00'
expected={units[0]:campaign_unit(root),units[1]:watchdog_unit(root)}
for u in units:
    assert not (Path('/etc/systemd/system')/u).is_symlink() and contents[u]==expected[u], 'OLD_UNIT_OWNERSHIP_DRIFT'
inventory=read(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json')
assert inventory['package_hash']=='5cbf273011c505984fe103955a94a256b1c84d1683de74cfa7a2a396cc223b60'
for name,digest in inventory['files'].items():
    assert hash_file(Path.cwd()/name)==digest,'OLD_FROZEN_SOURCE_DRIFT:'+name
rows=ro_rows(root)
assert len(rows)==1500 and all(r['state']=='BACKED_UP' for r in rows[:145]) and all(r['state']=='PLANNED' for r in rows[145:])
assert rows[145]['execution_id']=='01a11705-11f1-772d-8190-c43552871801'
subprocess.run(['systemctl','stop',*units],check=True,timeout=40)
for u in units:
    assert subprocess.run(['systemctl','show',u,'--property=MainPID','--value'],check=True,text=True,capture_output=True,timeout=10).stdout.strip()=='0'
    assert subprocess.run(['systemctl','is-active',u],text=True,capture_output=True,timeout=10).stdout.strip()=='inactive'
assert hash_file(root/'pause.json')==pause_hash and ro_rows(root)==rows
write_new(dep/'attempt-final-units-quiesced.json',{'status':'PASS','at_utc':utc().isoformat(),'pause_sha256':pause_hash,'original_pause_preserved':True,'all_original_rows_preserved':True,'old_source_package':inventory['package_hash'],'units_inactive':list(units),'backed_up':145,'planned':1355,'next_sequence':146})
print(json.dumps(read(dep/'attempt-final-units-quiesced.json')))
PY
