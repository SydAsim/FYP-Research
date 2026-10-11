#!/usr/bin/env bash
# Evidence finalization only: no admission, driver replay, source or app change.
set -euo pipefail
umask 077
bucket='@BUCKET@'
control=/srv/fyp-p82-finalize-v1
mkdir "$control"
date -u --iso-8601=seconds >"$control/start.txt"
systemctl is-active fyp-p82-stop.timer >"$control/timer.txt"
python3.12 - <<'PY'
import json,pathlib,subprocess
root=pathlib.Path('/srv/fyp-p82-v2')
assert json.loads((root/'qualification-success.json').read_text())['status']=='PASS_NATIVE_COLLECTOR_V2'
assert json.loads((root/'parallel-v2/success.json').read_text())['status']=='PASS_TWO_OBSERVED_RECIPES_ONLY'
for path in (root/'parallel-v2/commands').glob('*.json'):
    record=json.loads(path.read_text())
    # No attempt is removed if a command failed; retain its raw record.
    assert 'exit' in record
running=subprocess.run(['docker','ps','--format','{{.Names}}'],capture_output=True,text=True,check=True)
assert not any('-lane-' in n and n.startswith('p82-par-v2-') for n in running.stdout.splitlines())
PY
aws s3api get-object --bucket "$bucket" --key source/linux-source.tar.gz \
  --version-id '@SOURCE_VERSION@' --region ap-southeast-2 \
  "$control/preserved-linux-source.tar.gz" >"$control/source-download.json"
echo "2cbc081470257e3fa7c9c9c25ec749af1024b2d29496f99fbaf6511d1e4a1fe5  $control/preserved-linux-source.tar.gz" | sha256sum -c - >"$control/source-hash-verification.txt"
journalctl -u fyp-p82-qualification-v2.service -u fyp-p82-finish-v2.service --no-pager >"$control/journal.txt"
systemctl show fyp-p82-qualification-v2.service fyp-p82-finish-v2.service >"$control/unit-status.txt"
cp /opt/fyp-phase82-qualification/finalize-v1.sh "$control/finalizer-source.sh"
cd /opt/fyp-phase8-linux-v1
python3.12 - <<'PY'
import hashlib,json,pathlib
root=pathlib.Path.cwd();seal=json.loads((root/'linux-package-seal.json').read_text())
for name,expected in seal['hashes'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,name
slots=json.loads((root/'artifacts/phase-8-study-design/v4/main-slots.json').read_text())
assert len(slots)==1500 and all(s['status']=='NOT_STARTED' and not s['execution_id'] for s in slots)
pathlib.Path('/srv/fyp-p82-finalize-v1/guards.json').write_text(json.dumps({'capsule_files_verified':len(seal['hashes']),'main_slots_not_started':1500,'main_started':False}))
PY
archive="$control/evidence.tar.gz"
tar -czf "$archive" -C /srv fyp-p82 fyp-p82-backup fyp-p82-control \
  fyp-p82-v2 fyp-p82-backup-v2 fyp-p82-v2-control \
  fyp-p82-v3-integrity fyp-p82-backup-v3-integrity \
  fyp-p82-v3.1-integrity fyp-p82-backup-v3.1-integrity \
  -C "$control" start.txt timer.txt source-download.json source-hash-verification.txt \
  journal.txt unit-status.txt guards.json finalizer-source.sh
sha=$(sha256sum "$archive" | cut -d' ' -f1)
key="exports/phase82-final-evidence-$sha.tar.gz"
set +e
aws s3api put-object --bucket "$bucket" --key "$key" --body "$archive" \
  --checksum-algorithm SHA256 --metadata "sha256=$sha" --region ap-southeast-2 \
  >"$control/upload-response.json" 2>"$control/upload-error.txt"
status=$?
set -e
aws s3api head-object --bucket "$bucket" --key "$key" --checksum-mode ENABLED \
  --region ap-southeast-2 >"$control/head.json"
python3.12 - "$control" "$sha" "$key" "$status" <<'PY'
import base64,json,pathlib,sys
root=pathlib.Path(sys.argv[1]);head=json.loads((root/'head.json').read_text())
assert base64.b64decode(head['ChecksumSHA256']).hex()==sys.argv[2]==head['Metadata']['sha256']
assert head['ContentLength']==(root/'evidence.tar.gz').stat().st_size
(root/'receipt.json').write_text(json.dumps({'key':sys.argv[3],'sha256':sys.argv[2],'bytes':head['ContentLength'],'version_id':head['VersionId'],'upload_exit':int(sys.argv[4]),'main_started':False,'action':'verified evidence then stop, retain disk pending cleanup choice'}))
PY
aws s3api put-object --bucket "$bucket" --key "exports/phase82-final-receipt-$sha.json" \
  --body "$control/receipt.json" --region ap-southeast-2 >"$control/receipt-upload.json"
date -u --iso-8601=seconds >"$control/shutdown-request.txt"
/usr/sbin/shutdown -h now
