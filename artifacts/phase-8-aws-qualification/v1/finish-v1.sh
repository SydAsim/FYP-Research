#!/usr/bin/env bash
# Run as root on the dedicated, owned calibration host only. No main entrypoint.
set -euo pipefail
umask 077
bucket='@BUCKET@'
base=/opt/fyp-phase8-linux-v1
control=/srv/fyp-p82-control
mkdir -p "$control"
test ! -e "$control/finish-start.txt"
date -u --iso-8601=seconds >"$control/finish-start.txt"
systemctl is-active fyp-p82-stop.timer >"$control/stop-timer.txt"
end=$((SECONDS+2000))
while [[ $(systemctl show fyp-p82-qualification.service -p ActiveState --value) =~ ^(active|activating|reloading)$ ]]; do
  test "$SECONDS" -lt "$end" || { echo NATIVE_SUPERVISOR_TIMEOUT_RETAIN_DISK; exit 1; }
  sleep 5
done
printf '%s\n' PARALLEL_NOT_ADMITTED >"$control/parallel-attempt1.log"
if test -f /srv/fyp-p82/qualification-success.json; then
  # Exactly two separately sealed calibration recipes, conditional on headroom.
  runuser -u fyp -- env P8_DOCKER_DATA_PATH=/srv/fyp-p82 \
    "$base/.venv/bin/python" /opt/fyp-phase82-parallel-v1/parallel.py \
    >"$control/parallel-attempt1.log" 2>&1 || echo PARALLEL_NOT_QUALIFIED_RETAIN_ORIGINAL
fi
# A protocol failure may leave an existing detached collector alive. Do not
# replay it or cut its window short. Wait for its owned identity or lane to exit.
cd "$base"
python3.12 - <<'PY'
import json,pathlib,subprocess,time
from research.execution_linux_v1.platform import process_identity
until=time.monotonic()+850
while True:
    active=False
    for path in pathlib.Path('/srv/fyp-p82/native-original').glob('executions/*/linux-collector-owner.json'):
        owner=json.loads(path.read_text())
        active |= process_identity(owner['pid'])==owner['identity']
    result=subprocess.run(['docker','ps','--format','{{.Names}}'],capture_output=True,text=True,check=True)
    active |= any('-lane-' in name and name.startswith('p82-par-v1-') for name in result.stdout.splitlines())
    if not active:break
    if time.monotonic()>until:raise TimeoutError('LIVE_COLLECTOR_NOT_FINISHED: retain disk; four-hour stop remains active')
    time.sleep(5)
PY
journalctl -u fyp-p82-qualification.service --no-pager >"$control/native-journal.txt"
cp /var/log/cloud-init-output.log "$control/cloud-init-output.log"
uname -a >"$control/host.txt"
python3.12 --version >>"$control/host.txt"
docker --version >>"$control/host.txt"
df -B1 >>"$control/host.txt"
free -b >>"$control/host.txt"
systemctl list-timers --all --no-pager >>"$control/host.txt"
docker ps -a --no-trunc >"$control/docker-containers.txt"
docker image inspect postgres:16.9 redis:7.4.5-alpine >"$control/database-images.json"
sha256sum /tmp/linux-source.tar.gz /tmp/qualification.zip /tmp/parallel-v1.zip >"$control/source-download-hashes.txt"
python3.12 - <<'PY'
import hashlib,json,pathlib
root=pathlib.Path.cwd()
seal=json.loads((root/'linux-package-seal.json').read_text())
drift=[]
for name,expected in seal['hashes'].items():
    if not (root/name).is_file() or hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:drift.append(name)
slots=json.loads((root/'artifacts/phase-8-study-design/v4/main-slots.json').read_text())
not_started=sum(s['status']=='NOT_STARTED' and not s['execution_id'] for s in slots)
pathlib.Path('/srv/fyp-p82-control/final-guards.json').write_text(json.dumps({'capsule_files_checked':len(seal['hashes']),'source_drift':drift,'main_slots_not_started':not_started,'main_started':not_started!=1500,'status':'PASS' if not drift and not_started==1500 else 'FAIL_RETAIN_EVIDENCE'}))
PY
# Existing per-slot backups include PostgreSQL dumps, ledger snapshots and
# content-addressed compressed objects. Keep unsuccessful originals too.
archive="$control/evidence.tar.gz"
tar -czf "$archive" -C /srv fyp-p82 fyp-p82-backup \
  -C /srv/fyp-p82-control native-journal.txt cloud-init-output.log host.txt \
  docker-containers.txt database-images.json source-download-hashes.txt final-guards.json \
  finish-start.txt stop-timer.txt parallel-attempt1.log
sha=$(sha256sum "$archive" | cut -d' ' -f1)
key="exports/phase82-evidence-$sha.tar.gz"
printf '%s\n' "$sha" >"$control/evidence.sha256"
printf '%s\n' "$key" >"$control/export-key.txt"
set +e
aws s3api put-object --bucket "$bucket" --key "$key" --body "$archive" \
  --checksum-algorithm SHA256 --metadata "sha256=$sha" --region ap-southeast-2 \
  >"$control/upload-response.json" 2>"$control/upload-error.txt"
upload_exit=$?
set -e
# Reconcile even a nonzero/ambiguous upload; never silently overwrite/retry.
aws s3api head-object --bucket "$bucket" --key "$key" --checksum-mode ENABLED \
  --region ap-southeast-2 >"$control/upload-head.json"
python3.12 - "$control" "$sha" "$upload_exit" <<'PY'
import base64,hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1]); sha=sys.argv[2]
head=json.loads((root/'upload-head.json').read_text())
actual=base64.b64decode(head['ChecksumSHA256']).hex()
assert actual==sha==head['Metadata']['sha256']
assert head['ContentLength']==(root/'evidence.tar.gz').stat().st_size
(root/'export-verified.json').write_text(json.dumps({'sha256':sha,'version_id':head['VersionId'],'bytes':head['ContentLength'],'upload_exit':int(sys.argv[3]),'main_started':False,'instance_shutdown':'NEXT_LOCAL_ACTION'}))
PY
# A receipt has its own unique key. Disk remains available pending cleanup choice.
aws s3api put-object --bucket "$bucket" --key "exports/phase82-receipt-$sha.json" \
  --body "$control/export-verified.json" --region ap-southeast-2 >"$control/receipt-upload.json"
date -u --iso-8601=seconds >"$control/shutdown-request.txt"
/usr/sbin/shutdown -h now
