"""Record the explicit human launch authorization against verified actual readiness."""
import hashlib
import hmac
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, 'E:/p8v4/source/artifacts/phase-8-runner-amendment/v4-complete')
from controls import Policy, canonical, hash_file, read, write_new
from handover import verify_chain

result = read(HERE / 'final-readiness-status1-result.json')['result']
assert result['Status'] == 'Success' and result['ResponseCode'] == 0
ready = json.loads(result['StandardOutputContent'])
assert ready['status'] == 'PASS' and all(ready['checks'].values())
owner = Path.home() / '.fyp-research/phase8-owner/phase84-final-v2'
receipts = Path.home() / '.fyp-research/phase8-owner/phase85-complete-v4/receipts'
key = (owner / 'owner.key').read_bytes()
policy = Policy.model_validate(read(owner / 'launch-policy.json'))
body = {k: v for k, v in read(receipts / 'CONTINUATION_FREEZE.json').items() if k != 'signature'}
body.update(kind='CONTINUATION_LAUNCH', predecessor_hash=hashlib.sha256(canonical(read(receipts / 'CONTINUATION_FREEZE.json'))).hexdigest(),
            readiness_sha256=ready['readiness_sha256'], instance_id=ready['instance_id'])
receipt = {**body, 'signature': hmac.new(key, canonical(body), 'sha256').hexdigest()}
write_new(receipts / 'CONTINUATION_LAUNCH.json', receipt)
write_new(HERE / 'CONTINUATION_LAUNCH.json', receipt)
verify_chain(receipts, key, body['package_hash'], policy, body['identities_sha256'],
             hashlib.sha256(canonical(read(owner / 'receipts/LAUNCH.json'))).hexdigest(), datetime.now(UTC))
write_new(HERE / 'actual-launch-authorization-binding.json', {
    'kind': 'EXPLICIT_HUMAN_LAUNCH_AUTHORIZATION_ACTUAL_HOST_BINDING', 'at_utc': datetime.now(UTC).isoformat(),
    'instance_id': ready['instance_id'], 'readiness_sha256': ready['readiness_sha256'],
    'freeze_manifest_sha256': 'cf6d4ff9e6e8916a8204c420076676fe9d9c746545ad686357b4e65a8f78710c',
    'package_hash': body['package_hash'], 'launch_receipt_sha256': hash_file(HERE / 'CONTINUATION_LAUNCH.json'),
    'remaining_originals': 1462, 'next_execution_id': '01a11705-11f0-73c0-af15-dd9f1d590b08',
    'deadline_utc': policy.stop_at.isoformat(), 'total_campaign_limit_usd': 65, 'admission_guard_usd': 55,
    'operational_clock_reset': False, 'main_started': False,
})
text = (HERE / 'activate-controls-body.sh').read_text()
prefix = "set -euo pipefail\numask 077\npython3 - <<'RECEIPT'\nfrom pathlib import Path\np=Path('/var/lib/fyp-owner/combined-v4-receipts/CONTINUATION_LAUNCH.json')\nwith p.open('x') as f:f.write(" + repr((HERE / 'CONTINUATION_LAUNCH.json').read_text()) + ")\np.chmod(0o600)\nRECEIPT\n"
with (HERE / 'activate-controls.sh').open('x') as f: f.write(prefix + text)
print(json.dumps({'status':'PASS','instance_id':ready['instance_id'],'launch_receipt_sha256':hash_file(HERE / 'CONTINUATION_LAUNCH.json'),'service_started':False}))
