set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v9
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v9:/opt/fyp-phase8-continuation-v10/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v10/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'OLD'
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,Policy,write_new,hash_file
from runner import campaign_unit,watchdog_unit,unit_text
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v10/deployment');out=dep/'prior-unit-files-final';out.mkdir(mode=0o700,exist_ok=False)
service,timer=unit_text(root,Policy.model_validate(read(root/'run.json')['policy']))
expected={'fyp-phase8-hardstop.service':service,'fyp-phase8-hardstop.timer':timer,'fyp-phase8-watchdog.service':watchdog_unit(root),'fyp-phase8-campaign.service':campaign_unit(root)}
for name,text in expected.items():
    p=Path('/etc/systemd/system')/name
    assert not p.is_symlink() and p.read_text()==text,'OLD_UNIT_OWNERSHIP_DRIFT:'+name
for u in ('fyp-phase8-campaign.service','fyp-phase8-watchdog.service'):
    assert subprocess.run(['systemctl','show',u,'--property=MainPID','--value'],check=True,text=True,capture_output=True,timeout=10).stdout.strip()=='0'
write_new(out/'manifest.json',{name:hash_file(Path('/etc/systemd/system')/name) for name in expected})
subprocess.run(['systemctl','stop','fyp-phase8-hardstop.timer'],check=True,timeout=10)
for name in expected:(Path('/etc/systemd/system')/name).rename(out/name)
OLD
set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v10
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v10:/opt/fyp-phase8-continuation-v10/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v10/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'NEW'
import json,sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,write_new,utc,hash_file
from runner import unit_text,campaign_unit,watchdog_unit
from handover import ContinuationAuthority
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v10/deployment')
a=ContinuationAuthority(root,read(root/'run.json'));a.verify(prelaunch=True)
service,timer=unit_text(root,a.policy)
expected={'fyp-phase8-hardstop.service':service,'fyp-phase8-hardstop.timer':timer,'fyp-phase8-watchdog.service':watchdog_unit(root),'fyp-phase8-campaign.service':campaign_unit(root)}
for name,text in expected.items():
    with (Path('/etc/systemd/system')/name).open('x') as f:f.write(text)
bootstrap=Path('/etc/systemd/system/fyp-p85-continuation-bootstrap-stop.timer')
old=bootstrap.read_text()
assert not bootstrap.is_symlink() and old=='[Unit]\nDescription=Original campaign deadline, including paused time\n[Timer]\nOnCalendar=2026-10-22 15:24:23 UTC\nPersistent=true\nAccuracySec=1s\nUnit=fyp-p85-continuation-bootstrap-stop.service\n[Install]\nWantedBy=timers.target\n'
subprocess.run(['systemctl','stop',bootstrap.name],check=True,timeout=10)
bootstrap.rename(dep/'prior-unit-files-final'/bootstrap.name)
with bootstrap.open('x') as f:f.write(old.replace('2026-10-22','2026-10-25'))
subprocess.run(['systemctl','daemon-reload'],check=True,timeout=20)
subprocess.run(['systemctl','enable','--now','fyp-phase8-hardstop.timer',bootstrap.name],check=True,timeout=20)
for u in ('fyp-phase8-hardstop.timer',bootstrap.name):subprocess.run(['systemctl','is-active','--quiet',u],check=True,timeout=10)
write_new(dep/'timer-files-prepared-final.json',{'status':'PASS_TIMERS_ACTIVE_WATCHDOG_NOT_STARTED','at':utc().isoformat(),'units':{name:hash_file(Path('/etc/systemd/system')/name) for name in expected},'stop_at':a.policy.stop_at.isoformat(),'host_hours':a.policy.host_hours,'watchdog_active':False,'main_started':False})
print(json.dumps(read(dep/'timer-files-prepared-final.json')))
NEW
