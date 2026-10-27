"""Sign only the actual returned genuine readiness; keys remain local."""
from pathlib import Path
from datetime import datetime,UTC
import sys,json,hashlib,hmac,base64
H=Path(__file__).resolve().parent
sys.path.insert(0,'E:/p8v11/source/artifacts/phase-8-runner-amendment/v4-complete')
from controls import canonical,read,write_new
from operational_limits import effective_policy
from handover import verify_chain
def main():
    reply=read(H/'readiness-read1-result.json')['result'];assert reply['Status']=='Success' and reply['ResponseCode']==0
    found=[json.loads(line) for line in reply['StandardOutputContent'].splitlines() if line.startswith('{')]
    ready=next(v for v in found if v.get('status')=='PASS' and 'readiness_sha256' in v)
    assert all(ready['checks'].values()) and ready['main_admitted'] is False
    assert ready['instance_id']=='i-057344e5372faf62f'
    owner=Path('C:/Users/syeda/.fyp-research/phase8-owner');key=(owner/'phase84-final-v2/owner.key').read_bytes()
    receipts=owner/'phase85-continuation-v11/receipts';freeze=read(receipts/'CONTINUATION_FREEZE.json')
    policy=effective_policy(read(owner/'phase84-final-v2/launch-policy.json'))
    assert hashlib.sha256(canonical(policy.model_dump(mode='json'))).hexdigest()==ready['policy_sha256']==freeze['policy_sha256']
    body={k:v for k,v in freeze.items() if k!='signature'}
    body.update(kind='CONTINUATION_LAUNCH',predecessor_hash=hashlib.sha256(canonical(freeze)).hexdigest(),readiness_sha256=ready['readiness_sha256'],instance_id=ready['instance_id'])
    value={**body,'signature':hmac.new(key,canonical(body),'sha256').hexdigest()}
    write_new(receipts/'CONTINUATION_LAUNCH.json',value);write_new(H/'CONTINUATION_LAUNCH.json',value)
    verify_chain(receipts,key,freeze['package_hash'],policy,freeze['identities_sha256'],hashlib.sha256(canonical(read(owner/'phase84-final-v2/receipts/LAUNCH.json'))).hexdigest(),datetime.now(UTC))
    encoded=base64.b64encode((H/'CONTINUATION_LAUNCH.json').read_bytes()).decode()
    text="set -euo pipefail\numask 077\npython3 - <<'LAUNCH'\nimport base64,hashlib\nfrom pathlib import Path\np=Path('/var/lib/fyp-owner/continuation-v11-receipts/CONTINUATION_LAUNCH.json')\ndata=base64.b64decode('"+encoded+"')\nwith p.open('xb') as f:f.write(data)\np.chmod(0o600)\nprint('PASS_READINESS_BOUND_LAUNCH_RECEIPT_NOT_ADMISSION '+hashlib.sha256(data).hexdigest())\nLAUNCH\n"
    with (H/'transfer-launch.sh').open('x',newline='\n') as f:f.write(text)
    print('PASS_ACTUAL_READINESS_BOUND_LAUNCH_NOT_ADMISSION')
if __name__=='__main__':main()
