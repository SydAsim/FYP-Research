"""Use existing authorization only after actual readiness is verified."""
import hashlib
import hmac
import json
import sys
from datetime import UTC,datetime
from pathlib import Path
from ops import HERE,record

sys.path.insert(0,'E:/p8v10/source/artifacts/phase-8-runner-amendment/v4-complete')
from controls import canonical,read,hash_file
from handover import verify_chain
from operational_limits import effective_policy

def main():
    reply=read(HERE/'readiness-status-result.json')['result']
    assert reply['Status']=='Success' and reply['ResponseCode']==0
    records=[json.loads(line) for line in reply['StandardOutputContent'].splitlines() if line.startswith('{')]
    found=[r for r in records if r.get('status')=='PASS' and 'readiness_sha256' in r and 'checks' in r]
    assert len(found)==1
    ready=found[0];assert all(ready['checks'].values()) and ready['main_admitted'] is False and ready['instance_id']=='i-057344e5372faf62f'
    owner=Path('C:/Users/syeda/.fyp-research/phase8-owner/phase84-final-v2')
    receipts=owner.parent/'phase85-continuation-v10/receipts'
    key=(owner/'owner.key').read_bytes();freeze=read(receipts/'CONTINUATION_FREEZE.json')
    policy=effective_policy(read(owner/'launch-policy.json'))
    assert hashlib.sha256(canonical(policy.model_dump(mode='json'))).hexdigest()==ready['policy_sha256']==freeze['policy_sha256']
    body={k:v for k,v in freeze.items() if k!='signature'}
    body.update(kind='CONTINUATION_LAUNCH',predecessor_hash=hashlib.sha256(canonical(freeze)).hexdigest(),
                readiness_sha256=ready['readiness_sha256'],instance_id=ready['instance_id'])
    signed={**body,'signature':hmac.new(key,canonical(body),'sha256').hexdigest()}
    record('CONTINUATION_LAUNCH.json',signed)
    with (receipts/'CONTINUATION_LAUNCH.json').open('x',encoding='utf-8') as f:json.dump(signed,f,indent=2)
    verify_chain(receipts,key,freeze['package_hash'],policy,freeze['identities_sha256'],
        hashlib.sha256(canonical(read(owner/'receipts/LAUNCH.json'))).hexdigest(),datetime.now(UTC))
    text=(HERE/'CONTINUATION_LAUNCH.json').read_text()
    script="set -euo pipefail\numask 077\npython3 - <<'RECEIPT'\nfrom pathlib import Path\np=Path('/var/lib/fyp-owner/continuation-v10-receipts/CONTINUATION_LAUNCH.json')\nwith p.open('x') as f:f.write("+repr(text)+")\np.chmod(0o600)\nRECEIPT\n"
    with (HERE/'transfer-launch.sh').open('x',encoding='utf-8',newline='\n') as f:f.write(script)
    record('actual-launch-binding.json',{'status':'SIGNED_AFTER_ACTUAL_READINESS_NOT_ADMISSION','instance_id':ready['instance_id'],
        'readiness_sha256':ready['readiness_sha256'],'receipt_sha256':hash_file(HERE/'CONTINUATION_LAUNCH.json'),
        'freeze_sha256':hash_file(receipts/'CONTINUATION_FREEZE.json'),'package_hash':freeze['package_hash'],'next_sequence':146,
        'next_execution_id':'01a11705-11f1-772d-8190-c43552871801','stop_at':policy.stop_at.isoformat()})
    print('PASS_ACTUAL_READINESS_BOUND_LAUNCH_NOT_ADMISSION')

if __name__=='__main__':main()
