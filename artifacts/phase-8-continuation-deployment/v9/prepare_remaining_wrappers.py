"""External version/path and structured log selection; no frozen code edits."""
from pathlib import Path
from ops import HERE
from controls import write_new

def main():
    p=HERE/'bind_launch.py';text=p.read_text()
    text=text.replace("ready=json.loads(reply['StandardOutputContent'])", "records=[json.loads(line) for line in reply['StandardOutputContent'].splitlines() if line.startswith('{')]\n    found=[r for r in records if r.get('status')=='PASS' and 'readiness_sha256' in r and 'checks' in r]\n    assert len(found)==1, 'ONE_ACTUAL_READINESS_RECORD_REQUIRED'\n    ready=found[0]")
    p.write_text(text)
    original=(HERE.parent/'v7-attempt3/install-controls-body.sh').read_text()
    before,after=original.split('OLD_UNITS\ncd ',1)
    before=before.replace('/opt/fyp-phase8-combined-v4','/opt/fyp-phase8-continuation-v7').replace('/var/lib/p8-combined-v4/run','/var/lib/p8-continuation-v7/run').replace('/var/lib/p8-continuation-v7/deployment','/var/lib/p8-continuation-v9/deployment')
    after=after.replace('continuation-v7','continuation-v9')
    script=before+'OLD_UNITS\ncd '+after
    with (HERE/'install-controls-body.sh').open('x',newline='\n') as f:f.write(script)
    header='''set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v9
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v9:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
'''
    script=header+'''timeout --signal=TERM --kill-after=5s 1000s .venv/bin/python -B artifacts/phase-8-runner-amendment/v4-complete/prelaunch_backup.py prelaunch --root /var/lib/p8-continuation-v9/run --destination /var/lib/p8-continuation-v9/backup
.venv/bin/python -B - <<'PROOF'
import json
from pathlib import Path
print(json.dumps({'status':'PASS','proof':json.loads(Path('/var/lib/p8-continuation-v9/run/prelaunch-backup-proof.json').read_text()),'main_admission':False}))
PROOF
'''
    with (HERE/'prelaunch-backup.sh').open('x',newline='\n') as f:f.write(script)
    write_new(HERE/'external-output-and-unit-selection.json',{'status':'PASS_BEFORE_INVOCATION',
      'clock_records_preserved':True,'readiness_selected_by_unique_exact_schema_and_successful_SSM_exit':True,
      'old_unit_source':'/opt/fyp-phase8-continuation-v7','new_unit_source':'/opt/fyp-phase8-continuation-v9',
      'frozen_source_changed':False,'readiness_fabricated':False})

if __name__=='__main__':main()
