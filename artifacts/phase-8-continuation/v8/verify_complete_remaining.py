"""Finish the one interrupted complete-backup check, without repeating its copier."""
from __future__ import annotations
import json
import subprocess
import time
from pathlib import Path
from prepare import HERE, write
from qualify import IMAGE

def main() -> None:
    previous=json.loads((HERE/'qualification-remaining-result.json').read_text())
    assert previous['status']=='TIMEOUT_STOP_CANDIDATE'
    assert 'test_boundary_05_prelaunch_backup_roundtrip PASSED' in previous['stdout']
    write(HERE/'final-check-plan.json',{'checks':1,'scope':'Only finish complete-backup independent readback and corrupt-metadata rejection from already produced actual backup','max_wall_seconds':240,'copier_repeated':False,'passed_controls_repeated':0,'research_executions':0,'partial_previous_attempt_retained':True})
    inputs=Path('E:/p8v8/closure-remaining-evidence')
    code="""import tarfile,sys,json,shutil
from pathlib import Path
with tarfile.open('/control-source.tar.gz') as source: source.extractall('/tmp/control',filter='data')
sys.path[:0]=['/tmp/control/source','/tmp/control/source/artifacts/phase-8-runner-amendment/v4-complete']
from controls import hash_file,read,write_new,Journal
from storage import ObjectProof,OfflineCloud,verify_continuation_metadata
from postflight import recover
archive=Path('/input/complete.tar.gz');receipt=read(Path('/input/complete-receipt.json'))
assert archive.stat().st_size==receipt['bytes'] and hash_file(archive)==receipt['sha256']
cloud=OfflineCloud(Path('/tmp/cal-v8-complete-store'))
proof=cloud.put(archive,'calibration/v8/complete-'+receipt['sha256'])
cloud.verify(proof)
recovered=recover(proof,Path('/tmp/cal-v8-complete-readback'),local_archive=cloud.root/proof.version_id)/'slot'
verify_continuation_metadata(recovered)
rows=Journal(recovered).rows()
assert len(rows)==1500 and sum(r['state']=='BACKED_UP' for r in rows)==120 and sum(r['state']=='PLANNED' for r in rows)==1380
assert rows[120]['sequence']==121 and rows[120]['arm']=='P1' and rows[120]['execution_id']=='01a11705-11f1-75f4-b64e-8f0a3679518b'
assert read(recovered/'continuation-backup.json')['phase']=='COMPLETE'
original=(recovered/'restart-history/pause.json').read_bytes()
(recovered/'restart-history/pause.json').write_text('{}')
try: verify_continuation_metadata(recovered)
except ValueError as error: assert 'METADATA_DRIFT' in str(error); rejected=str(error)
else: raise AssertionError('CORRUPT_METADATA_ACCEPTED')
write_new(Path('/input/corrupt-test-evidence.json'),{'rejected':rejected,'original_pause_bytes':original.decode(),'corrupt_pause_bytes':'{}','research_execution':False})
(recovered/'restart-history/pause.json').write_bytes(original)
verify_continuation_metadata(recovered)
write_new(Path('/input/complete-roundtrip.json'),{'status':'PASS','phase':'COMPLETE','bytes':receipt['bytes'],'sha256':receipt['sha256'],'BACKED_UP':120,'PLANNED':1380,'driver_calls':0,'copier_repeated':False,'historical_records_not_launch_authority':True,'corrupt_metadata_rejected':rejected,'independent_local_proof':proof.model_dump()})
print('PASS: existing complete backup independently read back; exact 120/1380 and corrupt-metadata rejection.')
"""
    name='p85-v8-one-unfinished-readback-attempt3'
    command=['docker','run','--name',name,'--network','none','--memory','1g','--cpus','1','--mount','type=bind,source=E:/p8v8/control-source-attempt2.tar.gz,target=/control-source.tar.gz,readonly','--mount',f'type=bind,source={inputs},target=/input','-e','PYTHONPATH=/opt/fyp-phase8-linux-v1/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-linux-v1/.venv-transport/lib/python3.12/site-packages','--entrypoint','python',IMAGE,'-B','-c',code]
    started=time.monotonic()
    try:
        done=subprocess.run(command,capture_output=True,text=True,timeout=240)
        result={'status':'PASS' if done.returncode==0 else 'FAIL','exit':done.returncode,'stdout':done.stdout,'stderr':done.stderr}
    except subprocess.TimeoutExpired as error:
        result={'status':'TIMEOUT_STOP_CANDIDATE','stdout':str(error.stdout),'stderr':str(error.stderr)}
        subprocess.run(['docker','stop','--time','5',name],capture_output=True,timeout=15)
    result.update(wall_seconds=time.monotonic()-started,checks=1,command=command,container=name,image=IMAGE,completed_controls_repeated=0,copier_repeated=False,research_executions=0)
    write(HERE/'complete-readback-result.json',result)
    print(json.dumps(result,indent=2))
    if result['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
