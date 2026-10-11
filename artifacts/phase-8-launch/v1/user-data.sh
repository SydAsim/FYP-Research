#!/bin/bash
set -euo pipefail
umask 077
install -d -m 700 /var/lib/p8-deployment /var/lib/fyp-owner /var/lib/fyp-owner/receipts
# An absolute stop is armed before dependency installation or main initialization.
cat >/etc/systemd/system/fyp-p85-bootstrap-stop.service <<'UNIT'
[Unit]
Description=Phase 8 absolute deployment stop; retain evidence disk
[Service]
Type=oneshot
ExecStart=/sbin/shutdown -h now
UNIT
cat >/etc/systemd/system/fyp-p85-bootstrap-stop.timer <<'UNIT'
[Unit]
Description=Absolute authorized Phase 8 deadline, including deployment
[Timer]
OnCalendar=2026-10-22 15:24:23 UTC
OnBootSec=360h
Persistent=true
AccuracySec=1s
Unit=fyp-p85-bootstrap-stop.service
[Install]
WantedBy=timers.target
UNIT
systemctl daemon-reload
systemctl enable --now fyp-p85-bootstrap-stop.timer
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y docker.io python3.12 python3.12-venv python3-boto3 curl openssl
systemctl enable --now docker
# A host-only wrapping key protects transfer of the existing owner signing key.
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out /var/lib/fyp-owner/transfer-private.pem
chmod 600 /var/lib/fyp-owner/transfer-private.pem
openssl pkey -in /var/lib/fyp-owner/transfer-private.pem -pubout -out /var/lib/fyp-owner/transfer-public.pem
python3 - <<'PY'
import boto3, hashlib, json, os
from pathlib import Path
s3=boto3.client('s3',region_name='ap-southeast-2')
p=Path('/var/lib/p8-deployment/campaign-source.tar.gz')
reply=s3.get_object(Bucket='fyp-p82-20261005-018da1d6-803656589923',Key='exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/deployment/campaign-source.tar.gz',VersionId='ezrLssdE0rVRj3K.bIqaqHVcjs1aOSp9')
try:
    with p.open('xb') as f:
        for block in reply['Body'].iter_chunks(1024*1024): f.write(block)
        f.flush(); os.fsync(f.fileno())
finally: reply['Body'].close()
with p.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
if digest!='0e841d7dd7ab1329c4e30fa4dc32179b76655b2cf728ec1ad28db714258d7b62': raise ValueError('FROZEN_ARCHIVE_DRIFT')
with Path('/var/lib/p8-deployment/source-download.json').open('x') as f:
    json.dump({'sha256':digest,'version_id':reply['VersionId'],'bytes':p.stat().st_size},f)
PY
install -d -m 700 /opt/fyp-phase8-linux-v1 /var/lib/p8
tar -xzf /var/lib/p8-deployment/campaign-source.tar.gz -C /opt/fyp-phase8-linux-v1
cd /opt/fyp-phase8-linux-v1
docker pull ghcr.io/astral-sh/uv:0.9.24@sha256:816fdce3387ed2142e37d2e56e1b1b97ccc1ea87731ba199dc8a25c04e4997c5
docker create --name fyp-p85-uv-tool ghcr.io/astral-sh/uv:0.9.24@sha256:816fdce3387ed2142e37d2e56e1b1b97ccc1ea87731ba199dc8a25c04e4997c5
docker cp fyp-p85-uv-tool:/uv /usr/local/bin/uv
docker rm fyp-p85-uv-tool
chmod 755 /usr/local/bin/uv
uv python install 3.12.13
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
docker image inspect postgres:16.9 redis:7.4.5-alpine >/var/lib/p8-deployment/image-identities.json
.venv/bin/python -B - <<'PY'
import hashlib,json,sys
from pathlib import Path
r=Path.cwd(); inv=json.loads((r/'artifacts/phase-8-review-freeze/v2/review-inventory.json').read_text())
for name,digest in inv['files'].items():
    with (r/name).open('rb') as f: got=hashlib.file_digest(f,'sha256').hexdigest()
    if got!=digest: raise ValueError('SOURCE_DRIFT: '+name)
if sys.version_info[:3]!=(3,12,13): raise ValueError('PYTHON_VERSION_DRIFT')
with Path('/var/lib/p8-deployment/dependencies-ready.json').open('x') as f:
    json.dump({'status':'PASS','source_files':len(inv['files']),'python':sys.version,'main_initialized':False},f)
PY
# Main initialization and campaign start are separate readiness-gated SSM actions.
printf '%s\n' DEPENDENCIES_READY_MAIN_NOT_INITIALIZED
