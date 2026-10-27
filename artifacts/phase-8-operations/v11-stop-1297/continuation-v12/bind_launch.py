"""Sign only the actual successful readiness returned by the guarded host."""
from pathlib import Path
from datetime import UTC,datetime
import base64,hashlib,hmac,json,sys
H=Path(__file__).resolve().parent
sys.path.insert(0,'E:/p8v12/source/artifacts/phase-8-runner-amendment/v4-complete')
from controls import canonical,read,write_new
from operational_limits import effective_policy
from handover import verify_chain
def main():
    invocation=read(H/sys.argv[1])['result']
    assert invocation['Status']=='Success' and invocation['ResponseCode']==0
    found=[json.loads(line) for line in invocation['StandardOutputContent'].splitlines() if line.startswith('{')]
    ready=next(x for x in found if x.get('status')=='PASS_GENUINE_READINESS')
    assert all(ready['checks'].values()) and ready['main_admitted'] is False and ready['instance_id']=='i-057344e5372faf62f'
    owner=Path('C:/Users/syeda/.fyp-research/phase8-owner');key=(owner/'phase84-final-v2/owner.key').read_bytes()
    receipts=owner/'phase85-continuation-v12/receipts';freeze=read(receipts/'CONTINUATION_FREEZE.json')
    policy=effective_policy(read(owner/'phase84-final-v2/launch-policy.json'))
    assert hashlib.sha256(canonical(policy.model_dump(mode='json'))).hexdigest()==ready['policy_sha256']==freeze['policy_sha256']
    body={k:v for k,v in freeze.items() if k!='signature'}
    body.update(kind='CONTINUATION_LAUNCH',predecessor_hash=hashlib.sha256(canonical(freeze)).hexdigest(),readiness_sha256=ready['readiness_sha256'],instance_id=ready['instance_id'])
    value={**body,'signature':hmac.new(key,canonical(body),'sha256').hexdigest()}
    write_new(receipts/'CONTINUATION_LAUNCH.json',value);write_new(H/'CONTINUATION_LAUNCH.json',value)
    verify_chain(receipts,key,freeze['package_hash'],policy,freeze['identities_sha256'],hashlib.sha256(canonical(read(owner/'phase84-final-v2/receipts/LAUNCH.json'))).hexdigest(),datetime.now(UTC))
    raw=(H/'CONTINUATION_LAUNCH.json').read_bytes();encoded=base64.b64encode(raw).decode()
    script="set -euo pipefail\numask 077\npython3 -B - <<'LAUNCH_RECEIPT'\nfrom pathlib import Path\nimport base64,hashlib\ndata=base64.b64decode('"+encoded+"')\np=Path('/var/lib/fyp-owner/continuation-v12-receipts/CONTINUATION_LAUNCH.json')\nwith p.open('xb') as f:f.write(data)\np.chmod(0o600)\nprint('PASS_READINESS_BOUND_RECEIPT_NOT_ADMISSION '+hashlib.sha256(data).hexdigest())\nLAUNCH_RECEIPT\n"
    with (H/'transfer-launch.sh').open('x',newline='\n') as f:f.write(script)
    write_new(H/'actual-readiness-launch-binding.json',{'status':'SIGNED_ACTUAL_GENUINE_READINESS_NOT_ADMISSION','readiness_sha256':ready['readiness_sha256'],'launch_receipt_sha256':hashlib.sha256(raw).hexdigest(),'instance_id':ready['instance_id'],'package_hash':freeze['package_hash'],'source_invocation_id':invocation['CommandId'],'stop_at':policy.stop_at.isoformat()})
    print('PASS_ACTUAL_READINESS_BOUND_LAUNCH_NOT_ADMISSION')
if __name__=='__main__':main()
