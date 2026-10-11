cd /opt/fyp-phase8-combined-v4
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B artifacts/phase-8-runner-amendment/v4-complete/runner.py install-watchdog --root /var/lib/p8-combined-v4/run
.venv/bin/python -B - <<'PY'
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import Journal,read,utc,write_new
from runner import verify_run,verify_host_timer
from handover import verify_imported_first,verify_members
from storage import S3Cloud,final_backup,upload
from postflight import recover
from transport import S3Store
root=Path('/var/lib/p8-combined-v4/run');dep=root.parent/'deployment'
a=verify_run(root);verify_host_timer(root);verify_imported_first(root)
j=Journal(root);cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/')
archive=final_backup(j,root.parent/'backup')
p=upload(j,cloud,a.policy,archive);cloud.verify(p)
back=recover(p,root.parent/'authorized-prelaunch-readback',S3Store('fyp-research'))
verify_members(back/'slot');verify_imported_first(back/'slot')
j.event('V4_AUTHORIZED_PRELAUNCH_BACKUP_VERIFIED',proof=p.model_dump())
v={'status':'PASS','at_utc':utc().isoformat(),'instance_id':'i-057344e5372faf62f','backup':p.model_dump(),'authority':a.verify(),'watchdog_and_absolute_timer_verified':True,'driver_calls':0,'main_started':False}
write_new(dep/'authorized-prelaunch-backup.json',v);print(json.dumps(v))
PY
systemctl is-active fyp-phase8-watchdog.service fyp-phase8-hardstop.timer fyp-p85-continuation-bootstrap-stop.timer fyp-p85-combined-preparation-absolute.timer
