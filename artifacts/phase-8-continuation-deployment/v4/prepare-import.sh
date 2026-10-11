set -euo pipefail
umask 077
cat >/var/lib/p8-combined-v4/deployment/owner-envelope.json <<'ENVELOPE'
{"kind": "FRESH_HOST_RSA_OAEP_SHA256_ENVELOPE", "target_instance": "i-057344e5372faf62f", "public_key_sha256": "be3a1b78e95a5b2b9c861772beb98b26132651e85dfe4a173884e1a24529d4bf", "encrypted_owner_key": "nW3TIMgU2YWEflaPLNoODLbTkbd6Py6M+aIRymzTZmzQHd7Mn+2VJK2P8qYx1DMvw5DGaj/n9FkmA9F96cRoElEVHIn4WA29C6X1xtRy6XM+wneEi0gjYaRqU/QfNlcYS+uCl3IycChYlAedR54Wg/+VKfk1TJyUc2+deLur0KsfBrwcA3CRM8KAclM9eG/zEXXJQBiBEvgueVLDNAeSDKvPw3rVXmdHEyN76UzZrGdvNi/7s752O1c2AH5lMeRJWD0Y2poFJ/KG1TUE8mxO8ork6j+gWauTccxl3bDGLkoXr074SmxUEkhEAPK+ul8TELzpfAtCt+nOuLhFPW4+kjtLVqPQZ8IhbzWQ1TtEjl4Cn99ncxVS6Vh8qiI7Dmp6K6WB0r7MQyCMmRYDHv06ZG9z6sn/IzWjFwOtVOaOORdfBTNsCwSN2PQ7WIs+rmqFI797P77+u9DFSBWHBUD8PUEFQfdb//Q1vlpJ7HS/Je1FjkJiyMFkIWG7ZFs4vL1R", "clear_key_included": false}
ENVELOPE
cat >/var/lib/p8-combined-v4/deployment/actual-deployment-binding.json <<'BINDING'
{
  "instance_id": "i-057344e5372faf62f",
  "launch_time": "2026-10-08T19:50:57+00:00",
  "package_hash": "a869745a6c1807e4f2427cc9597e5d85f41a2b4eb2aa4aa8abd4bdb8cc9b7306",
  "freeze_manifest_sha256": "cf6d4ff9e6e8916a8204c420076676fe9d9c746545ad686357b4e65a8f78710c",
  "region": "ap-southeast-2",
  "preparation_deadline": "2026-10-08 21:50:50 UTC",
  "actual_main_started": false,
  "root_disk_deletion_authorized": false
}

BINDING
set -euo pipefail
umask 077
chmod 700 /var/lib/fyp-owner
cd /opt/fyp-phase8-combined-v4
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
install -d -m 700 /root/.aws
test ! -e /root/.aws/config
printf '%s\n' '[profile fyp-research]' 'region = ap-southeast-2' >/root/.aws/config
.venv/bin/python -B - <<'PY'
import base64,hashlib,json,shutil,socket,sqlite3,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import Journal,guard,hash_file,read,utc,write_new
from handover import ContinuationAuthority,bind_host_segment,stage,verify_imported_first,verify_members,closed_boundary
from storage import ObjectProof,S3Cloud,final_backup,upload
from postflight import recover
from transport import S3Store
from research.execution_linux_v1.platform import host
root=Path('/var/lib/p8-combined-v4/run');dep=root.parent/'deployment';owner=Path('/var/lib/fyp-owner')
value=read(dep/'owner-envelope.json')
if value['target_instance']!=read(dep/'actual-deployment-binding.json')['instance_id'] or value['public_key_sha256']!=hash_file(owner/'transfer-public.pem'):raise ValueError('OWNER_ENVELOPE_HOST_BINDING_DRIFT')
with (dep/'wrapped-owner.bin').open('xb') as f:f.write(base64.b64decode(value['encrypted_owner_key']))
if (owner/'owner.key').exists():raise ValueError('EXISTING_KEY_RETAIN_ATTEMPT')
subprocess.run(['openssl','pkeyutl','-decrypt','-inkey',str(owner/'transfer-private.pem'),'-in',str(dep/'wrapped-owner.bin'),'-out',str(owner/'owner.key'),'-pkeyopt','rsa_padding_mode:oaep','-pkeyopt','rsa_oaep_md:sha256','-pkeyopt','rsa_mgf1_md:sha256'],check=True,timeout=15)
(owner/'owner.key').chmod(0o600)
public=dep/'authority.tar.gz.extract'
for label,names,target in [('original',('REVIEW_ACCEPTED','FREEZE','LAUNCH'),'receipts'),('combined-v4',('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'),'combined-v4-receipts')]:
 for n in names:
  shutil.copyfile(public/label/(n+'.json'),owner/target/(n+'.json'));(owner/target/(n+'.json')).chmod(0o600)
