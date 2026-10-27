set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v11
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v11:/opt/fyp-phase8-continuation-v11/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v11/.venv-transport/lib/python3.12/site-packages
timeout --signal=TERM --kill-after=5s 240s .venv/bin/python -B - <<'COMPLETE'
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,write_new,utc
from runner import meter
from handover import ContinuationAuthority
from prelaunch_backup import run
from storage import S3Cloud
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v11/deployment')
a=ContinuationAuthority(root,read(root/'run.json'));a.verify()
before=meter(root)['backup_bytes'];ready=read(root/'continuation-readiness.json')
cloud_config=read(root/'cloud.json')
run(root,root.parent/'backup','complete',S3Cloud(cloud_config['bucket'],cloud_config['prefix']))
after=meter(root)['backup_bytes'];assert after-before<=ready['complete_backup_stage_bound_bytes'],'COMPLETE_BACKUP_FOOTPRINT_BOUND_EXCEEDED'
proof=read(root/'complete-backup-proof.json');write_new(dep/'complete-stage.json',{'status':'PASS_INDEPENDENT_READBACK','at':utc().isoformat(),'backup_growth_bytes':after-before,'bound_bytes':ready['complete_backup_stage_bound_bytes'],'proof':proof})
print(json.dumps({'status':'PASS_COMPLETE_INDEPENDENT_READBACK','backup_growth_bytes':after-before,'proof':proof}))
COMPLETE
