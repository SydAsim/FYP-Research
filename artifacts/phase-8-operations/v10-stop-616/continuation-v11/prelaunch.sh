set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v11
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v11:/opt/fyp-phase8-continuation-v11/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v11/.venv-transport/lib/python3.12/site-packages
timeout --signal=TERM --kill-after=5s 240s .venv/bin/python -B - <<'BACKUP'
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,write_new,utc
from prelaunch_backup import run
from storage import S3Cloud
root=Path('/var/lib/p8-continuation-v9/run');dep=Path('/var/lib/p8-continuation-v11/deployment')
assert read(dep/'live-checks.json')['status']=='PASS' and read(dep/'root-resize-verified.json')['status']=='PASS_ACTUAL_FILESYSTEM_EXPANSION'
cloud_config=read(root/'cloud.json')
run(root,root.parent/'backup','prelaunch',S3Cloud(cloud_config['bucket'],cloud_config['prefix']))
proof=read(root/'prelaunch-backup-proof.json')
write_new(dep/'prelaunch-stage.json',{'at':utc().isoformat(),'status':'PASS_INDEPENDENT_READBACK','proof':proof})
print(json.dumps({'status':'PASS_PRELAUNCH_INDEPENDENT_READBACK','proof':proof}))
BACKUP
