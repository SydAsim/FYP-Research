#!/bin/bash
set -euo pipefail
umask 077
cloud-init status --wait
systemctl is-active docker fyp-p85-continuation-bootstrap-stop.timer fyp-p85-continuation-preparation-stop.timer fyp-p85-combined-preparation-absolute.timer
cat >/var/lib/p8-combined/deployment/bootstrap-objects.json <<'OBJECTS'
[{"bucket": "fyp-p82-20261005-018da1d6-803656589923", "key": "exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/combined-v3/deployment/0878ad052db96b9c075f527dc53194b0eb013d7b98e47603a74acf36b8ff3aaf-v3-combined-review-candidate.tar.gz", "version_id": "t5hzdXv2hfNhxZwV4P4aJKVut2YbRAlw", "sha256": "0878ad052db96b9c075f527dc53194b0eb013d7b98e47603a74acf36b8ff3aaf", "bytes": 31592559, "label": "package.tar.gz"}, {"bucket": "fyp-p82-20261005-018da1d6-803656589923", "key": "exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/combined-v3/deployment/26ac769250a23684a144c2a11197b42dd62f9fab3d53fbf3dad3a5905a779c37-public-authority.tar.gz", "version_id": "JiNXs2uo4QHwyfAKDH2QYl2bi8s6AEjN", "sha256": "26ac769250a23684a144c2a11197b42dd62f9fab3d53fbf3dad3a5905a779c37", "bytes": 98558, "label": "authority.tar.gz"}]
OBJECTS
cat >/var/lib/p8-combined/deployment/bootstrap-transfer.py <<'TRANSFER'
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
    deployment = Path('/var/lib/p8-combined/deployment')
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
            if sum(m.size for m in members) > 200 * 1024**2:
                raise ValueError('BOOTSTRAP_EXPANSION_LIMIT')
            destination.mkdir(exist_ok=False)
            incoming.extractall(destination, members=members, filter='data')
        with (deployment / (obj['label'] + '.verified.json')).open('x') as out:
            json.dump({'sha256': got, 'object': obj, 'members': len(members),
                       'partial_evidence_preserved': True, 'driver_calls': 0}, out)
    root = Path('/opt/fyp-phase8-combined-v3')
    shutil.copytree(deployment / 'package.tar.gz.extract', root)
    inventory = json.loads((root / 'artifacts/phase-8-runner-amendment/v3/candidate-inventory.json').read_text())
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
python3 /var/lib/p8-combined/deployment/bootstrap-transfer.py
cd /opt/fyp-phase8-combined-v3
docker pull ghcr.io/astral-sh/uv:0.9.24@sha256:816fdce3387ed2142e37d2e56e1b1b97ccc1ea87731ba199dc8a25c04e4997c5
docker create --name fyp-combined-v3-uv-tool ghcr.io/astral-sh/uv:0.9.24@sha256:816fdce3387ed2142e37d2e56e1b1b97ccc1ea87731ba199dc8a25c04e4997c5
docker cp fyp-combined-v3-uv-tool:/uv /usr/local/bin/uv
chmod 755 /usr/local/bin/uv
cat >/var/lib/p8-combined/deployment/python-download-catalog.json <<'CATALOG'
{"cpython-3.12.13-linux-x86_64-gnu": {"name": "cpython", "arch": {"family": "x86_64", "variant": null}, "os": "linux", "libc": "gnu", "major": 3, "minor": 12, "patch": 13, "prerelease": "", "url": "https://github.com/astral-sh/python-build-standalone/releases/download/20260807/cpython-3.12.13%2B20260807-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz", "sha256": "506191be3ee7bd190a8834dcdc1b3bc70aab50608deccc711935aa007239cabd", "variant": null, "build": "20260807"}}
CATALOG
UV_PYTHON_DOWNLOADS_JSON_URL=/var/lib/p8-combined/deployment/python-download-catalog.json uv python install 3.12.13
uv sync --locked --no-install-project --python 3.12.13
uv venv --python 3.12.13 .venv-analysis
uv pip install --python .venv-analysis/bin/python -r research/study/requirements.txt
uv venv --python 3.12.13 .venv-transport
uv pip install --python .venv-transport/bin/python -r artifacts/phase-8-review-freeze/v2/requirements.txt
.venv/bin/python -B -m research.execution_linux_v1.portable
docker pull postgres:16.9@sha256:ddfe3e8713e3ee5b8f286082cb12512488dfbf3f5a1ecb0b74a42e6055af0a5f
docker tag postgres@sha256:ddfe3e8713e3ee5b8f286082cb12512488dfbf3f5a1ecb0b74a42e6055af0a5f postgres:16.9
docker pull redis:7.4.5-alpine@sha256:bb186d083732f669da90be8b0f975a37812b15e913465bb14d845db72a4e3e08
docker tag redis@sha256:bb186d083732f669da90be8b0f975a37812b15e913465bb14d845db72a4e3e08 redis:7.4.5-alpine
docker image inspect postgres:16.9 redis:7.4.5-alpine >/var/lib/p8-combined/deployment/image-identities.json
.venv/bin/python -B - <<'PY'
import hashlib,json,sys
from pathlib import Path
r=Path.cwd(); inv=json.loads((r/'artifacts/phase-8-review-freeze/v2/review-inventory.json').read_text())
for name,digest in inv['files'].items():
    with (r/name).open('rb') as f: got=hashlib.file_digest(f,'sha256').hexdigest()
    if got!=digest: raise ValueError('SOURCE_DRIFT: '+name)
if sys.version_info[:3]!=(3,12,13): raise ValueError('PYTHON_VERSION_DRIFT')
with Path('/var/lib/p8-combined/deployment/dependencies-ready.json').open('x') as f:
    json.dump({'status':'PASS','source_files':len(inv['files']),'python':sys.version,'main_initialized':False},f)
PY
# Main initialization and campaign start are separate readiness-gated SSM actions.
printf '%s\n' DEPENDENCIES_READY_MAIN_NOT_INITIALIZED