runtime=Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'
stage(runtime/'boundary',root);verify_imported_first(root);bind_host_segment(root)
a=ContinuationAuthority(root,read(root/'run.json'));a.verify(prelaunch=True)
rows=Journal(root).rows();closed_boundary(rows,read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows'])
if rows[38]['execution_id']!='01a11705-11f0-73c0-af15-dd9f1d590b08' or rows[38]['arm']!='B3' or rows[38]['attempt']!=1 or any(r['state']!='PLANNED' for r in rows[38:]):raise ValueError('EXACT_SEQUENCE39_OR_BOUNDARY_DRIFT')
backup=root.parent/'backup';backup.mkdir(exist_ok=False)
cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/');store=S3Store('fyp-research')
proofs=read(runtime/'retained-slot-proofs.json')
for obj in proofs:cloud.verify(ObjectProof.model_validate(obj['cloud']))
cloud.verify(ObjectProof.model_validate(read(runtime/'stopped-boundary-reference.json')))
sample=host(root,backup);sample.update(working_bytes=0,backup_bytes=0)
cloud_bytes=cloud.inventory();guard(a.policy,sample,utc(),cloud_bytes,extra_bytes=a.policy.slot_capacity_reserve_bytes)
for port in (16432,16433,19100,19101,19102,19110):
 with socket.socket() as s:s.bind(('127.0.0.1',port))
if owner.stat().st_mode&0o777!=0o700 or (owner/'owner.key').stat().st_mode&0o777!=0o600:raise ValueError('PRIVATE_OWNER_PERMISSIONS')
probe=dep/'permission-probe.json';write_new(probe,{'kind':'PRELAUNCH_PERMISSION_PROBE_NOT_RESEARCH_OUTCOME','at_utc':utc().isoformat(),'run_id':a.policy.run_id})
probe_proof=cloud.put(probe,cloud.prefix+'combined-v4/deployment/permission-probe.json');cloud.verify(probe_proof)
reply=store.client.get_object(Bucket=probe_proof.bucket,Key=probe_proof.key,VersionId=probe_proof.version_id)
try:
 if hashlib.sha256(reply['Body'].read()).hexdigest()!=probe_proof.sha256:raise ValueError('PERMISSION_GET_DRIFT')
finally:reply['Body'].close()
journal=Journal(root);journal.verify();archive=final_backup(journal,backup)
p=upload(journal,cloud,a.policy,archive);cloud.verify(p)
back=recover(p,root.parent/'prelaunch-readback',store);verify_members(back/'slot');verify_imported_first(back/'slot')
journal.event('V4_PRELAUNCH_BACKUP_VERIFIED',proof=p.model_dump())
write_new(dep/'import-and-backup-readiness.json',{'status':'PASS','at_utc':utc().isoformat(),'instance_id':value['target_instance'],'identities':1500,'backed_up':38,'planned':1462,'next_sequence':39,'next_arm':'B3','next_attempt':1,'next_execution_id':rows[38]['execution_id'],'driver_calls':0,'old_live_state_restored':False,'original_backups':[x['cloud'] for x in proofs],'boundary_backup':read(runtime/'stopped-boundary-reference.json'),'prelaunch_backup':p.model_dump(),'permission_probe':probe_proof.model_dump(),'host':sample,'cloud_bytes':cloud_bytes,'owner_mode':'0700/0600','operational_clock_reset':False,'original_deadline':a.policy.stop_at.isoformat(),'cost_at_now_usd':a.policy.committed_cost(utc())})
print(json.dumps(read(dep/'import-and-backup-readiness.json')))
PY
systemctl is-active fyp-p85-continuation-bootstrap-stop.timer fyp-p85-combined-preparation-absolute.timer
