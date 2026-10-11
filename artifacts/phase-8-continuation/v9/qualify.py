from __future__ import annotations
import json
import subprocess
import time
from pathlib import Path
from prepare import HERE,SOURCE,PREFIX,digest,write

def main():
    output=Path('E:/p8v9/qualification-attempt1');output.mkdir(exist_ok=False)
    image='sha256:5faee27d3793882b26aa166de48fc26d7939710ac9435b0fe7f988c8765497d8'
    name='p85-v9-storage-controls-attempt1'
    test=HERE/'test_storage_v9.py'
    dest=SOURCE/'artifacts/phase-8-continuation/v9';dest.mkdir(parents=True)
    (dest/test.name).write_bytes(test.read_bytes())
    code="import platform,sys;print('PINNED_RUNTIME',platform.platform(),sys.version);import pytest;raise SystemExit(pytest.main(['-vv','-p','no:cacheprovider','--basetemp=/tmp/v9-controls','/source/artifacts/phase-8-continuation/v9/test_storage_v9.py']))"
    command=['docker','run','--name',name,'--network','none','--memory','1g','--cpus','1',
      '--mount',f'type=bind,source={SOURCE},target=/source,readonly',
      '-e','PYTHONPATH=/source:/source/'+PREFIX+':/opt/fyp-phase8-linux-v1/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-linux-v1/.venv-transport/lib/python3.12/site-packages',
      '--entrypoint','python',image,'-B','-c',code]
    write(HERE/'qualification-command.json',{'command':command,'checks':8,'wall_limit_seconds':120,'research_executions':0})
    started=time.monotonic()
    try:
        done=subprocess.run(command,capture_output=True,text=True,timeout=120)
        result={'status':'PASS' if done.returncode==0 and '8 passed' in done.stdout else 'FAIL',
          'exit':done.returncode,'stdout':done.stdout,'stderr':done.stderr}
    except subprocess.TimeoutExpired as error:
        result={'status':'TIMEOUT_STOP','stdout':str(error.stdout),'stderr':str(error.stderr)}
        subprocess.run(['docker','stop','--time','5',name],capture_output=True,timeout=15)
    result.update(wall_seconds=time.monotonic()-started,image=image,container=name,research_executions=0,
       files={n:digest(SOURCE/PREFIX/n) for n in ('controls.py','operational_limits.py','handover.py','closed_restart.py')},
       test_sha256=digest(test))
    write(HERE/'qualification-result.json',result);print(json.dumps(result,indent=2))
    if result['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
