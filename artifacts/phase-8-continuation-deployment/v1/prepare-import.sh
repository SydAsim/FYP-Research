#!/bin/bash
set -euo pipefail
umask 077
cat >/var/lib/p8-continuation/deployment/owner-envelope.json <<'ENVELOPE'
{"kind": "FRESH_HOST_ONLY_RSA_OAEP_SHA256_ENVELOPE", "target_instance": "i-034252c3e9b083abf", "public_key_sha256": "cddc3b1dc7c335819361fd00c07d2bed2848d5e42209152efd9cfea9b8103708", "encrypted_owner_key": "HyrMgKcCfxizIdjhQ7oJtEGKz9mpIQzEqfyv4ofJD+jcSUjIn+druOOgHskxZGx34q5iZ/sEtmwm0alHwA9kb0JGOD59CKH13AAqCVOxxBylRdShdwtEkdwwqwEAb2rMfIWKlehitrGqvngblJM5WK40CE+Uqmd+h/G3ISu11g5ZcXVBxDyJtAulVzHaWz8+QTAB65Tv2fhS/gk89lxgR7y2+0G0ZAGdIWyOQ+wKs+FECridHTxX7rk9jPsXNw5hzKTPvruxPOdvYAcaAd90svIXn4iA2xzVFTKD9gt9e8JP//GImVZM+QFo9sw9BmSfC588AfscboyVEt98laUVn5RkavrEWKp8wR1b3znZz6ebBxztqk6V2lC1DuJatHFaRQr2EmojG99sBENS9lbc4uD5uIQBb7IuUCI/9BkEk7xG9Vm1f8HhRXB2Kd5rS2IUBfII/4OnyQvBVbdz35WTNQV+n+Ram06GaI9sNmiJ3HnfCUIdvUyaVew0lb3e6fRy", "public_files": {"receipts/REVIEW_ACCEPTED.json": {"base64": "ew0KICAia2luZCI6ICJSRVZJRVdfQUNDRVBURUQiLA0KICAic2NvcGUiOiAiQ0FNUEFJR04iLA0KICAicGFja2FnZV9oYXNoIjogImM3NmZjNTQwMThjZTZiOWU5Zjc3ZWViMjk0NmNlYTI1MzI3MWFkNGE4NTczZjhmZTA0Nzk2MWQ3YjZmNmRjNmIiLA0KICAicG9saWN5X2hhc2giOiAiZDA4OTlkMmRiOWY4NThlN2RjMTBiZDljOTVhODgxOWE3MzM1ZjY0MWE1OWEwMGRiNTEzZjA1YzQ2OTZjYmRjMSIsDQogICJzY2hlZHVsZV9oYXNoIjogIjhjYWViZTFhNzBhYTg3ZDY2YzJmNzJkNWFkZTRhODJkZWU4Mjk4ZmY4NDQ5YTRmZWZmMmYwNWMxYTZkNDQxNzQiLA0KICAicHJlZGVjZXNzb3JfaGFzaCI6IG51bGwsDQogICJleHBpcmVzX2F0IjogIjk5OTktMTItMzFUMjM6NTk6NTkrMDA6MDAiLA0KICAic2lnbmVyIjogIkh1bWFuIGFjY2VwdGFuY2UgcmVjb3JkZWQgYnkgdGhlIGxvY2FsIEZZUCBvcGVyYXRvciIsDQogICJzaWduYXR1cmUiOiAiOGUzZjEwYjA2ZDZiZDJlZjgzNGI2NWIxNTMzZTUzMzY2YmEwMjg0ZGFhODA5NTZhNGUwN2ExZDVjZDYyY2QzYiINCn0NCg==", "sha256": "95e337416773c6ed99cc8bc1caa82736c30ee829c606317a8837b51c4c0d1461"}, "receipts/FREEZE.json": {"base64": "ew0KICAia2luZCI6ICJGUkVFWkUiLA0KICAic2NvcGUiOiAiQ0FNUEFJR04iLA0KICAicGFja2FnZV9oYXNoIjogImM3NmZjNTQwMThjZTZiOWU5Zjc3ZWViMjk0NmNlYTI1MzI3MWFkNGE4NTczZjhmZTA0Nzk2MWQ3YjZmNmRjNmIiLA0KICAicG9saWN5X2hhc2giOiAiZDA4OTlkMmRiOWY4NThlN2RjMTBiZDljOTVhODgxOWE3MzM1ZjY0MWE1OWEwMGRiNTEzZjA1YzQ2OTZjYmRjMSIsDQogICJzY2hlZHVsZV9oYXNoIjogIjhjYWViZTFhNzBhYTg3ZDY2YzJmNzJkNWFkZTRhODJkZWU4Mjk4ZmY4NDQ5YTRmZWZmMmYwNWMxYTZkNDQxNzQiLA0KICAicHJlZGVjZXNzb3JfaGFzaCI6ICI2NTgxNmUwZTE4NmZlNDJhNzgzM2I0NWJiNTYzZGQwYWY5Y2IzZGVjM2QzM2Y1YTZmNzMwY2RlMjM3NWYzMDliIiwNCiAgImV4cGlyZXNfYXQiOiAiOTk5OS0xMi0zMVQyMzo1OTo1OSswMDowMCIsDQogICJzaWduZXIiOiAiSHVtYW4gYWNjZXB0YW5jZSByZWNvcmRlZCBieSB0aGUgbG9jYWwgRllQIG9wZXJhdG9yIiwNCiAgInNpZ25hdHVyZSI6ICJiNTQwZWFiNDgzMGIwZmI4YTYyOTQxMjEwNGJjOTZmMDk5ZDY1ODgwMDhmNTM5M2QzMGUxNGMwZmMwNTczYWU5Ig0KfQ0K", "sha256": "0435a37f534b8a8cde77104840c0fb81323011f7f21d93b4ebc38260a09222b2"}, "receipts/LAUNCH.json": {"base64": "ew0KICAia2luZCI6ICJMQVVOQ0giLA0KICAic2NvcGUiOiAiQ0FNUEFJR04iLA0KICAicGFja2FnZV9oYXNoIjogImM3NmZjNTQwMThjZTZiOWU5Zjc3ZWViMjk0NmNlYTI1MzI3MWFkNGE4NTczZjhmZTA0Nzk2MWQ3YjZmNmRjNmIiLA0KICAicG9saWN5X2hhc2giOiAiODdmZjNhYzk4YzhmNzY0NmVjZDI1ZWNiNjQxZTdmZmQ0OWU1MDA4YTFkMGIzYzhmOTdjY2E2YTdkMDkxZTI0NiIsDQogICJzY2hlZHVsZV9oYXNoIjogIjhjYWViZTFhNzBhYTg3ZDY2YzJmNzJkNWFkZTRhODJkZWU4Mjk4ZmY4NDQ5YTRmZWZmMmYwNWMxYTZkNDQxNzQiLA0KICAicHJlZGVjZXNzb3JfaGFzaCI6ICI4N2FlZWIzYmU4YjNiYzdiMzgyYzdhMTVhYzhmMWI0NTY5OWNlMTNhNzNkZDFjNDgwZGU4YzVjMmY5NDc1ZjM4IiwNCiAgImV4cGlyZXNfYXQiOiAiMjAyNi0xMC0yMlQxNToyNDoyMy44MTA2NzQrMDA6MDAiLA0KICAic2lnbmVyIjogIkh1bWFuLWF1dGhvcml6ZWQgbG9jYWwgRllQIGRlcGxveW1lbnQgb3BlcmF0b3IiLA0KICAic2lnbmF0dXJlIjogIjIzMDBhMTE3YjdjNmYwZTk0NGYwODBiZDFmYmE4MGFiZDdkNmIxYjZjMWI5YjExOTZlZDZhMjVhZDIzN2E2ZTIiDQp9DQo=", "sha256": "35b9d06c9676baadffd4561bf2489b2bc1b08afce28fca5f1e259657f841bcd9"}, "continuation-receipts/CONTINUATION_ACCEPTED.json": {"base64": "ew0KICAia2luZCI6ICJDT05USU5VQVRJT05fQUNDRVBURUQiLA0KICAicGFja2FnZV9oYXNoIjogImMzMDgyMjIwOTZjZjNjOTAyNmFhMjc1ZTczZmQ3ZDc1YmNlMzg2ZTY0MTgyNDMzMGYzODVkYWIwMmQ0YjYwOWYiLA0KICAicHJlZGVjZXNzb3JfaGFzaCI6ICI5OGNiZWRiNmYxNWVjMDI3YjU4YThjZTViYWE3YjQ3NTE1YTFjOWNiMGFiODgxNjEwODRhMTgyMjg4ZGJkMTIyIiwNCiAgInBvbGljeV9zaGEyNTYiOiAiODdmZjNhYzk4YzhmNzY0NmVjZDI1ZWNiNjQxZTdmZmQ0OWU1MDA4YTFkMGIzYzhmOTdjY2E2YTdkMDkxZTI0NiIsDQogICJpZGVudGl0aWVzX3NoYTI1NiI6ICI1YWE1NmZlZjExNmI1NWI4MzliNThjMDViODVkN2NkMWQzZWIwMzBhY2IxYjZkOWNkMTU2ZTY0MGIyODVlZDhkIiwNCiAgInBhcmVudF9mcmVlemVfc2hhMjU2IjogIjA0MzVhMzdmNTM0YjhhOGNkZTc3MTA0ODQwYzBmYjgxMzIzMDExZjdmMjFkOTNiNGViYzM4MjYwYTA5MjIyYjIiLA0KICAiZmlyc3RfZXhwb3J0X3NoYTI1NiI6ICIyODMwMDFkYzFhNTkwNGYzZThiNGRlODkzZWY2NThkMmU3ZmU4MDUzYjhlOThlZDdiYWFkNmYyNDJkMzE4ZDhiIiwNCiAgImV4cGlyZXNfYXQiOiAiMjAyNi0xMC0yMlQxNToyNDoyMy44MTA2NzQrMDA6MDAiLA0KICAic2lnbmVyIjogIkV4cGxpY2l0IGh1bWFuIGluc3RydWN0aW9uIHJlY29yZGVkIGJ5IGxvY2FsIEZZUCBvcGVyYXRvciIsDQogICJyZWFkaW5lc3Nfc2hhMjU2IjogbnVsbCwNCiAgImluc3RhbmNlX2lkIjogbnVsbCwNCiAgInNpZ25hdHVyZSI6ICIwNTY3OTc5YTVmZmIyMDc3YmE2NjNhZTY5MWNjOWU3ZjM4NDQ2NzgzN2NlYjNkOTViYzhhNGYwY2UxMjI4ZWMwIg0KfQ0K", "sha256": "2f43d2cae1320d75166df44e546b203ba997f6f098bed18440e8f87ca3365cf5"}, "continuation-receipts/CONTINUATION_FREEZE.json": {"base64": "ew0KICAia2luZCI6ICJDT05USU5VQVRJT05fRlJFRVpFIiwNCiAgInBhY2thZ2VfaGFzaCI6ICJjMzA4MjIyMDk2Y2YzYzkwMjZhYTI3NWU3M2ZkN2Q3NWJjZTM4NmU2NDE4MjQzMzBmMzg1ZGFiMDJkNGI2MDlmIiwNCiAgInByZWRlY2Vzc29yX2hhc2giOiAiNWE0NzA5MTJhOWI5NzgwMTAwMmFmN2VlNWI5MzI4MzJjZTA3NWEyNjU0MjljMjI3MTRlNWI3ZDVlMmJmNzEzOSIsDQogICJwb2xpY3lfc2hhMjU2IjogIjg3ZmYzYWM5OGM4Zjc2NDZlY2QyNWVjYjY0MWU3ZmZkNDllNTAwOGExZDBiM2M4Zjk3Y2NhNmE3ZDA5MWUyNDYiLA0KICAiaWRlbnRpdGllc19zaGEyNTYiOiAiNWFhNTZmZWYxMTZiNTViODM5YjU4YzA1Yjg1ZDdjZDFkM2ViMDMwYWNiMWI2ZDljZDE1NmU2NDBiMjg1ZWQ4ZCIsDQogICJwYXJlbnRfZnJlZXplX3NoYTI1NiI6ICIwNDM1YTM3ZjUzNGI4YThjZGU3NzEwNDg0MGMwZmI4MTMyMzAxMWY3ZjIxZDkzYjRlYmMzODI2MGEwOTIyMmIyIiwNCiAgImZpcnN0X2V4cG9ydF9zaGEyNTYiOiAiMjgzMDAxZGMxYTU5MDRmM2U4YjRkZTg5M2VmNjU4ZDJlN2ZlODA1M2I4ZTk4ZWQ3YmFhZDZmMjQyZDMxOGQ4YiIsDQogICJleHBpcmVzX2F0IjogIjIwMjYtMTAtMjJUMTU6MjQ6MjMuODEwNjc0KzAwOjAwIiwNCiAgInNpZ25lciI6ICJFeHBsaWNpdCBodW1hbiBpbnN0cnVjdGlvbiByZWNvcmRlZCBieSBsb2NhbCBGWVAgb3BlcmF0b3IiLA0KICAicmVhZGluZXNzX3NoYTI1NiI6IG51bGwsDQogICJpbnN0YW5jZV9pZCI6IG51bGwsDQogICJzaWduYXR1cmUiOiAiZGJkZjRmNWVmYjlmYzRiZjVlOGJhZWE3MTgyYmVmMTlmNThhYjMxZmRlODY2YWNiNTJiOTUyYWE4NDAyNDY0MSINCn0NCg==", "sha256": "e74cde4ab23b11c88338e8f40a201f00b53c263ed62fae4048b3fe389db6a779"}}, "clear_key_included": false}
ENVELOPE
cd /opt/fyp-phase8-continuation-v1
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
install -d -m 700 /root/.aws
test ! -e /root/.aws/config
printf '%s\n' '[profile fyp-research]' 'region = ap-southeast-2' >/root/.aws/config
.venv/bin/python -B - <<'PY'
import base64,gzip,hashlib,json,os,shutil,socket,sqlite3,subprocess,sys,tarfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-continuation/v1'))
from controls import Authority,Journal,guard,hash_file,read,utc,write_new
from handover import ContinuationAuthority,ContinuationPolicy,bind_host_segment,stage,verify_imported_first,verify_members
from storage import ObjectProof,S3Cloud,upload,verify_local
from postflight import recover
from transport import S3Store
from research.execution_linux_v1.platform import host
root=Path('/var/lib/p8-continuation/run'); deployment=Path('/var/lib/p8-continuation/deployment')
owner=Path('/var/lib/fyp-owner'); value=read(deployment/'owner-envelope.json')
if value['target_instance']!='i-034252c3e9b083abf':raise ValueError('OWNER_ENVELOPE_WRONG_HOST')
with (deployment/'wrapped-owner.bin').open('xb') as out:out.write(base64.b64decode(value['encrypted_owner_key']))
if (owner/'owner.key').exists():raise ValueError('EXISTING_KEY_RETAIN_ATTEMPT')
subprocess.run(['openssl','pkeyutl','-decrypt','-inkey',str(owner/'transfer-private.pem'),'-in',str(deployment/'wrapped-owner.bin'),'-out',str(owner/'owner.key'),'-pkeyopt','rsa_padding_mode:oaep','-pkeyopt','rsa_oaep_md:sha256','-pkeyopt','rsa_mgf1_md:sha256'],check=True,timeout=15)
(owner/'owner.key').chmod(0o600)
for name,spec in value['public_files'].items():
 raw=base64.b64decode(spec['base64'])
 if hashlib.sha256(raw).hexdigest()!=spec['sha256']:raise ValueError('PUBLIC_RECEIPT_BYTES_DRIFT')
 target=owner/name
 with target.open('xb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
 target.chmod(0o600)
store=S3Store('fyp-research'); proofs=[]
for obj in read(Path.cwd()/'artifacts/phase-8-launch/v1/local-postflight.json')['objects']:
 proof=ObjectProof.model_validate(obj['proof']); destination=deployment.parent/'retained'/obj['label']
 recovered=recover(proof,destination,store)
 verify_members(recovered/'slot')
 proofs.append(proof.model_dump())
first=deployment.parent/'retained/slot1/x/slot'
manifest=read(first/'manifest.json')
if not manifest['postgres_dumps'] or not {'setup_app.sql.gz','setup_truth.sql.gz'}.issubset(manifest['files']):raise ValueError('FIRST_DUMPS_MISSING')
for name in ('setup_app.sql.gz','setup_truth.sql.gz'):
 with gzip.open(first/name,'rb') as source:
  while source.read(1024**2):pass
stage(deployment.parent/'retained/master/x/slot',first,root)
verify_imported_first(root)
bind_host_segment(root)
authority=ContinuationAuthority(root,read(root/'run.json'));authority.verify(prelaunch=True)
backup=Path('/var/lib/p8-continuation/backup');backup.mkdir(exist_ok=False)
policy=authority.policy; cloud=S3Cloud(policy.cloud_bucket,f'exports/phase8/{policy.run_id}/')
sample=host(root,backup);sample.update(working_bytes=0,backup_bytes=0)
cloud_bytes=cloud.inventory();guard(policy,sample,utc(),cloud_bytes,extra_bytes=policy.slot_capacity_reserve_bytes)
for port in (16432,16433,19100,19101,19102,19110):
 with socket.socket() as s:s.bind(('127.0.0.1',port))
if owner.stat().st_mode&0o777!=0o700 or (owner/'owner.key').stat().st_mode&0o777!=0o600:raise ValueError('PRIVATE_OWNER_PERMISSIONS')
probe=deployment/'permission-probe.json';write_new(probe,{'kind':'PRELAUNCH_PERMISSION_PROBE_NOT_RESEARCH_OUTCOME','at_utc':utc().isoformat(),'run_id':policy.run_id})
probe_proof=cloud.put(probe,cloud.prefix+'continuation-v1/deployment/permission-probe.json');cloud.verify(probe_proof)
with store.client.get_object(Bucket=probe_proof.bucket,Key=probe_proof.key,VersionId=probe_proof.version_id)['Body'] as body:
 if hashlib.sha256(body.read()).hexdigest()!=probe_proof.sha256:raise ValueError('PERMISSION_PROBE_GET_DRIFT')
if store.client.get_bucket_versioning(Bucket=policy.cloud_bucket).get('Status')!='Enabled':raise ValueError('VERSIONING_DISABLED')
# A public master snapshot before main admission; no new slot or driver.
folder=backup/'prelaunch-attempt1';folder.mkdir(exist_ok=False);journal=Journal(root);journal.verify()
with journal.connect() as source,sqlite3.connect(folder/'campaign.sqlite3') as target:
 source.backup(target)
 if target.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('PRELAUNCH_LEDGER_CORRUPTION')
for name in ('run.json','bindings.json','binding-seal.json','cloud.json','host-clock.json','handover.json','saved-identities.json'):
 shutil.copyfile(root/name,folder/name)
for prefix,names in (('receipts',('REVIEW_ACCEPTED','FREEZE','LAUNCH')),('continuation-receipts',('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'))):
 dest=folder/'public-authority'/prefix;dest.mkdir(parents=True)
 for name in names:shutil.copyfile(owner/prefix/(name+'.json'),dest/(name+'.json'))
shutil.copytree(root/'backups',folder/'backups')
shutil.copyfile(deployment/'source-ready.json',folder/'source-ready.json')
files={p.relative_to(folder).as_posix():hash_file(p) for p in folder.rglob('*') if p.is_file()}
write_new(folder/'manifest.json',{'kind':'PRELAUNCH_CONTINUATION_MASTER_NOT_EXECUTION','postgres_dumps':False,'files':files})
archive=folder.with_suffix('.tar.gz')
with tarfile.open(archive,'x:gz') as out:out.add(folder,arcname='slot')
verify_local(archive,hash_file(archive));proof=upload(journal,cloud,policy,archive);cloud.verify(proof)
readback= recover(proof,deployment.parent/'prelaunch-readback',store)
verify_members(readback/'slot')
journal.event('CONTINUATION_PRELAUNCH_BACKUP_VERIFIED',proof=proof.model_dump())
write_new(deployment/'import-and-backup-readiness.json',{'status':'PASS','at_utc':utc().isoformat(),'run_id':policy.run_id,'instance_id':'i-034252c3e9b083abf','imported_first_raw_status':'FAILED','rows':1500,'backed_up':1,'planned':1499,'driver_calls':0,'original_backups':proofs,'prelaunch_backup':proof.model_dump(),'permission_probe':probe_proof.model_dump(),'host':sample,'cloud_bytes':cloud_bytes,'owner_mode':'0700/0600','source_and_freeze_chain':'PASS','boot_segment_bound':True,'operational_clock_reset':False,'original_deadline_utc':policy.stop_at.isoformat(),'estimated_committed_usd':policy.committed_cost(utc())})
print(json.dumps(read(deployment/'import-and-backup-readiness.json')))
PY
systemctl is-active fyp-p85-continuation-bootstrap-stop.timer fyp-p85-continuation-preparation-stop.timer
printf '%s\n' IMPORT_BACKUP_VERIFIED_MAIN_NOT_STARTED
