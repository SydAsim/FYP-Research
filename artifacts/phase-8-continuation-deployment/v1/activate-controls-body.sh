cd /opt/fyp-phase8-continuation-v1
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B artifacts/phase-8-continuation/v1/runner.py verify --root /var/lib/p8-continuation/run
.venv/bin/python -B artifacts/phase-8-continuation/v1/runner.py install-watchdog --root /var/lib/p8-continuation/run
systemctl is-active fyp-phase8-hardstop.timer fyp-phase8-watchdog.service fyp-p85-continuation-bootstrap-stop.timer fyp-p85-continuation-preparation-stop.timer
systemctl list-timers fyp-phase8-hardstop.timer fyp-p85-continuation-bootstrap-stop.timer fyp-p85-continuation-preparation-stop.timer --no-pager
.venv/bin/python -B - <<'PY'
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-continuation/v1'))
from controls import Journal,hash_file,read,utc,write_new
from runner import cloud_for,verify_host_timer,verify_run
from storage import final_backup,upload
from postflight import recover
from transport import S3Store
from handover import closed_boundary,verify_members
root=Path('/var/lib/p8-continuation/run');dep=Path('/var/lib/p8-continuation/deployment')
authority=verify_run(root);verify_host_timer(root);journal=Journal(root)
closed_boundary(journal.rows(),read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows'])
archive=final_backup(journal,Path('/var/lib/p8-continuation/backup'))
cloud=cloud_for(root);proof=upload(journal,cloud,authority.policy,archive);cloud.verify(proof)
recovered=recover(proof,root.parent/'authorization-backup-readback',S3Store('fyp-research'));verify_members(recovered/'slot')
journal.event('CONTINUATION_AUTHORIZED_PRELAUNCH_BACKUP_VERIFIED',proof=proof.model_dump())
write_new(dep/'authorized-prelaunch-backup.json',{'kind':'AUTHORIZED_PRELAUNCH_NOT_EXECUTION_OR_COMPLETION','status':'PASS','at_utc':utc().isoformat(),'instance_id':'i-034252c3e9b083abf','readiness_sha256':hash_file(root/'continuation-readiness.json'),'cloud':proof.model_dump(),'local':str(archive),'source_and_authority':'PASS','active_watchdog_and_absolute_timers':'PASS','first_BACKED_UP':1,'remaining_PLANNED':1499,'main_started':False})
print(json.dumps(read(dep/'authorized-prelaunch-backup.json')))
PY
printf '%s\n' AUTHORIZED_CONTROLS_AND_BACKUP_VERIFIED_MAIN_NOT_STARTED
