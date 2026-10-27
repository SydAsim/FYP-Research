"""Bind actual preboot proofs and start only under the verified fresh guard."""
import hashlib
import json
from datetime import UTC,datetime,timedelta
from ops import HERE,record,call,HOST

def main():
    guards=json.loads((HERE/'independent-guards-verified.json').read_text());assert guards['status']=='PASS_BEFORE_BOOT'
    now=datetime.now(UTC)
    assert now-datetime.fromisoformat(json.loads((HERE/'feasibility.json').read_text())['at'])<timedelta(minutes=20)
    gate={'kind':'GENUINE_PREBOOT_EVIDENCE_NOT_READINESS','at':now.isoformat(),'expires_at':(now+timedelta(minutes=90)).isoformat(),
        'instance_id':HOST,'host_owned_stopped_before_boot':True,'no_inbound_access':True,'retention_authorized_until':'2026-10-27T15:24:23.810674Z',
        'guards':{'preparation':guards['preparation'],'absolute':guards['absolute']},'feasibility':json.loads((HERE/'feasibility.json').read_text()),
        'evidence_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('preboot-host-result.json','preboot-security-result.json','preboot-versions-result.json','independent-guards-verified.json','preboot-command-review-final.json')}}
    record('external-preboot-final.json',gate)
    body=json.dumps(gate,indent=2)
    script="set -euo pipefail\numask 077\npython3 - <<'GATES'\nfrom pathlib import Path\np=Path('/var/lib/p8-continuation-v10/deployment/external-preboot-final.json')\nwith p.open('x') as f:f.write("+repr(body)+")\nGATES\n"
    with (HERE/'transfer-external-proof.sh').open('x',encoding='utf-8',newline='\n') as f:f.write(script)
    print(json.dumps(call('start-retained-host',['ec2','start-instances','--instance-ids',HOST])))

if __name__=='__main__':main()
