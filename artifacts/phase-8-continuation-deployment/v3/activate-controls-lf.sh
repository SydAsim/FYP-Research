set -euo pipefail
umask 077
python3 - <<'RECEIPT'
from pathlib import Path
p=Path('/var/lib/fyp-owner/combined-v3-receipts/CONTINUATION_LAUNCH.json')
with p.open('x') as f:f.write('{\n  "kind": "CONTINUATION_LAUNCH",\n  "package_hash": "2963b5b1b88b33b39bd66010dc9f7efa0914ea55cfd7014625ed65ecd3100736",\n  "predecessor_hash": "27d4c192ce8d3b400eef1f1bc1f4312ae3c916cfe0166542c08f1dd5b4aa32f1",\n  "policy_sha256": "87ff3ac98c8f7646ecd25ecb641e7ffd49e5008a1d0b3c8f97cca6a7d091e246",\n  "identities_sha256": "e4b8b5b86bc3d3228284960db3e4611d998af780f85b82128a33dd73041c0e8f",\n  "parent_freeze_sha256": "0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2",\n  "immediate_parent_freeze_sha256": "4b921d416b9111594531ca33f26b1b307e04b22241ef995b6e571ce96a21f3e7",\n  "first_export_sha256": "283001dc1a5904f3e8b4de893ef658d2e7fe8053b8e98ed7baad6f242d318d8b",\n  "second_export_sha256": "bd4d32f4968eaff243d65d9cfe8fad36c603cd709c09ee7fdebd29746e90da42",\n  "expires_at": "2026-10-22T15:24:23.810674+00:00",\n  "signer": "Explicit human instruction recorded by local FYP operator",\n  "readiness_sha256": "3c95a1496b94c921d4c2256e9e9ce7e9d737607203d91439eb114329b195be2c",\n  "instance_id": "i-002b63326e1566005",\n  "signature": "08750cadd4bc934d96c5edb90cf9e4843ad6d67a6723bb9cb51b7c0588cc0a9c"\n}\n')
p.chmod(0o600)
RECEIPT
cd /opt/fyp-phase8-combined-v3
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B artifacts/phase-8-runner-amendment/v3/runner.py install-watchdog --root /var/lib/p8-combined/run
.venv/bin/python -B - <<'PY'
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v3'))
from controls import Journal,read,utc,write_new
from runner import verify_run,verify_host_timer
from handover import verify_imported_first,verify_members
from storage import S3Cloud,final_backup,upload
from postflight import recover
from transport import S3Store
root=Path('/var/lib/p8-combined/run');dep=root.parent/'deployment'
a=verify_run(root);verify_host_timer(root);verify_imported_first(root)
j=Journal(root);cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/')
archive=final_backup(j,root.parent/'backup')
p=upload(j,cloud,a.policy,archive);cloud.verify(p)
back=recover(p,root.parent/'authorized-prelaunch-readback',S3Store('fyp-research'))
verify_members(back/'slot');verify_imported_first(back/'slot')
j.event('V3_AUTHORIZED_PRELAUNCH_BACKUP_VERIFIED',proof=p.model_dump())
v={'status':'PASS','at_utc':utc().isoformat(),'instance_id':'i-002b63326e1566005','backup':p.model_dump(),'authority':a.verify(),'watchdog_and_absolute_timer_verified':True,'driver_calls':0,'main_started':False}
write_new(dep/'authorized-prelaunch-backup.json',v);print(json.dumps(v))
PY
systemctl is-active fyp-phase8-watchdog.service fyp-phase8-hardstop.timer fyp-p85-continuation-bootstrap-stop.timer fyp-p85-combined-preparation-absolute.timer
