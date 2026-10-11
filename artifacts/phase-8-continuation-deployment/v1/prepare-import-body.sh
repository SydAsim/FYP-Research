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
