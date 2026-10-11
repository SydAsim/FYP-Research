"""Record already explicit human launch authorization against actual readiness."""
import hashlib,hmac,json
from datetime import UTC,datetime
from pathlib import Path
from ops import HERE
from controls import Policy,canonical,read,write_new,hash_file
from handover import verify_chain
from operational_limits import LIMITS_SHA256

def main():
    reply=read(HERE/'final-readiness-status1-result.json')['result']
    assert reply['Status']=='Success' and reply['ResponseCode']==0
    ready=json.loads(reply['StandardOutputContent'])
    assert ready['status']=='PASS' and all(ready['checks'].values()) and ready['main_admitted'] is False
    assert ready['operational_limits_sha256']==LIMITS_SHA256
    owner=Path.home()/'.fyp-research/phase8-owner/phase84-final-v2'
    receipts=Path.home()/'.fyp-research/phase8-owner/phase85-continuation-v7/receipts'
    key=(owner/'owner.key').read_bytes();policy=Policy.model_validate(read(owner/'launch-policy.json'))
    original=read(receipts/'CONTINUATION_FREEZE.json')
    assert original['package_hash']=='9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817'
    assert original['policy_sha256']==ready['policy_sha256']
    body={k:v for k,v in original.items() if k!='signature'}
    body.update(kind='CONTINUATION_LAUNCH',predecessor_hash=hashlib.sha256(canonical(original)).hexdigest(),readiness_sha256=ready['readiness_sha256'],instance_id=ready['instance_id'])
    signed={**body,'signature':hmac.new(key,canonical(body),'sha256').hexdigest()}
    write_new(receipts/'CONTINUATION_LAUNCH.json',signed)
    write_new(HERE/'CONTINUATION_LAUNCH.json',signed)
    verify_chain(receipts,key,body['package_hash'],policy,body['identities_sha256'],hashlib.sha256(canonical(read(owner/'receipts/LAUNCH.json'))).hexdigest(),datetime.now(UTC))
    write_new(HERE/'actual-launch-authorization-binding.json',{'kind':'EXPLICIT_HUMAN_AUTHORIZATION_BOUND_TO_ACTUAL_VERIFIED_HOST','at_utc':datetime.now(UTC).isoformat(),'instance_id':ready['instance_id'],'readiness_sha256':ready['readiness_sha256'],'launch_receipt_sha256':hash_file(HERE/'CONTINUATION_LAUNCH.json'),'human_instruction_sha256':hash_file(HERE/'human-acceptance.json'),'package_hash':body['package_hash'],'operational_limits_sha256':LIMITS_SHA256,'remaining':1418,'next_sequence':83,'next_execution_id':'01a11705-11f1-792b-ae1e-36bfc6773842','original_deadline':policy.stop_at.isoformat(),'guard_usd':60,'total_usd':65,'actual_admission':False})
    prefix="set -euo pipefail\numask 077\npython3 - <<'RECEIPT'\nfrom pathlib import Path\np=Path('/var/lib/fyp-owner/continuation-v7-receipts/CONTINUATION_LAUNCH.json')\nwith p.open('x') as f:f.write("+repr((HERE/'CONTINUATION_LAUNCH.json').read_text())+")\np.chmod(0o600)\nRECEIPT\n"
    with (HERE/'transfer-launch-receipt.sh').open('x',encoding='utf-8',newline='\n') as out:out.write(prefix)
    print(json.dumps({'status':'PASS','launch_receipt_sha256':hash_file(HERE/'CONTINUATION_LAUNCH.json'),'actual_admission':False}))

if __name__=='__main__':main()
