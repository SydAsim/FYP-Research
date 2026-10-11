"""Single bounded pinned-Linux metadata/control qualification; no research execution."""
from __future__ import annotations
import json
import subprocess
import time
from pathlib import Path
from prepare import HERE, PREFIX, SOURCE, digest, write

IMAGE='sha256:5faee27d3793882b26aa166de48fc26d7939710ac9435b0fe7f988c8765497d8'
NAME='p85-v8-clock-boundary-controls-attempt1'

def main() -> None:
    assert (HERE/'PLAN.md').is_file() and (HERE/'boundary-closure.json').is_file()
    assert not (HERE/'qualification-result.json').exists()
    output=Path('E:/p8v8/qualification-attempt1');output.mkdir(exist_ok=False)
    code="import platform,sys; print('PINNED_RUNTIME',platform.platform(),sys.version); import pytest; raise SystemExit(pytest.main(['-vv','-p','no:cacheprovider','--basetemp=/evidence/temporary-metadata','--junitxml=/evidence/results.xml','/source/artifacts/phase-8-runner-amendment/v4-complete/test_clock_continuation_v8.py']))"
    command=['docker','run','--name',NAME,'--network','none','--memory','1g','--cpus','1',
       '--mount',f'type=bind,source={SOURCE},target=/source,readonly',
       '--mount',f'type=bind,source={output},target=/evidence',
       '-e','PYTHONPATH=/source:/source/'+PREFIX+':/opt/fyp-phase8-linux-v1/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-linux-v1/.venv-transport/lib/python3.12/site-packages',
       '--entrypoint','python',IMAGE,'-B','-c',code]
    write(HERE/'qualification-command.json',{'command':command,'checks':18,'wall_limit_seconds':240,'research_executions':0})
    started=time.monotonic()
    try:
        done=subprocess.run(command,capture_output=True,text=True,timeout=240)
        result={'status':'PASS' if done.returncode==0 and '18 passed' in done.stdout else 'FAIL','exit':done.returncode,'stdout':done.stdout,'stderr':done.stderr}
    except subprocess.TimeoutExpired as error:
        result={'status':'TIMEOUT_STOP_CANDIDATE','stdout':str(error.stdout),'stderr':str(error.stderr)}
        subprocess.run(['docker','stop','--time','5',NAME],capture_output=True,timeout=15)
    result.update(wall_seconds=time.monotonic()-started,image=IMAGE,container=NAME,output=str(output),research_executions=0,network='none',files={n:digest(SOURCE/PREFIX/n) for n in ('clock_sampling.py','runner.py','handover.py','closed_restart.py','reuse_prepare.py','test_clock_continuation_v8.py')})
    write(HERE/'qualification-result.json',result)
    print(json.dumps(result,indent=2))
    if result['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
