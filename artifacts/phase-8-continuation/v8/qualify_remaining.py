"""Complete only failed/unstarted controls on container-local temporary storage."""
from __future__ import annotations
import json
import subprocess
import tarfile
import time
from pathlib import Path
from prepare import HERE, PREFIX, SOURCE, digest, write
from qualify import IMAGE

def main() -> None:
    original=json.loads((HERE/'qualification-result.json').read_text())
    assert original['status']=='TIMEOUT_STOP_CANDIDATE'
    assert not (HERE/'qualification-remaining-result.json').exists()
    names=['test_clock_01_bracket_order_and_midpoint',*[f'test_boundary_{n:02d}' for n in range(1,7)]]
    write(HERE/'remaining-check-plan.json',{'reason':'One floating-point test assertion; six boundary checks not completed within first attempt Windows mount limit','controls':names,'count':7,'wall_limit_seconds':240,'already_passed_controls_repeated':0,'source_code_changes_since_first_attempt':'Test uses approximate IEEE-754 assertion; runner import noqa only','network':'none','research_executions':0})
    archive=Path('E:/p8v8/control-source-attempt2.tar.gz')
    with tarfile.open(archive,'x:gz') as out:
        for p in sorted(SOURCE.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
                out.add(p,arcname='source/'+p.relative_to(SOURCE).as_posix(),recursive=False)
    output=Path('E:/p8v8/qualification-attempt2');output.mkdir(exist_ok=False)
    name='p85-v8-clock-boundary-remaining-attempt2'
    code="""import tarfile,platform,sys,time
print('PINNED_RUNTIME',platform.platform(),sys.version,flush=True)
with tarfile.open('/control-source.tar.gz') as source: source.extractall('/tmp/control',filter='data')
sys.path[:0]=['/tmp/control/source','/tmp/control/source/artifacts/phase-8-runner-amendment/v4-complete']
import pytest
result=pytest.main(['-vv','-p','no:cacheprovider','--basetemp=/tmp/cal-v8','--junitxml=/evidence/results.xml','-k','test_clock_01 or test_boundary','/tmp/control/source/artifacts/phase-8-runner-amendment/v4-complete/test_clock_continuation_v8.py'])
with tarfile.open('/evidence/retained-temporary-metadata.tar.gz','x:gz') as output: output.add('/tmp/cal-v8',arcname='calibration')
raise SystemExit(result)
"""
    command=['docker','run','--name',name,'--network','none','--memory','1g','--cpus','1','--mount',f'type=bind,source={archive},target=/control-source.tar.gz,readonly','--mount',f'type=bind,source={output},target=/evidence','-e','PYTHONPATH=/opt/fyp-phase8-linux-v1/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-linux-v1/.venv-transport/lib/python3.12/site-packages','--entrypoint','python',IMAGE,'-B','-c',code]
    started=time.monotonic()
    try:
        done=subprocess.run(command,capture_output=True,text=True,timeout=240)
        result={'status':'PASS' if done.returncode==0 and '7 passed' in done.stdout else 'FAIL','exit':done.returncode,'stdout':done.stdout,'stderr':done.stderr}
    except subprocess.TimeoutExpired as error:
        result={'status':'TIMEOUT_STOP_CANDIDATE','stdout':str(error.stdout),'stderr':str(error.stderr)}
        subprocess.run(['docker','stop','--time','5',name],capture_output=True,timeout=15)
    result.update(wall_seconds=time.monotonic()-started,container=name,image=IMAGE,command=command,source_archive_sha256=digest(archive),output=str(output),files={n:digest(SOURCE/PREFIX/n) for n in original['files']},controls=7,completed_controls_repeated=0,research_executions=0)
    write(HERE/'qualification-remaining-result.json',result)
    print(json.dumps(result,indent=2))
    if result['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
