#!/bin/bash
set -euo pipefail
umask 077
cd /opt/fyp-phase8-linux-v1
cat >/var/lib/p8-deployment/python-download-catalog.json <<'CATALOG'
{"cpython-3.12.13-linux-x86_64-gnu": {"name": "cpython", "arch": {"family": "x86_64", "variant": null}, "os": "linux", "libc": "gnu", "major": 3, "minor": 12, "patch": 13, "prerelease": "", "url": "https://github.com/astral-sh/python-build-standalone/releases/download/20260807/cpython-3.12.13%2B20260807-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz", "sha256": "506191be3ee7bd190a8834dcdc1b3bc70aab50608deccc711935aa007239cabd", "variant": null, "build": "20260807"}}
CATALOG
UV_PYTHON_DOWNLOADS_JSON_URL=/var/lib/p8-deployment/python-download-catalog.json uv python install 3.12.13
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
