#!/usr/bin/env bash
# Bounded export on success or stop. Never replay a driver or replace its outcome.
set -euo pipefail
umask 077
control=/srv/fyp-p83-control
while systemctl is-active --quiet fyp-p83-pilot.service || [ "$(systemctl show fyp-p83-pilot.service -p ActiveState --value)" = activating ]; do
  sleep 15
done
# A protocol stop does not shorten any remaining reachable collector windows.
python3.12 - <<'PY'
import datetime,json,os,pathlib,sqlite3,time
root=pathlib.Path('/srv/fyp-p83-v1')
hard=datetime.datetime.fromisoformat(os.environ['P83_HOST_STOP_AT'])
while True:
    cutoffs=[]
    for path in root.glob('blocks/*/*/run/ledger.sqlite3'):
        with sqlite3.connect(f'file:{path}?mode=ro',uri=True) as conn:
            cutoffs.extend(datetime.datetime.fromisoformat(r[0]) for r in conn.execute("SELECT deadline FROM slots WHERE state IN ('RUNNING','CHECKPOINTED') AND deadline IS NOT NULL"))
            for (identity,) in conn.execute("SELECT execution_id FROM slots WHERE state IN ('RUNNING','CHECKPOINTED') AND deadline IS NULL AND execution_id IS NOT NULL"):
                checkpoint=path.parent/'executions'/identity/'checkpoint.json'
                if checkpoint.exists():
                    row=json.loads(checkpoint.read_text())
                    if row.get('started_at'):
                        cutoffs.append(datetime.datetime.fromisoformat(row['started_at'])+datetime.timedelta(seconds=600))
    if not cutoffs:break
    now=datetime.datetime.now(datetime.UTC)
    # Cutoff plus read/export reserve; absolute cost stop still applies.
    until=min(max(cutoffs)+datetime.timedelta(seconds=90),hard-datetime.timedelta(seconds=60))
    if now>=until:break
    time.sleep(min(15,(until-now).total_seconds()))
PY
journalctl -u fyp-p83-pilot.service -u fyp-p83-finish.service --no-pager >"$control/journal.txt"
systemctl show fyp-p83-pilot.service fyp-p83-stop.timer >"$control/unit-status.txt"
mkdir -p /srv/fyp-p83-v1 /srv/fyp-p83-backup-v1
set +e
PYTHONPATH=/opt/fyp-phase83-pilot-v1:/opt/fyp-phase8-linux-v1/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-linux-v1 /opt/fyp-phase8-linux-v1/.venv/bin/python \
 /opt/fyp-phase83-pilot-v1/postprocess.py /srv/fyp-p83-v1 /srv/fyp-p83-backup-v1 \
 /srv/fyp-p83-v1/accounting.json >"$control/accounting.log" 2>&1
analysis_status=$?
set -e
echo "$analysis_status" >"$control/accounting-exit.txt"
archive="$control/evidence.tar.gz"
tar -czf "$archive" -C /srv fyp-p83-v1 fyp-p83-backup-v1 \
 -C "$control" bootstrap.log journal.txt unit-status.txt accounting.log accounting-exit.txt capsule.tar.gz v2.zip v31.zip p83.zip
sha=$(sha256sum "$archive" | cut -d' ' -f1)
key="exports/phase83-evidence-$sha.tar.gz"
# An ambiguous upload is reconciled by HEAD of the same content key, not a new key.
set +e
aws s3api put-object --bucket "$P83_BUCKET" --key "$key" --body "$archive" \
 --checksum-algorithm SHA256 --metadata "sha256=$sha" --region ap-southeast-2 \
 >"$control/upload.json" 2>"$control/upload-error.txt"
status=$?
set -e
aws s3api head-object --bucket "$P83_BUCKET" --key "$key" --checksum-mode ENABLED \
 --region ap-southeast-2 >"$control/head.json"
python3.12 - "$control" "$sha" "$key" "$status" <<'PY'
import base64,json,pathlib,sys
root=pathlib.Path(sys.argv[1]);head=json.loads((root/'head.json').read_text())
assert base64.b64decode(head['ChecksumSHA256']).hex()==sys.argv[2]==head['Metadata']['sha256']
assert head['ContentLength']==(root/'evidence.tar.gz').stat().st_size
(root/'receipt.json').write_text(json.dumps({'key':sys.argv[3],'sha256':sys.argv[2],'bytes':head['ContentLength'],'version_id':head['VersionId'],'upload_exit':int(sys.argv[4]),'main_started':False,'action':'verified export then stop; retain disk until separately verified cleanup'}))
PY
aws s3api put-object --bucket "$P83_BUCKET" --key "exports/phase83-receipt-$sha.json" \
 --body "$control/receipt.json" --region ap-southeast-2 >"$control/receipt-upload.json"
/usr/sbin/shutdown -h now
