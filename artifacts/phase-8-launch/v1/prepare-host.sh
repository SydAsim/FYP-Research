#!/bin/bash
set -euo pipefail
umask 077
test -f /var/lib/p8-deployment/dependencies-ready.json
test ! -e /var/lib/fyp-owner/owner.key
test ! -e /var/lib/p8/run
python3 - <<'PY'
import base64,boto3,hashlib,json,os,subprocess
from pathlib import Path
s3=boto3.client('s3',region_name='ap-southeast-2')
response=s3.get_object(Bucket='fyp-p82-20261005-018da1d6-803656589923',Key='exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/deployment/host-owner-envelope.json',VersionId='OpCS0UDPt_JoN0GeJGePqmoIoAYCpizS')
try: data=response['Body'].read()
finally: response['Body'].close()
if hashlib.sha256(data).hexdigest()!='61d8cbe3db201682fb1ad28c000559cd85fde38b79f0ba19f8dbe17c4e5c38e1': raise ValueError('OWNER_ENVELOPE_DRIFT')
envelope=json.loads(data)
if envelope['target_instance']!='i-0a6196aff6f8098ac' or envelope['run_id']!='p85-01a116f7-3b82-7a79-8653-3aee62dc99e9': raise ValueError('WRAPPING_TARGET_DRIFT')
owner=Path('/var/lib/fyp-owner'); cipher=owner/'transfer-cipher.bin'
with cipher.open('xb') as f: f.write(base64.b64decode(envelope['encrypted_key']));f.flush();os.fsync(f.fileno())
subprocess.run(['openssl','pkeyutl','-decrypt','-inkey',str(owner/'transfer-private.pem'),'-in',str(cipher),'-out',str(owner/'owner.key'),'-pkeyopt','rsa_padding_mode:oaep','-pkeyopt','rsa_oaep_md:sha256','-pkeyopt','rsa_mgf1_md:sha256'],check=True)
if (owner/'owner.key').stat().st_size!=32: raise ValueError('INVALID_OWNER_KEY')
for kind,raw in envelope['public_receipts'].items():
    if kind not in ('REVIEW_ACCEPTED','FREEZE','LAUNCH'): raise ValueError('RECEIPT_KIND')
    with (owner/'receipts'/f'{kind}.json').open('x') as f: json.dump(raw,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
with (owner/'launch-policy.json').open('x') as f: json.dump(envelope['launch_policy'],f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
for p in [owner/'owner.key',owner/'launch-policy.json',*list((owner/'receipts').glob('*.json'))]: p.chmod(0o600)
print('PASS protected host-bound receipt/key transfer; key not printed')
PY
cd /opt/fyp-phase8-linux-v1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
.venv/bin/python -B - <<'PY'
import json,socket,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-review-freeze/v2'))
from controls import Authority,Policy,guard,hash_file,read,utc,write_new
from storage import S3Cloud
from research.execution_linux_v1.platform import host
r=Path.cwd(); owner=Path('/var/lib/fyp-owner'); policy=Policy.model_validate(read(owner/'launch-policy.json'))
Authority(r,r/'artifacts/phase-8-review-freeze/v2/review-inventory.json',policy,hash_file(r/'artifacts/phase-8-review-freeze/v2/schedule.json'),owner/'receipts',owner/'owner.key').verify()
cloud=S3Cloud(policy.cloud_bucket,f'exports/phase8/{policy.run_id}/')
sample=host(Path('/var/lib/p8'),Path('/var/lib/p8'))
sample.update(working_bytes=0,backup_bytes=0)
cloud_bytes=cloud.inventory()
guard(policy,sample,utc(),cloud_bytes,extra_bytes=policy.slot_capacity_reserve_bytes)
for port in (16432,16433,19100,19101,19102,19110):
    with socket.socket() as s: s.bind(('127.0.0.1',port))
probe=Path('/var/lib/p8-deployment/permission-probe.json')
write_new(probe,{'classification':'DEPLOYMENT_PERMISSION_CHECK_NOT_SCIENTIFIC_EXECUTION','run_id':policy.run_id,'at':utc().isoformat()})
proof=cloud.put(probe,cloud.prefix+'deployment/permission-probe.json');cloud.verify(proof)
write_new(Path('/var/lib/p8-deployment/preinitialize-readiness.json'),{'status':'PASS','at':utc().isoformat(),'host':sample,'cloud_bytes_before_probe':cloud_bytes,'proof':proof.model_dump(),'owner_key_mode':oct((owner/'owner.key').stat().st_mode&0o777),'authorization_chain':'PASS','ports_free':True,'main_executions':0})
print(json.dumps(read(Path('/var/lib/p8-deployment/preinitialize-readiness.json'))))
PY
.venv/bin/python -B artifacts/phase-8-review-freeze/v2/runner.py init --root /var/lib/p8/run --backup /var/lib/p8/backup --source /opt/fyp-phase8-linux-v1 --manifest artifacts/phase-8-review-freeze/v2/review-inventory.json --schedule artifacts/phase-8-review-freeze/v2/schedule.json --policy /var/lib/fyp-owner/launch-policy.json --receipts /var/lib/fyp-owner/receipts --key /var/lib/fyp-owner/owner.key
.venv/bin/python -B artifacts/phase-8-review-freeze/v2/runner.py verify --root /var/lib/p8/run
.venv/bin/python -B artifacts/phase-8-review-freeze/v2/runner.py install-watchdog --root /var/lib/p8/run
systemctl is-active fyp-phase8-hardstop.timer fyp-phase8-watchdog.service
systemctl list-timers fyp-phase8-hardstop.timer fyp-p85-bootstrap-stop.timer --no-pager
# Preparation never starts the campaign service.
printf '%s\n' HOST_INITIALIZED_TIMERS_ACTIVE_MAIN_NOT_STARTED
