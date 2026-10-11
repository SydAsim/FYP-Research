set -euo pipefail
umask 077
cd /opt/fyp-phase8-combined-v4
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-combined-v4:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'OLD_UNITS'
import subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from runner import unit_text,campaign_unit,watchdog_unit
from controls import Policy,read,write_new,hash_file
old=Path('/var/lib/p8-combined-v4/run');out=Path('/var/lib/p8-continuation-v7/deployment/retained-v4-unit-files-attempt3')
service,timer=unit_text(old,Policy.model_validate(read(old/'run.json')['policy']))
expected={'fyp-phase8-hardstop.service':service,'fyp-phase8-hardstop.timer':timer,'fyp-phase8-watchdog.service':watchdog_unit(old),'fyp-phase8-campaign.service':campaign_unit(old)}
for name,content in expected.items():
    p=Path('/etc/systemd/system')/name
    if p.is_symlink() or p.read_text()!=content:raise ValueError('OLD_UNIT_REPLACEMENT_OWNERSHIP_DRIFT:'+name)
for unit in ('fyp-phase8-campaign.service','fyp-phase8-watchdog.service'):
    assert subprocess.run(['systemctl','show',unit,'--property=MainPID','--value'],check=True,text=True,capture_output=True,timeout=10).stdout.strip()=='0'
subprocess.run(['systemctl','is-active','--quiet','fyp-p85-continuation-bootstrap-stop.timer'],check=True,timeout=10)
out.mkdir(mode=0o700,exist_ok=False)
write_new(out/'prior-unit-hashes.json',{name:hash_file(Path('/etc/systemd/system')/name) for name in expected})
subprocess.run(['systemctl','stop','fyp-phase8-hardstop.timer'],check=True,timeout=10)
for name in expected:(Path('/etc/systemd/system')/name).rename(out/name)
OLD_UNITS
cd /opt/fyp-phase8-continuation-v7
export PYTHONPATH=/opt/fyp-phase8-continuation-v7:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B artifacts/phase-8-runner-amendment/v4-complete/runner.py install-watchdog --root /var/lib/p8-continuation-v7/run
.venv/bin/python -B - <<'NEW_UNITS'
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from runner import verify_run,verify_host_timer
from controls import read,write_new,utc
from prelaunch_backup import verify_proof
from storage import S3Cloud
root=Path('/var/lib/p8-continuation-v7/run');a=verify_run(root);verify_host_timer(root)
cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/')
for phase in ('prelaunch','complete'):verify_proof(root,phase,cloud)
assert read(root/'pause.json')['reason']=='CONTINUATION_REVIEW_REQUIRED'
v={'status':'PASS','at_utc':utc().isoformat(),'watchdog_active':True,'exact_absolute_timer_active':True,'original_deadline':a.policy.stop_at.isoformat(),'both_backup_proofs_verified':True,'old_unit_files_preserved':True,'main_service_started':False}
write_new(root.parent/'deployment/controls-installed-attempt3.json',v);print(json.dumps(v))
NEW_UNITS
