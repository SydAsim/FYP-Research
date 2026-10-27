"""External deployment rendering; no frozen-source or dependency changes."""
import base64
import gzip
import hashlib
import json
import tarfile
from pathlib import Path
from ops import HERE,record

def main():
    proof=json.loads((HERE.parent/'source-proof.json').read_text())
    archive=Path('D:/FYP-ResearchBackups/classifier-145-v2/v10-complete-continuation.tar.gz')
    with tarfile.open(archive) as t:expanded=sum(m.size for m in t)
    proof.update(expanded_bytes=expanded,label='package.tar.gz')
    authority=(HERE.parent/'public-authority-v10.tar.gz').read_bytes()
    payload=base64.b64encode(gzip.compress(authority)).decode()
    bootstrap=(HERE.parent.parent/'v9/bootstrap-transfer.py').read_text()
    bootstrap=bootstrap.replace('continuation-v9','continuation-v10')
    bootstrap=bootstrap.replace("shutil.copytree(deployment / 'package.tar.gz.extract', root)","(deployment / 'package.tar.gz.extract').rename(root)")
    bootstrap=bootstrap.replace("output.write(block)","if output.tell()+len(block)>obj['bytes']:raise ValueError('BOOTSTRAP_SIZE_BOUND')\n                    output.write(block)")
    header='''set -euo pipefail
umask 077
install -d -m 700 /var/lib/p8-continuation-v10/deployment
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
test ! -e /opt/fyp-phase8-continuation-v10
test ! -e /var/lib/p8-continuation-v10/deployment/package.tar.gz
/opt/fyp-phase8-combined-v4/.venv/bin/python -B - <<'IMPORT_CHECK'
import boto3,botocore,sys,hashlib
from pathlib import Path
assert sys.version_info[:3]==(3,12,13),'PINNED_TRANSPORT_INTERPRETER'
assert hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest()=='0e6475dfda68a9b2d93501449fc47593ca169010e8f4881577b97463fd0c1263'
print('PASS_PINNED_EXISTING_TRANSPORT_IMPORT')
IMPORT_CHECK
'''
    script=header+"cat >/var/lib/p8-continuation-v10/deployment/bootstrap-objects.json <<'OBJECTS'\n"+json.dumps([proof])+"\nOBJECTS\ncat >/var/lib/p8-continuation-v10/deployment/bootstrap-transfer.py <<'TRANSFER'\n"+bootstrap+"\nTRANSFER\ntimeout --signal=TERM --kill-after=5s 300s /opt/fyp-phase8-combined-v4/.venv/bin/python -B /var/lib/p8-continuation-v10/deployment/bootstrap-transfer.py\n"
    script+='''/opt/fyp-phase8-combined-v4/.venv/bin/python -B - <<'AUTHORITY'
import base64,gzip,tarfile,io,json,hashlib,hmac
from pathlib import Path
source=Path('/opt/fyp-phase8-continuation-v10');owner=Path('/var/lib/fyp-owner');dep=Path('/var/lib/p8-continuation-v10/deployment')
assert owner.stat().st_mode&0o777==0o700 and (owner/'owner.key').stat().st_mode&0o777==0o600
for name in ('.venv','.venv-analysis','.venv-transport'):(source/name).symlink_to(Path('/opt/fyp-phase8-combined-v4')/name,target_is_directory=True)
data=gzip.decompress(base64.b64decode('''+repr(payload)+'''))
assert hashlib.sha256(data).hexdigest()=='''+repr(hashlib.sha256(authority).hexdigest())+'''
with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
    members=t.getmembers();assert len(members)<20 and all(m.isfile() and Path(m.name).name==m.name for m in members)
    records={m.name:t.extractfile(m).read() for m in members}
canonical=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
key=(owner/'owner.key').read_bytes();manifest=json.loads(records['freeze-manifest.json'])
assert hashlib.sha256(records['freeze-manifest.json']).hexdigest()=='e4b6888f560575c5808267947a0a8b62b9b678dbbf6e1d07c20880a88aeda74b'
assert hmac.compare_digest(json.loads(records['freeze-attestation.json'])['signature'],hmac.new(key,canonical(manifest),'sha256').hexdigest())
assert manifest['package_hash']=='bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c'
for name,digest in manifest['files'].items():
    assert hashlib.sha256(records[name]).hexdigest()==digest
    v=json.loads(records[name]);signature=v.pop('signature');assert hmac.compare_digest(signature,hmac.new(key,canonical(v),'sha256').hexdigest())
dest=dep/'public-authority';dest.mkdir(mode=0o700,exist_ok=False)
for name,b in records.items():
    p=dest/name
    with p.open('xb') as f:f.write(b)
    p.chmod(0o600)
receipts=owner/'continuation-v10-receipts';receipts.mkdir(mode=0o700,exist_ok=False)
for name in ('CONTINUATION_ACCEPTED.json','CONTINUATION_FREEZE.json'):
    p=receipts/name
    with p.open('xb') as f:f.write(records[name])
    p.chmod(0o600)
inventory=json.loads((source/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json').read_text())
assert hashlib.sha256(canonical(inventory['files'])).hexdigest()==inventory['package_hash']==manifest['package_hash']
for name,digest in inventory['files'].items():
    with (source/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest,'SOURCE_CLOSURE_DRIFT:'+name
print(json.dumps({'status':'PASS_V10_SOURCE_AND_PUBLIC_AUTHORITY','package_hash':inventory['package_hash'],'source_members':len(inventory['files']),'archive_sha256':manifest['archive_sha256'],'signing_key_transferred':False,'driver_calls':0}))
AUTHORITY
'''
    (HERE/'prepare-source.sh').write_text(script,encoding='utf-8',newline='\n')
    record('source-rendering.json',{'source_proof':proof,'authority_bytes':len(authority),'authority_sha256':hashlib.sha256(authority).hexdigest(),
        'bootstrap_parent':'v9/bootstrap-transfer.py','external_differences':['v10 paths','existing pinned v10 source object','rename verified extraction instead of duplicate copytree','stream exact bytes bound'],
        'private_key_in_payload':False,'frozen_source_changed':False})
    print('External source rendering ready; existing interpreter import precedes transfer.')

if __name__=='__main__':main()
