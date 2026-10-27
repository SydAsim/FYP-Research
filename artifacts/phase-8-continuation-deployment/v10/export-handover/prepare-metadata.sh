set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v10
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v10:/opt/fyp-phase8-continuation-v10/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v10/.venv-transport/lib/python3.12/site-packages
 .venv/bin/python -B - <<'METADATA'
import json,sys,hashlib,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,write_new,hash_file,Journal,utc
from closed145 import verify_retained_root
from handover import ContinuationAuthority,bind_host_segment,original_policy
from operational_limits import LIMITS_SHA256
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v10/deployment')
for u in ('fyp-phase8-campaign.service','fyp-phase8-watchdog.service'):
    assert subprocess.run(['systemctl','show',u,'--property=MainPID','--value'],check=True,text=True,capture_output=True,timeout=10).stdout.strip()=='0'
    assert subprocess.run(['systemctl','is-active',u],text=True,capture_output=True,timeout=10).stdout.strip()=='inactive'
checked=verify_retained_root(root);assert checked['backed_up']==145 and checked['planned']==1355
assert not (root/'retained-host-clock-before-v10.json').exists(),'RETAIN_PREVIOUS_BIND_ATTEMPT_STOP'
config=read(root/'run.json');original_policy(config['policy'])
historical=root/'restart-history'/'v9-before-v10';historical.mkdir(mode=0o700,exist_ok=False)
preserved={}
for name in ('run.json','binding-seal.json','continuation-readiness.json','prelaunch-backup-proof.json','complete-backup-proof.json'):
    p=root/name
    if p.exists():
        preserved[name]=hash_file(p);p.rename(historical/name)
(historical/'previous-host-clock.json').write_bytes((root/'host-clock.json').read_bytes())
write_new(historical/'preservation.json',{'at':utc().isoformat(),'preserved':preserved,'clock_sha256':hash_file(root/'host-clock.json'),'no_regrading':True})
config.update(source=str(Path.cwd()),manifest=str(Path.cwd()/'artifacts/phase-8-review-freeze/v2/review-inventory.json'),
    continuation={'manifest':'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json','receipts':'/var/lib/fyp-owner/continuation-v10-receipts'},operational_limits_sha256=LIMITS_SHA256)
write_new(root/'run.json',config)
seal={'run':hash_file(root/'run.json'),'bindings':hash_file(root/'bindings.json')};write_new(root/'binding-seal.json',seal)
j=Journal(root);j.event('BINDINGS_SEALED',**seal)
a=ContinuationAuthority(root,config);a.verify(prelaunch=True)
bind_host_segment(root)
from runner import verify_clock
verify_clock(root,a.policy)
checked=verify_retained_root(root)
write_new(dep/'metadata-prepared-final.json',{'status':'PASS','at':utc().isoformat(),'backed_up':145,'planned':1355,'next_sequence':146,'next_execution_id':checked['next']['execution_id'],'original_pause_preserved':True,'run_sha256':seal['run'],'clock_sha256':hash_file(root/'host-clock.json'),'historical_metadata':preserved,'driver_calls':0})
print(json.dumps(read(dep/'metadata-prepared-final.json')))
METADATA
