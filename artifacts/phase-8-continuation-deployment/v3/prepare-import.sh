#!/bin/bash
set -euo pipefail
umask 077
chmod 700 /var/lib/fyp-owner
cd /opt/fyp-phase8-combined-v3
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
install -d -m 700 /root/.aws
test ! -e /root/.aws/config
printf '%s\n' '[profile fyp-research]' 'region = ap-southeast-2' >/root/.aws/config
cat >/var/lib/p8-combined/deployment/owner-envelope.json <<'ENVELOPE'
{
  "kind": "FRESH_HOST_RSA_OAEP_SHA256_ENVELOPE",
  "target_instance": "i-002b63326e1566005",
  "public_key_sha256": "d27c18870e2643fc96cb3883fd193af75dabecad7ed8a63e8d3eb1022854ba51",
  "encrypted_owner_key": "cceUsEKTJNqDemwwkLHobR4lcLGWDkmbr6kwhxokSOBi/yZSxk4yYEtKfdhPGLcbm59QXMJCOz3fQ0KVjBoeYMvv6jUFHKLZ9Mttsn52IMNaquyEM6CLlUoA73KBahyEhqiIK1HPQSgCnEz/EmkmluKoi7Mvs4rR6keQzMPXtU41j92WL4fPk2I9sHI4nWdLuEWcVA0T8Md/llx1+6zv2xSSYGAH2w6r+Z4Fhln2aD8iPGIjFZ5lI+e7uuaGWIFzdY4+/EuSejxaytj+9srwfK6RqLktLbIGTDvshs0y6b33L8cgNmRrcDxvuKfcCTt2dlEo3b5aOtsfCjPHsHPc4RYvoTtftZ/KLfFSeSxJeqanMRD81CfjH/KL9Pj77bZK0B61rYyWLmPCGrmizKKdsgfoccB7IREU04cb+Yq9NkkuTDwM5HM4rkGM1Ij32KZqn+chcd+TYdHe/u4nWbNbBN0h7ek1gLFxQm/HbSEQEKB7sJROKy06Sae9uxYiW7YY",
  "clear_key_included": false
}
ENVELOPE
cat >/var/lib/p8-combined/deployment/original-proofs.json <<'PROOFS'
[{"label": "first", "proof": {"bucket": "fyp-p82-20261005-018da1d6-803656589923", "key": "exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/cc38346ff273b2f04ef8022345654708991fd40ff8ab3ffc9c8b8f4de5bfb8f1.tar.gz", "version_id": "SDh8fTiUZ60.u3OMiYr_bVKjEpxL19SA", "sha256": "cc38346ff273b2f04ef8022345654708991fd40ff8ab3ffc9c8b8f4de5bfb8f1", "bytes": 444490}}, {"label": "second", "proof": {"bucket": "fyp-p82-20261005-018da1d6-803656589923", "key": "exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/8fb4547bd0eee33743997f9ad602fb4c03d0243ce117cbd5c11f1fb765daf739.tar.gz", "version_id": "B0toEx.sKtZy5q.HBTNWDk4j1W75NKmT", "sha256": "8fb4547bd0eee33743997f9ad602fb4c03d0243ce117cbd5c11f1fb765daf739", "bytes": 526263}}, {"label": "master", "proof": {"bucket": "fyp-p82-20261005-018da1d6-803656589923", "key": "exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/f39e75cac63d077137ff6bd5e09ef6c2e66f7ddf3caa869ccd0fefa77fdf1661.tar.gz", "version_id": "Dvltv.4YHlHKxeB3N7goE.vTaaTCuf5l", "sha256": "f39e75cac63d077137ff6bd5e09ef6c2e66f7ddf3caa869ccd0fefa77fdf1661", "bytes": 253654}}]
PROOFS
.venv/bin/python -B - <<'PY'
import base64,gzip,hashlib,json,os,shutil,socket,sqlite3,subprocess,sys,tarfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v3'))
from controls import Journal,guard,hash_file,read,utc,write_new
from handover import ContinuationAuthority,bind_host_segment,stage,verify_imported_first,verify_members,closed_boundary
from storage import ObjectProof,S3Cloud,upload,verify_local
from postflight import recover
from transport import S3Store
from research.execution_linux_v1.platform import host
root=Path('/var/lib/p8-combined/run');dep=root.parent/'deployment';owner=Path('/var/lib/fyp-owner')
value=read(dep/'owner-envelope.json')
if value['target_instance']!='i-002b63326e1566005' or value['public_key_sha256']!=hash_file(owner/'transfer-public.pem'):raise ValueError('OWNER_ENVELOPE_HOST_BINDING_DRIFT')
with (dep/'wrapped-owner.bin').open('xb') as f:f.write(base64.b64decode(value['encrypted_owner_key']))
if (owner/'owner.key').exists():raise ValueError('EXISTING_KEY_RETAIN_ATTEMPT')
subprocess.run(['openssl','pkeyutl','-decrypt','-inkey',str(owner/'transfer-private.pem'),'-in',str(dep/'wrapped-owner.bin'),'-out',str(owner/'owner.key'),'-pkeyopt','rsa_padding_mode:oaep','-pkeyopt','rsa_oaep_md:sha256','-pkeyopt','rsa_mgf1_md:sha256'],check=True,timeout=15)
(owner/'owner.key').chmod(0o600)
public=dep/'authority.tar.gz.extract'
for label, names, target in [('original',('REVIEW_ACCEPTED','FREEZE','LAUNCH'),'receipts'),('combined-v3',('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'),'combined-v3-receipts')]:
 for n in names:
  shutil.copyfile(public/label/(n+'.json'),owner/target/(n+'.json'))
  (owner/target/(n+'.json')).chmod(0o600)
