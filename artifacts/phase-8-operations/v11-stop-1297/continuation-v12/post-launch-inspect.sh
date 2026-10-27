set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v12:/opt/fyp-phase8-continuation-v12/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v12/.venv-transport/lib/python3.12/site-packages
cd /opt/fyp-phase8-continuation-v12
.venv/bin/python -B - <<'READ_ONLY_RUNNING'
import hashlib,json,sys,subprocess
from datetime import UTC,datetime
from pathlib import Path
sys.path.insert(0,'/opt/fyp-phase8-continuation-v12/artifacts/phase-8-runner-amendment/v4-complete')
from controls import read,hash_file
from closed1297 import verify
from runner import meter
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v12/deployment')
prefix=verify(root)
assert not (root/'pause.json').exists()
assert hash_file(root/'retained-protocol1297-pause-v12.json')=='7cf255c9359c9c88951eac98eade347adad2831ad1fd522ea1eab33e1c616ab8'
assert prefix['next']['execution_id']=='01a11705-11f4-7c05-9897-af35348a8028'
state=subprocess.run(['systemctl','show','fyp-phase8-campaign.service','fyp-phase8-watchdog.service','--property=Id,ActiveState,SubState,MainPID'],capture_output=True,text=True,check=True,timeout=10).stdout
assert state.count('ActiveState=active')==2 and state.count('SubState=running')==2
print(json.dumps({'status':'PASS_POST_LAUNCH_READ_ONLY','at':datetime.now(UTC).isoformat(),'original1297_prefix_still_verified':True,'source_package':read(Path('/opt/fyp-phase8-continuation-v12/artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json'))['package_hash'],'first_admitted':prefix['next'],'old_pause_retained_sha256':hash_file(root/'retained-protocol1297-pause-v12.json'),'actual_release':read(dep/'actual-release.json'),'prelaunch':read(root/'prelaunch-backup-proof.json'),'complete':read(root/'complete-backup-proof.json'),'preparation_backup_growth_bytes':meter(root)['backup_bytes']-read(dep/'live-checks.json')['resource_sample']['backup_bytes'],'resources':meter(root),'service_state':state,'timers':subprocess.run(['systemctl','show','fyp-phase8-hardstop.timer','fyp-p85-continuation-bootstrap-stop.timer','fyp-v12-admission-cutoff.timer','--property=Id,ActiveState,NextElapseUSecRealtime'],capture_output=True,text=True,check=True,timeout=10).stdout}))
READ_ONLY_RUNNING
