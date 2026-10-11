set -euo pipefail
umask 077
python3 - <<'RECEIPT'
from pathlib import Path
p=Path('/var/lib/fyp-owner/combined-v4-receipts/CONTINUATION_LAUNCH.json')
with p.open('x') as f:f.write('{\n  "kind": "CONTINUATION_LAUNCH",\n  "package_hash": "a869745a6c1807e4f2427cc9597e5d85f41a2b4eb2aa4aa8abd4bdb8cc9b7306",\n  "predecessor_hash": "997268c5293b03c2bd84105661dfacab53a44f8124d8b54d9ea5e481dc05cb8d",\n  "policy_sha256": "87ff3ac98c8f7646ecd25ecb641e7ffd49e5008a1d0b3c8f97cca6a7d091e246",\n  "identities_sha256": "ab585ba36f9a78c5058916e412dca407d57db83a893c32018b60ff3d071838c0",\n  "parent_freeze_sha256": "0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2",\n  "immediate_parent_freeze_sha256": "49ec78e719d9d28e017f62e6a40dd69cc236a45c5406d5be1a209ef59b9d2c86",\n  "first_export_sha256": "283001dc1a5904f3e8b4de893ef658d2e7fe8053b8e98ed7baad6f242d318d8b",\n  "second_export_sha256": "bd4d32f4968eaff243d65d9cfe8fad36c603cd709c09ee7fdebd29746e90da42",\n  "expires_at": "2026-10-22T15:24:23.810674+00:00",\n  "signer": "Explicit human instruction recorded by local FYP operator",\n  "readiness_sha256": "f22479a108d223f7b65837de899f131438c2b11c671621916760eea343eb33df",\n  "instance_id": "i-057344e5372faf62f",\n  "signature": "92de93da4cc07ccce666e7376595bd6601c34821fa21e6fca289cfc56c1d2c67"\n}\n')
p.chmod(0o600)
RECEIPT
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
