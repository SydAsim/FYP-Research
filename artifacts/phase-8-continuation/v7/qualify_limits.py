"""One bounded offline attempt for the eight newly proposed operational controls."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGE = 'sha256:5faee27d3793882b26aa166de48fc26d7939710ac9435b0fe7f988c8765497d8'
NAME = 'p85-v7-new-limits-only'
MODULES = Path('E:/p8v7/source/artifacts/phase-8-runner-amendment/v4-complete')


def main() -> None:
    assert json.loads((HERE/'qualification-plan.json').read_text())['new_only_controls'] == 8
    result_path = HERE/'new-controls-result.json'
    assert not result_path.exists(), 'NO_REPEAT_OF_COMPLETED_CONTROLS'
    command = ['docker','run','--name',NAME,'--network','none','--memory','512m','--cpus','1',
               '--mount',f'type=bind,source={MODULES},target=/work,readonly',
               '-e','PYTHONPATH=/work:/opt/fyp-phase8-linux-v1/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-linux-v1/.venv-transport/lib/python3.12/site-packages',
               '--entrypoint','python',IMAGE,'-B','/work/test_operational_limits.py']
    started = time.monotonic()
    try:
        run = subprocess.run(command,capture_output=True,text=True,timeout=60)
        result = {'status':'PASS' if run.returncode == 0 and 'Ran 8 tests' in run.stderr else 'FAIL',
                  'exit':run.returncode,'stdout':run.stdout,'stderr':run.stderr}
    except subprocess.TimeoutExpired as error:
        result = {'status':'TIMEOUT_STOP_CANDIDATE','stdout':str(error.stdout),'stderr':str(error.stderr)}
        subprocess.run(['docker','stop','--time','5',NAME],capture_output=True,timeout=15)
    result.update(wall_seconds=time.monotonic()-started,image=IMAGE,container=NAME,
                  repeated_v6_tests=0,research_executions=0,network='none',
                  files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in MODULES.glob('*.py')
                         if p.name in ['controls.py','operational_limits.py','staging_retention.py','test_operational_limits.py']})
    result_path.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    if result['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
