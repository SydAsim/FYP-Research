set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v10
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v10:/opt/fyp-phase8-continuation-v10/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v10/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B - <<'ANCHOR'
import json,sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,write_new,hash_file,utc
from handover import ContinuationAuthority,bind_host_segment
from closed145 import verify_retained_root
from runner import verify_clock
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v10/deployment')
for u in ('fyp-phase8-campaign.service','fyp-phase8-watchdog.service'):
 assert subprocess.run(['systemctl','show',u,'--property=MainPID','--value'],check=True,text=True,capture_output=True,timeout=10).stdout.strip()=='0'
checked=verify_retained_root(root);assert checked['backed_up']==145 and checked['planned']==1355
config=read(root/'run.json');assert config['source']=='/opt/fyp-phase8-continuation-v10'
assert hash_file(root/'run.json')=='367ead4efc7b2e8feac630406142268029ac3455a6ad1f88d32bb6856376ae83'
pause_hash=hash_file(root/'pause.json');assert pause_hash=='28ea1aec440408f1d9e467ece07e54c39485d14c29434dc79b35b9460919d519'
a=ContinuationAuthority(root,config);a.verify(prelaunch=True)
history=root/'restart-history/capacity-resume-20261013';history.mkdir(mode=0o700,exist_ok=False)
old=root/'retained-host-clock-before-v10.json';previous=hash_file(root/'host-clock.json')
assert old.is_file();old_hash=hash_file(old);old.rename(history/old.name)
# Exact qualified binder now has an empty retained target; it preserves previous v10 anchor there.
bind_host_segment(root)
assert hash_file(root/'retained-host-clock-before-v10.json')==previous and hash_file(history/old.name)==old_hash
verify_clock(root,a.policy)
assert hash_file(root/'pause.json')==pause_hash and hash_file(root/'run.json')=='367ead4efc7b2e8feac630406142268029ac3455a6ad1f88d32bb6856376ae83'
record={'status':'PASS','at':utc().isoformat(),'backed_up':145,'planned':1355,'next_sequence':146,'next_execution_id':checked['next']['execution_id'],'original_pause_preserved':True,'clock_sha256':hash_file(root/'host-clock.json'),'previous_v10_clock_sha256':previous,'previous_v9_clock_sha256':old_hash,'new_boot_anchor_only':True,'old_metadata_migration_repeated':False,'original_start':a.policy.host_started_at.isoformat(),'stop_at':a.policy.stop_at.isoformat(),'driver_calls':0}
write_new(history/'anchor-provenance.json',record);write_new(dep/'metadata-prepared-capacity.json',record);print(json.dumps(record))
ANCHOR
