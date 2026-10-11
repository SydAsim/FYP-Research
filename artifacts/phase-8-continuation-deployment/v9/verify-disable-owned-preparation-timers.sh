set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v9
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v9:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'TIMERS'
import json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,write_new,utc
from handover import ro_rows
from runner import verify_host_timer
root=Path('/var/lib/p8-continuation-v9/run');rows=ro_rows(root)
assert rows[120]['state'] not in ('PLANNED','BACKED_UP') and rows[120]['execution_id']=='01a11705-11f1-75f4-b64e-8f0a3679518b'
assert not (root/'pause.json').exists()
verify_host_timer(root)
subprocess.run(['systemctl','is-active','--quiet','fyp-phase8-campaign.service'],check=True,timeout=10)
expected={
'fyp-p85-continuation-preparation-stop.timer':'[Unit]\nDescription=Bounded fresh-host preparation, two hours maximum\n[Timer]\nOnActiveSec=2h\nAccuracySec=1s\nUnit=fyp-p85-continuation-bootstrap-stop.service\n[Install]\nWantedBy=timers.target\n',
'fyp-p85-combined-preparation-absolute.timer':'[Unit]\nDescription=Bounded new-host preparation; original campaign deadline unchanged\n[Timer]\nOnCalendar=2026-10-08 21:50:50 UTC\nPersistent=true\nAccuracySec=1s\nUnit=fyp-p85-continuation-bootstrap-stop.service\n[Install]\nWantedBy=timers.target\n'}
records={}
for name,content in expected.items():
    p=Path('/etc/systemd/system')/name
    assert not p.is_symlink() and p.read_text()==content
    records[name]={'unit_text':content,'state_before':subprocess.run(['systemctl','show',name,'--property=ActiveState,SubState'],check=True,text=True,capture_output=True,timeout=10).stdout}
write_new(root.parent/'deployment/owned-preparation-timers-before-disable-attempt3.json',records)
subprocess.run(['systemctl','disable','--now',*expected],check=True,timeout=20)
for name in expected:
    state=subprocess.run(['systemctl','is-active',name],text=True,capture_output=True,timeout=10)
    enabled=subprocess.run(['systemctl','is-enabled',name],text=True,capture_output=True,timeout=10)
    assert state.stdout.strip()=='inactive' and enabled.stdout.strip()=='disabled'
verify_host_timer(root)
subprocess.run(['systemctl','is-active','--quiet','fyp-p85-continuation-bootstrap-stop.timer'],check=True,timeout=10)
value={'status':'PASS','at_utc':utc().isoformat(),'owned_preparation_timers_disabled':list(expected),'absolute_timers_and_watchdog_preserved':True,'sequence121_state':rows[120]['state']}
write_new(root.parent/'deployment/preparation-timers-disabled-attempt3.json',value);print(json.dumps(value))
TIMERS
