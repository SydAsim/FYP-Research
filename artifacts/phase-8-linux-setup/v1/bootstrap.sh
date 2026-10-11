#!/usr/bin/env bash
# Run only inside a verified extracted capsule, on a dedicated Linux research host.
set -euo pipefail
umask 077
test "$(uname -s)" = Linux
test "$(uname -m)" = x86_64
python3.12 - <<'PY'
import hashlib,json,pathlib
root=pathlib.Path.cwd()
manifest=json.loads((root/'linux-package-seal.json').read_text())
assert manifest['version']=='phase8-linux-setup-v1' and not manifest['main_started']
for name, expected in manifest['hashes'].items():
    path=root/name
    assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==expected,name
print('PASS source capsule hashes; no main launch')
PY
python3.12 -m research.execution_linux_v1.portable
docker info >/dev/null
mkdir -p runtime-bin
tool_container="fyp-p8-uv-$(date +%s)-$$"
trap 'docker rm "$tool_container" >/dev/null 2>&1 || true' EXIT
docker create --name "$tool_container" ghcr.io/astral-sh/uv:0.9.24@sha256:816fdce3387ed2142e37d2e56e1b1b97ccc1ea87731ba199dc8a25c04e4997c5 >/dev/null
docker cp "$tool_container:/uv" runtime-bin/uv
chmod 700 runtime-bin/uv
runtime-bin/uv sync --locked --python python3.12 --no-install-project
runtime-bin/uv venv --python python3.12 .venv-analysis
runtime-bin/uv pip install --python .venv-analysis/bin/python -r research/study/requirements.txt
# Pin the same server artifacts used locally, then use --pull=never at execution.
docker pull postgres:16.9@sha256:ddfe3e8713e3ee5b8f286082cb12512488dfbf3f5a1ecb0b74a42e6055af0a5f
docker tag postgres@sha256:ddfe3e8713e3ee5b8f286082cb12512488dfbf3f5a1ecb0b74a42e6055af0a5f postgres:16.9
docker pull redis:7.4.5-alpine@sha256:bb186d083732f669da90be8b0f975a37812b15e913465bb14d845db72a4e3e08
docker tag redis@sha256:bb186d083732f669da90be8b0f975a37812b15e913465bb14d845db72a4e3e08 redis:7.4.5-alpine
docker image inspect postgres:16.9 redis:7.4.5-alpine > runtime-bin/database-image-identities.json
printf '%s\n' 'Dependencies prepared. No calibration slot or main input has been executed.'
