set -euo pipefail
umask 077
install -d -m 700 /var/lib/p8-continuation-v9/deployment
cat >/var/lib/p8-continuation-v9/deployment/bootstrap-objects.json <<'OBJECTS'
[{"bucket": "fyp-p82-20261005-018da1d6-803656589923", "key": "exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/continuation-v9/deployment/aba46ecaca5ead14e6e2ef75c21e019f4b652f517a6a72f1c4090669596e81a0-v9-complete-continuation-candidate.tar.gz", "version_id": "16NgW5CaJ79GO_ybVjfHfHRnGs1cC2Q7", "sha256": "aba46ecaca5ead14e6e2ef75c21e019f4b652f517a6a72f1c4090669596e81a0", "bytes": 279489039, "expanded_bytes": 966579129, "label": "package.tar.gz"}, {"bucket": "fyp-p82-20261005-018da1d6-803656589923", "key": "exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/continuation-v9/deployment/4c65d8b22ae7e13eb20c67f62afd3130b26166b14e4c989d9f185b7ef72a9c8e-public-authority.tar.gz", "version_id": "G4aBG.9uK1_XCo5a9cR9s39UjqMW0vxh", "sha256": "4c65d8b22ae7e13eb20c67f62afd3130b26166b14e4c989d9f185b7ef72a9c8e", "bytes": 163403, "label": "authority.tar.gz", "expanded_bytes": 598986}]
OBJECTS
cat >/var/lib/p8-continuation-v9/deployment/bootstrap-transfer.py <<'TRANSFER'
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
    deployment = Path('/var/lib/p8-continuation-v9/deployment')
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
    root = Path('/opt/fyp-phase8-continuation-v9')
    shutil.copytree(deployment / 'package.tar.gz.extract', root)
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
set -euo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
test ! -e /var/lib/p8-continuation-v9/deployment/package.tar.gz
test ! -e /opt/fyp-phase8-continuation-v9
/opt/fyp-phase8-combined-v4/.venv/bin/python -B - <<'TRANSPORT_CHECK'
import importlib.metadata,json,sys
from pathlib import Path
import boto3,botocore
assert sys.version_info[:3]==(3,12,13)
assert sys.executable=='/opt/fyp-phase8-combined-v4/.venv/bin/python'
assert Path(boto3.__file__).resolve().is_relative_to(Path('/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages').resolve())
record={'status':'PASS','interpreter':sys.executable,'python':sys.version,'boto3':boto3.__version__,'botocore':botocore.__version__,'boto3_path':boto3.__file__,'qualified_v5_transport_environment':True,'dependency_install':False}
with Path('/var/lib/p8-continuation-v9/deployment/transport-import-attempt2.json').open('x') as output:json.dump(record,output,indent=2)
print(json.dumps(record))
TRANSPORT_CHECK
timeout --signal=TERM --kill-after=5s 600s /opt/fyp-phase8-combined-v4/.venv/bin/python -B /var/lib/p8-continuation-v9/deployment/bootstrap-transfer.py
cd /opt/fyp-phase8-continuation-v9
for env in .venv .venv-analysis .venv-transport; do ln -s "/opt/fyp-phase8-combined-v4/$env" "$env"; done
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B -m research.execution_linux_v1.portable
.venv/bin/python -B - <<'PY'
import hmac,hashlib,json,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import canonical,read,hash_file,write_new
dep=Path('/var/lib/p8-continuation-v9/deployment');public=dep/'authority.tar.gz.extract';owner=Path('/var/lib/fyp-owner');key=(owner/'owner.key').read_bytes()
m=read(public/'freeze-manifest.json');att=read(public/'freeze-attestation.json')
if hash_file(public/'freeze-manifest.json')!='c4ed361b1af81bd90e1148333d0f106b02e7e401a8a6930f19507a7ddbd6872c' or not hmac.compare_digest(att['signature'],hmac.new(key,canonical(m),'sha256').hexdigest()):raise ValueError('V7_FREEZE_SIGNATURE_DRIFT')
inv=read(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json')
if inv['package_hash']!='5cbf273011c505984fe103955a94a256b1c84d1683de74cfa7a2a396cc223b60' or hashlib.sha256(canonical(inv['files'])).hexdigest()!=inv['package_hash']:raise ValueError('EXACT_V7_PACKAGE_DRIFT')
for n,d in inv['files'].items():
 if hash_file(Path.cwd()/n)!=d:raise ValueError('V7_SOURCE_MEMBER_DRIFT: '+n)
receipt_dir=owner/'continuation-v9-receipts';receipt_dir.mkdir(mode=0o700,exist_ok=False)
for kind in ('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'):
 p=public/(kind+'.json');raw=read(p);body={k:v for k,v in raw.items() if k!='signature'}
 if not hmac.compare_digest(raw['signature'],hmac.new(key,canonical(body),'sha256').hexdigest()):raise ValueError('V7_RECEIPT_SIGNATURE_DRIFT')
 shutil.copyfile(p,receipt_dir/p.name);(receipt_dir/p.name).chmod(0o600)
write_new(dep/'source-and-authority-ready.json',{'status':'PASS','source_files':len(inv['files']),'freeze_manifest_sha256':hash_file(public/'freeze-manifest.json'),'package_hash':inv['package_hash'],'dependency_install_or_upgrade':False,'driver_calls':0})
print(json.dumps(read(dep/'source-and-authority-ready.json')))
PY
