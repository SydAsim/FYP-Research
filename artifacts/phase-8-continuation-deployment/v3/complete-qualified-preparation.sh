#!/bin/bash
set -euo pipefail
umask 077
cd /opt/fyp-phase8-combined-v3
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD:$PWD/.venv-analysis/lib/python3.12/site-packages:$PWD/.venv-transport/lib/python3.12/site-packages"
.venv/bin/python -B - <<'PY'
import hashlib,json,os,tarfile,time
from pathlib import Path
import boto3
from botocore.config import Config
p=Path('/var/lib/p8-combined/deployment/original-bootstrap.tar.gz')
s3=boto3.client('s3',region_name='ap-southeast-2',config=Config(connect_timeout=5,read_timeout=25,retries={'total_max_attempts':2,'mode':'standard'}))
at=time.monotonic()+180
reply=s3.get_object(Bucket='fyp-p82-20261005-018da1d6-803656589923',Key='exports/phase8/p85-01a116f7-3b82-7a79-8653-3aee62dc99e9/deployment/campaign-source.tar.gz',VersionId='ezrLssdE0rVRj3K.bIqaqHVcjs1aOSp9')
try:
 with p.open('xb') as f:
  for chunk in reply['Body'].iter_chunks(1024**2):
   if time.monotonic()>=at:raise TimeoutError('RETAIN_ORIGINAL_METADATA_DOWNLOAD')
   f.write(chunk)
  f.flush();os.fsync(f.fileno())
finally:reply['Body'].close()
if p.stat().st_size!=30075526 or hashlib.sha256(p.read_bytes()).hexdigest()!='0e841d7dd7ab1329c4e30fa4dc32179b76655b2cf728ec1ad28db714258d7b62':raise ValueError('QUALIFIED_ORIGINAL_ARCHIVE_DRIFT')
with tarfile.open(p) as t:
 m=t.getmember('linux-package-seal.json')
 if not m.isfile():raise ValueError('SEAL_NOT_REGULAR_FILE')
 raw=t.extractfile(m).read()
 if hashlib.sha256(raw).hexdigest()!='bfaf6a67ced678b45f5cfd911be8cefafcbf7725d45bbfb10be87ac472d7fb42':raise ValueError('QUALIFIED_SEAL_DRIFT')
 with Path('linux-package-seal.json').open('xb') as f:f.write(raw)
seal=json.loads(raw)
for name,digest in seal['hashes'].items():
 if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest:raise ValueError('ORIGINAL_LINUX_SEAL_SOURCE_DRIFT: '+name)
with Path('/var/lib/p8-combined/deployment/original-metadata-resolution.json').open('x') as f:json.dump({'kind':'QUALIFIED_ORIGINAL_BOOTSTRAP_METADATA_RESTORED','archive_sha256':'0e841d7dd7ab1329c4e30fa4dc32179b76655b2cf728ec1ad28db714258d7b62','seal_sha256':hashlib.sha256(raw).hexdigest(),'frozen_code_changed':False,'driver_calls':0,'prior_failed_preparation_retained':True},f)
PY
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
