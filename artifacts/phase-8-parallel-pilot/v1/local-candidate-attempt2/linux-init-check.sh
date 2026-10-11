#!/usr/bin/env bash
# Zero admissions, no Docker socket, no AWS access: initializer and integrity checks.
set -euo pipefail
tar -xzf /capsule.tar.gz -C /opt/fyp-phase8-linux-v1
cd /opt/fyp-phase8-linux-v1
export PYTHONPATH=/opt/fyp-phase83-pilot-v1:/opt/fyp-phase82-qualification-v3.1:/opt/fyp-phase82-qualification-v2:/opt/fyp-phase8-linux-v1/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-linux-v1
export P8_VALIDATION_NETWORK=p83-local-zero-admission
export P8_DOCKER_DATA_PATH=/tmp
.venv/bin/python -m pytest /opt/fyp-phase83-pilot-v1/test_plan.py /opt/fyp-phase83-pilot-v1/test_checks.py /opt/fyp-phase83-pilot-v1/test_accounting.py /opt/fyp-phase83-pilot-v1/test_deploy.py /opt/fyp-phase82-qualification-v3.1/test_integrity.py /opt/fyp-phase82-qualification-v2/test_window.py -q -p no:cacheprovider
bash -n /opt/fyp-phase83-pilot-v1/bootstrap.sh
bash -n /opt/fyp-phase83-pilot-v1/finish.sh
export P83_SLOT_ID=serial-01-B3
.venv/bin/python /opt/fyp-phase83-pilot-v1/combined.py init --root /tmp/p83/original --backup /tmp/p83-backup/original
.venv/bin/python /opt/fyp-phase83-pilot-v1/combined.py verify --root /tmp/p83/original
export P83_SLOT_ID=pair-01-B3-05
export P83_REFERENCE_EXECUTION=00000000-0000-4000-8000-000000000001
.venv/bin/python /opt/fyp-phase83-pilot-v1/combined.py init --root /tmp/p83/repeat --backup /tmp/p83-backup/repeat
.venv/bin/python /opt/fyp-phase83-pilot-v1/combined.py verify --root /tmp/p83/repeat
.venv/bin/python - <<'PY'
import json,pathlib,sqlite3
results=[]
for name in ['original','repeat']:
    root=pathlib.Path('/tmp/p83')/name
    with sqlite3.connect(root/'ledger.sqlite3') as conn:
        row=conn.execute('SELECT case_id,arm,state,attempt,label,original_id,execution_id FROM slots').fetchone()
    assert row[2]=='PLANNED' and row[-1] is None
    assert row[0].startswith('cal-v4-linux-v1-p83-v1-')
    results.append({'initializer':name,'row':row,'executing_manifest':json.loads((root/'executing-adapters-seal.json').read_text())})
assert results[0]['row'][4]=='ORIGINAL_PLANNED'
assert results[1]['row'][4]=='PLANNED_SCHEDULE_REPEAT'
print(json.dumps({'combined_initializers':'PASS','business_admissions':0,'main_started':False,'reference_id':'INIT_ONLY_PLACEHOLDER_NOT_EXECUTION','results':results}))
PY
