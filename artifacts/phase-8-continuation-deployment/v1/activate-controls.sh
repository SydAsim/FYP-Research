#!/bin/bash
set -euo pipefail
umask 077
python3 - <<'RECEIPT'
import base64,hashlib,os
from pathlib import Path
raw=base64.b64decode('ew0KICAia2luZCI6ICJDT05USU5VQVRJT05fTEFVTkNIIiwNCiAgInBhY2thZ2VfaGFzaCI6ICJjMzA4MjIyMDk2Y2YzYzkwMjZhYTI3NWU3M2ZkN2Q3NWJjZTM4NmU2NDE4MjQzMzBmMzg1ZGFiMDJkNGI2MDlmIiwNCiAgInByZWRlY2Vzc29yX2hhc2giOiAiNmM0YWNhZjgyYjlkZDI0MmJhMDYwOTAxYWNiM2JkNGJlMTVhZGM0M2U3YzJkMTg0NjQ4ODljNDU1YzkyMjk2ZiIsDQogICJwb2xpY3lfc2hhMjU2IjogIjg3ZmYzYWM5OGM4Zjc2NDZlY2QyNWVjYjY0MWU3ZmZkNDllNTAwOGExZDBiM2M4Zjk3Y2NhNmE3ZDA5MWUyNDYiLA0KICAiaWRlbnRpdGllc19zaGEyNTYiOiAiNWFhNTZmZWYxMTZiNTViODM5YjU4YzA1Yjg1ZDdjZDFkM2ViMDMwYWNiMWI2ZDljZDE1NmU2NDBiMjg1ZWQ4ZCIsDQogICJwYXJlbnRfZnJlZXplX3NoYTI1NiI6ICIwNDM1YTM3ZjUzNGI4YThjZGU3NzEwNDg0MGMwZmI4MTMyMzAxMWY3ZjIxZDkzYjRlYmMzODI2MGEwOTIyMmIyIiwNCiAgImZpcnN0X2V4cG9ydF9zaGEyNTYiOiAiMjgzMDAxZGMxYTU5MDRmM2U4YjRkZTg5M2VmNjU4ZDJlN2ZlODA1M2I4ZTk4ZWQ3YmFhZDZmMjQyZDMxOGQ4YiIsDQogICJleHBpcmVzX2F0IjogIjIwMjYtMTAtMjJUMTU6MjQ6MjMuODEwNjc0KzAwOjAwIiwNCiAgInNpZ25lciI6ICJTZXBhcmF0ZSBleHBsaWNpdCBodW1hbiBjb250aW51YXRpb24gbGF1bmNoIGluc3RydWN0aW9uIHJlY29yZGVkIGJ5IGxvY2FsIEZZUCBvcGVyYXRvciIsDQogICJyZWFkaW5lc3Nfc2hhMjU2IjogIjE0ZmQ1M2QyZWMxNmI3YjEyMWMyMGIzODZmYmJkODU2OTk0MjQ0MzkzMzhkOWU0YTUwNzg5NGY0MDAxMWNiZjciLA0KICAiaW5zdGFuY2VfaWQiOiAiaS0wMzQyNTJjM2U5YjA4M2FiZiIsDQogICJzaWduYXR1cmUiOiAiMzA1NGM3ODU4NWViMTA3NGZlMjBkNjU3YzhlMGE2NzRiMTBhZmY2YmNkNWM3YjNhZDNmMGM2ZDUyNTcxYzk0MCINCn0NCg==')
if hashlib.sha256(raw).hexdigest()!='ba79d85308bb7e27d9795e749ff36afa3ee1d453ea00995ee883e8045aad9d13':raise ValueError('LAUNCH_RECEIPT_TRANSFER_DRIFT')
p=Path('/var/lib/fyp-owner/continuation-receipts/CONTINUATION_LAUNCH.json')
with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
p.chmod(0o600)
RECEIPT
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
