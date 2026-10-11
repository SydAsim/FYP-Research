set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v5
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v5:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
cat >/var/lib/p8-continuation-v5/deployment/backup_gate_control.py <<'CONTROL'
"""Two fast metadata controls; no driver or main execution."""
import json
import shutil
import sys
import time
from pathlib import Path

RUNTIME=Path('/opt/fyp-phase8-continuation-v5/artifacts/phase-8-runner-amendment/v4-complete')
sys.path.insert(0,str(RUNTIME))
from closed_restart import stage
from controls import Journal,hash_file,read,write_new,utc
from storage import final_backup,copy_continuation_metadata

def main():
    out=Path('/var/lib/p8-continuation-v5/deployment')/('cal-backup-gate-'+str(time.time_ns()))
    out.mkdir()
    root=out/'metadata-only';stage(RUNTIME/'closed-82',root)
    shutil.copyfile(RUNTIME/'closed-82/host-clock.json',root/'host-clock.json')
    before=Journal(root).rows()
    backup=out/'failed-prelaunch-backup';backup.mkdir()
    try:
        final_backup(Journal(root),backup)
    except FileNotFoundError as error:
        first={'type':type(error).__name__,'message':str(error),'partial_retained':True}
    else:
        raise AssertionError('EXPECTED_BACKUP_GATE_FAILURE_NOT_REPRODUCED')
    assert 'continuation-readiness.json' in first['message']
    # Separate inert control input supplies the ordinary fields to reveal whether
    # the copier carries the new required 82-original restart records at all.
    fake=out/'calibration-copier-input';fake.mkdir()
    for name in ('handover.json','saved-identities.json','host-clock.json'):
        shutil.copyfile(root/name,fake/name)
    write_new(fake/'continuation-readiness.json',{'kind':'CALIBRATION_ONLY_NOT_AUTHORIZATION'})
    write_new(fake/'restart-boundary.json',read(root/'restart-boundary.json'))
    shutil.copytree(root/'restart-history',fake/'restart-history')
    receipts=out/'inert-test-receipts';receipts.mkdir()
    for name in ('REVIEW_ACCEPTED','FREEZE','LAUNCH','CONTINUATION_ACCEPTED','CONTINUATION_FREEZE','CONTINUATION_LAUNCH'):
        write_new(receipts/(name+'.json'),{'kind':'CALIBRATION_ONLY_NOT_AUTHORIZATION','name':name})
    write_new(fake/'run.json',{'receipts':str(receipts),'continuation':{'receipts':str(receipts)}})
    copied=out/'copied-continuation';copied.mkdir()
    copy_continuation_metadata(fake,copied)
    missing=[name for name in ('restart-boundary.json','restart-history') if not (copied/name).exists()]
    assert missing==['restart-boundary.json','restart-history']
    assert Journal(root).rows()==before
    result={'status':'REPRODUCED_LAUNCH_GATE_DEFECT','at_utc':utc().isoformat(),'calibration_id':out.name,
            'first_prelaunch_failure':first,'missing_required_restart_metadata':missing,'source_storage_sha256':hash_file(RUNTIME/'storage.py'),
            'next_sequence':83,'BACKED_UP':82,'PLANNED':1418,'originals_replayed':0,'research_executions':0,'actual_campaign_modified':False,
            'new_real_readiness_or_launch_receipt':False,'pause_cleared':False}
    write_new(out/'result.json',result);write_new(out.parent/'backup-gate-control-result.json',result)
    print(json.dumps(result))

if __name__=='__main__':
    main()

CONTROL
timeout --signal=TERM --kill-after=5s 120s .venv/bin/python -B /var/lib/p8-continuation-v5/deployment/backup_gate_control.py