store=S3Store('fyp-research');proofs=[]
for obj in read(dep/'original-proofs.json'):
 p=ObjectProof.model_validate(obj['proof']);destination=root.parent/'retained'/obj['label']
 recovered=recover(p,destination,store);verify_members(recovered/'slot');proofs.append(p.model_dump())
 for dump in ('setup_app.sql.gz','setup_truth.sql.gz'):
  if obj['label']!='master':
   with gzip.open(recovered/'slot'/dump,'rb') as f:
    while f.read(1024**2):pass
stage(root.parent/'retained/master/x/slot',root.parent/'retained/first/x/slot',root,
 second=root.parent/'retained/second/x/slot',first_archive=root.parent/'retained/first/t/e.tar.gz',second_archive=root.parent/'retained/second/t/e.tar.gz')
verify_imported_first(root);bind_host_segment(root)
a=ContinuationAuthority(root,read(root/'run.json'));a.verify(prelaunch=True)
rows=Journal(root).rows();closed_boundary(rows,read(Path.cwd()/'artifacts/phase-8-review-freeze/v2/schedule.json')['rows'])
if rows[2]['execution_id']!='01a11705-11f0-7a68-8c68-4da5c8126c84' or any(r['state']!='PLANNED' for r in rows[2:]):raise ValueError('EXACT_NEXT_P2_OR_BOUNDARY_DRIFT')
backup=root.parent/'backup';backup.mkdir(exist_ok=False)
cloud=S3Cloud(a.policy.cloud_bucket,f'exports/phase8/{a.policy.run_id}/')
sample=host(root,backup);sample.update(working_bytes=0,backup_bytes=0)
cloud_bytes=cloud.inventory();guard(a.policy,sample,utc(),cloud_bytes,extra_bytes=a.policy.slot_capacity_reserve_bytes)
for port in (16432,16433,19100,19101,19102,19110):
 with socket.socket() as s:s.bind(('127.0.0.1',port))
if owner.stat().st_mode&0o777!=0o700 or (owner/'owner.key').stat().st_mode&0o777!=0o600:raise ValueError('PRIVATE_OWNER_PERMISSIONS')
probe=dep/'permission-probe.json';write_new(probe,{'kind':'PRELAUNCH_PERMISSION_PROBE_NOT_RESEARCH_OUTCOME','at_utc':utc().isoformat(),'run_id':a.policy.run_id})
probe_proof=cloud.put(probe,cloud.prefix+'combined-v3/deployment/permission-probe.json');cloud.verify(probe_proof)
with store.client.get_object(Bucket=probe_proof.bucket,Key=probe_proof.key,VersionId=probe_proof.version_id)['Body'] as f:
 if hashlib.sha256(f.read()).hexdigest()!=probe_proof.sha256:raise ValueError('PERMISSION_GET_DRIFT')
folder=backup/'prelaunch-attempt1';folder.mkdir(exist_ok=False);journal=Journal(root);journal.verify()
with journal.connect() as source,sqlite3.connect(folder/'campaign.sqlite3') as target:
 source.backup(target)
 if target.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('PRELAUNCH_LEDGER_CORRUPTION')
for n in ('run.json','bindings.json','binding-seal.json','cloud.json','host-clock.json','handover.json','saved-identities.json','historical-evidence.tar.gz'):
 shutil.copyfile(root/n,folder/n)
for prefix,names in [('receipts',('REVIEW_ACCEPTED','FREEZE','LAUNCH')),('combined-v3-receipts',('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'))]:
 d=folder/'public-authority'/prefix;d.mkdir(parents=True)
 for n in names:shutil.copyfile(owner/prefix/(n+'.json'),d/(n+'.json'))
shutil.copytree(root/'backups',folder/'backups')
shutil.copyfile(dep/'source-ready.json',folder/'source-ready.json')
files={p.relative_to(folder).as_posix():hash_file(p) for p in folder.rglob('*') if p.is_file()}
write_new(folder/'manifest.json',{'kind':'PRELAUNCH_COMBINED_MASTER_NOT_EXECUTION','postgres_dumps':False,'files':files})
archive=folder.with_suffix('.tar.gz')
with tarfile.open(archive,'x:gz') as out:out.add(folder,arcname='slot')
verify_local(archive,hash_file(archive));p=upload(journal,cloud,a.policy,archive);cloud.verify(p)
readback=recover(p,root.parent/'prelaunch-readback',store);verify_members(readback/'slot');verify_imported_first(readback/'slot')
journal.event('V3_PRELAUNCH_BACKUP_VERIFIED',proof=p.model_dump())
write_new(dep/'import-and-backup-readiness.json',{'status':'PASS','at_utc':utc().isoformat(),'instance_id':'i-002b63326e1566005','original_statuses':['FAILED','FAILED'],'identities':1500,'backed_up':2,'planned':1498,'next_execution_id':rows[2]['execution_id'],'driver_calls':0,'old_live_state_restored':False,'original_backups':proofs,'prelaunch_backup':p.model_dump(),'permission_probe':probe_proof.model_dump(),'host':sample,'cloud_bytes':cloud_bytes,'owner_mode':'0700/0600','operational_clock_reset':False,'original_deadline':a.policy.stop_at.isoformat(),'cost_at_now_usd':a.policy.committed_cost(utc())})
print(json.dumps(read(dep/'import-and-backup-readiness.json')))
PY
systemctl is-active fyp-p85-continuation-bootstrap-stop.timer fyp-p85-combined-preparation-absolute.timer
