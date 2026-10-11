set -euo pipefail
umask 077
systemctl stop fyp-phase8-campaign.service fyp-phase8-watchdog.service
systemctl is-active docker fyp-p85-continuation-bootstrap-stop.timer
install -d -m 700 /var/lib/p8-continuation-v7/deployment
cat >/var/lib/p8-continuation-v7/deployment/bootstrap-objects.json <<'OBJECTS'
[{"bucket": "fyp-p82-20261005-018da1d6-803656589923", "key": "exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/continuation-v7/deployment/c5a90f1830b1b53a5cdafbe88daf909cb028382a281a10ecbac299016355d152-v7-complete-continuation-review-candidate.tar.gz", "version_id": "D1iG1HiWHJWti0UQeSuLTCMLu0ibPLM_", "sha256": "c5a90f1830b1b53a5cdafbe88daf909cb028382a281a10ecbac299016355d152", "bytes": 120884050, "expanded_bytes": 438045391, "label": "package.tar.gz"}, {"bucket": "fyp-p82-20261005-018da1d6-803656589923", "key": "exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/continuation-v7/deployment/15f9600bc05e6dc214d9de32e2527eee4cc6ec5683691e24e9ffb6a3408b448d-public-authority.tar.gz", "version_id": "G_FDqOn9MGeWhidmMWGC5949yGrJgSAM", "sha256": "15f9600bc05e6dc214d9de32e2527eee4cc6ec5683691e24e9ffb6a3408b448d", "bytes": 121650, "label": "authority.tar.gz", "expanded_bytes": 407329}]
OBJECTS
cat >/var/lib/p8-continuation-v7/deployment/bootstrap-transfer.py <<'TRANSFER'
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
    deployment = Path('/var/lib/p8-continuation-v7/deployment')
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
    root = Path('/opt/fyp-phase8-continuation-v7')
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
timeout --signal=TERM --kill-after=5s 600s /opt/fyp-phase8-combined-v4/.venv/bin/python -B /var/lib/p8-continuation-v7/deployment/bootstrap-transfer.py
cd /opt/fyp-phase8-continuation-v7
for env in .venv .venv-analysis .venv-transport; do ln -s "/opt/fyp-phase8-combined-v4/$env" "$env"; done
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B -m research.execution_linux_v1.portable
.venv/bin/python -B - <<'PY'
import hmac,hashlib,json,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import canonical,read,hash_file,write_new
dep=Path('/var/lib/p8-continuation-v7/deployment');public=dep/'authority.tar.gz.extract';owner=Path('/var/lib/fyp-owner');key=(owner/'owner.key').read_bytes()
m=read(public/'freeze-manifest.json');att=read(public/'freeze-attestation.json')
if hash_file(public/'freeze-manifest.json')!='3a4bf3b0f6d833bc89744778557258f6612a3622337511fb6ff9841ce27f5e46' or not hmac.compare_digest(att['signature'],hmac.new(key,canonical(m),'sha256').hexdigest()):raise ValueError('V7_FREEZE_SIGNATURE_DRIFT')
inv=read(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json')
if inv['package_hash']!='9221ef77f4b0d223d6e03993c401cfa9b7d50aaea1db9b6659e478654de28817' or hashlib.sha256(canonical(inv['files'])).hexdigest()!=inv['package_hash']:raise ValueError('EXACT_V7_PACKAGE_DRIFT')
for n,d in inv['files'].items():
 if hash_file(Path.cwd()/n)!=d:raise ValueError('V7_SOURCE_MEMBER_DRIFT: '+n)
receipt_dir=owner/'continuation-v7-receipts';receipt_dir.mkdir(mode=0o700,exist_ok=False)
for kind in ('CONTINUATION_ACCEPTED','CONTINUATION_FREEZE'):
 p=public/(kind+'.json');raw=read(p);body={k:v for k,v in raw.items() if k!='signature'}
 if not hmac.compare_digest(raw['signature'],hmac.new(key,canonical(body),'sha256').hexdigest()):raise ValueError('V7_RECEIPT_SIGNATURE_DRIFT')
 shutil.copyfile(p,receipt_dir/p.name);(receipt_dir/p.name).chmod(0o600)
write_new(dep/'source-and-authority-ready.json',{'status':'PASS','source_files':len(inv['files']),'freeze_manifest_sha256':hash_file(public/'freeze-manifest.json'),'package_hash':inv['package_hash'],'dependency_install_or_upgrade':False,'driver_calls':0})
print(json.dumps(read(dep/'source-and-authority-ready.json')))
PY
