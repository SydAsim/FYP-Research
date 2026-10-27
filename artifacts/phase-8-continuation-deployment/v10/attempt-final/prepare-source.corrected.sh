set -euo pipefail
umask 077
install -d -m 700 /var/lib/p8-continuation-v10/deployment
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
test ! -e /opt/fyp-phase8-continuation-v10
test ! -e /var/lib/p8-continuation-v10/deployment/package.tar.gz
/opt/fyp-phase8-combined-v4/.venv/bin/python -B - <<'IMPORT_CHECK'
import boto3,botocore,sys,hashlib,json
from pathlib import Path
assert sys.version_info[:3]==(3,12,13),'PINNED_TRANSPORT_INTERPRETER'
qualified=json.loads(Path('/var/lib/p8-combined-v4/deployment/host-health-readiness.json').read_text())
assert sys.version==qualified['python'],'QUALIFIED_HOST_PYTHON_BUILD_DRIFT'
print(json.dumps({'kind':'EXISTING_HOST_TRANSPORT_BINDING','python':sys.version,'binary_sha256':hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest()}))
print('PASS_PINNED_EXISTING_TRANSPORT_IMPORT')
IMPORT_CHECK
cat >/var/lib/p8-continuation-v10/deployment/bootstrap-objects.json <<'OBJECTS'
[{"bucket": "fyp-p82-20261005-018da1d6-803656589923", "key": "exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/continuation-v10/deployment/212269264d45ac8bd6637c2ca0ca5e09c951d354cb445c9bf7a16c6ba2d0ba37-v10-complete-continuation.tar.gz", "version_id": "QmAcYmVhFW5GHo08qBB01sD.laBJlcyo", "sha256": "212269264d45ac8bd6637c2ca0ca5e09c951d354cb445c9bf7a16c6ba2d0ba37", "bytes": 292118202, "expanded_bytes": 972556042, "label": "package.tar.gz"}]
OBJECTS
cat >/var/lib/p8-continuation-v10/deployment/bootstrap-transfer.py <<'TRANSFER'
"""Bounded first source transfer on an empty host; no driver or authorization signing."""
import hashlib
import json
import os
import shutil
import tarfile
import time
from pathlib import Path, PurePosixPath

import boto3
from botocore.config import Config


def main() -> None:
    deployment = Path('/var/lib/p8-continuation-v10/deployment')
    objects = json.loads((deployment / 'bootstrap-objects.json').read_text())
    s3 = boto3.client('s3', region_name='ap-southeast-2', config=Config(
        connect_timeout=5, read_timeout=25, retries={'total_max_attempts': 2, 'mode': 'standard'}))
    for obj in objects:
        target = deployment / obj['label']
        deadline = time.monotonic() + 180
        response = s3.get_object(Bucket=obj['bucket'], Key=obj['key'], VersionId=obj['version_id'])
        if response.get('VersionId') != obj['version_id']:
            raise ValueError('PINNED_VERSION_MISMATCH')
        try:
            with target.open('xb') as output:
                for block in response['Body'].iter_chunks(1024**2):
                    if time.monotonic() >= deadline:
                        raise TimeoutError('BOOTSTRAP_TRANSFER_LIMIT_RETAIN_PARTIAL')
                    if output.tell()+len(block)>obj['bytes']:raise ValueError('BOOTSTRAP_SIZE_BOUND')
                    output.write(block)
                output.flush()
                os.fsync(output.fileno())
        finally:
            response['Body'].close()
        if target.stat().st_size != obj['bytes']:
            raise ValueError('BOOTSTRAP_SIZE_DRIFT')
        with target.open('rb') as source:
            got = hashlib.file_digest(source, 'sha256').hexdigest()
        if got != obj['sha256']:
            raise ValueError('BOOTSTRAP_HASH_DRIFT_RETAIN_ATTEMPT')
        destination = deployment / (obj['label'] + '.extract')
        with tarfile.open(target, 'r:gz') as incoming:
            members = incoming.getmembers()
            names = set()
            for member in members:
                p = PurePosixPath(member.name)
                if p.is_absolute() or '..' in p.parts or '\\' in member.name or not (
                        member.isfile() or member.isdir()) or member.name in names:
                    raise ValueError('UNSAFE_BOOTSTRAP_ARCHIVE')
                names.add(member.name)
            if sum(m.size for m in members) != obj['expanded_bytes']:
                raise ValueError('BOOTSTRAP_EXPANSION_LIMIT')
            destination.mkdir(exist_ok=False)
            incoming.extractall(destination, members=members, filter='data')
        with (deployment / (obj['label'] + '.verified.json')).open('x') as out:
            json.dump({'sha256': got, 'object': obj, 'members': len(members),
                       'partial_evidence_preserved': True, 'driver_calls': 0}, out)
    root = Path('/opt/fyp-phase8-continuation-v10')
    (deployment / 'package.tar.gz.extract').rename(root)
    inventory = json.loads((root / 'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json').read_text())
    for name, expected in inventory['files'].items():
        with (root / name).open('rb') as source:
            if hashlib.file_digest(source, 'sha256').hexdigest() != expected:
                raise ValueError('CONTINUATION_SOURCE_DRIFT: ' + name)
    with (deployment / 'source-ready.json').open('x') as out:
        json.dump({'status': 'PASS', 'source_files': len(inventory['files']),
                   'package_hash': inventory['package_hash'], 'driver_calls': 0}, out)


if __name__ == '__main__':
    main()

TRANSFER
timeout --signal=TERM --kill-after=5s 300s /opt/fyp-phase8-combined-v4/.venv/bin/python -B /var/lib/p8-continuation-v10/deployment/bootstrap-transfer.py
/opt/fyp-phase8-combined-v4/.venv/bin/python -B - <<'AUTHORITY'
import base64,gzip,tarfile,io,json,hashlib,hmac
from pathlib import Path
source=Path('/opt/fyp-phase8-continuation-v10');owner=Path('/var/lib/fyp-owner');dep=Path('/var/lib/p8-continuation-v10/deployment')
assert owner.stat().st_mode&0o777==0o700 and (owner/'owner.key').stat().st_mode&0o777==0o600
for name in ('.venv','.venv-analysis','.venv-transport'):(source/name).symlink_to(Path('/opt/fyp-phase8-combined-v4')/name,target_is_directory=True)
data=gzip.decompress(base64.b64decode('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'))
assert hashlib.sha256(data).hexdigest()=='68684a4a134ec8189ae968304c4f87b4f4a9cb0769e4bda3eca24d622f19a6aa'
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
