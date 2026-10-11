"""Fixed two-attempt, network-disabled pinned-Linux metadata qualification."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tarfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path('E:/p8v6/source')
PREFIX = 'artifacts/phase-8-runner-amendment/v4-complete'
IMAGE = 'sha256:5faee27d3793882b26aa166de48fc26d7939710ac9435b0fe7f988c8765497d8'


def main() -> None:
    attempt = sys.argv[1]
    assert attempt in ('attempt1', 'attempt2')
    output = HERE / attempt
    output.mkdir(exist_ok=False)
    command = (
        'set -eu; mkdir /tmp/candidate; tar -xzf /tmp/source.tar.gz -C /tmp/candidate; cd /tmp/candidate; '
        'export PYTHONDONTWRITEBYTECODE=1 AWS_EC2_METADATA_DISABLED=true '
        'PYTHONPATH=/tmp/candidate:/tmp/candidate/' + PREFIX + ':'
        '/opt/fyp-phase8-linux-v1/.venv-analysis/lib/python3.12/site-packages:'
        '/opt/fyp-phase8-linux-v1/.venv-transport/lib/python3.12/site-packages; '
        'python -m research.execution_linux_v1.portable; '
        "python -c 'import sys,sqlite3,botocore; assert sys.version_info[:3]==(3,12,13); "
        'assert botocore.__version__=="1.43.108"; print(sys.version,sqlite3.sqlite_version,botocore.__version__)\'; '
        'timeout --signal=TERM --kill-after=5s 300s python -m pytest -x -v -o addopts=\'\' '
        + PREFIX + '/test_backup_closure.py --basetemp=/tmp/cal-v6 --junitxml=/out/results.xml; '
        'tar -czf /out/control-metadata.tar.gz -C /tmp cal-v6'
    )
    archive = output / 'source.tar.gz'
    with tarfile.open(archive, 'x:gz') as target:
        for path in sorted(SOURCE.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                target.add(path, arcname=path.relative_to(SOURCE).as_posix(), recursive=False)
    name = 'p85-v6-metadata-' + attempt
    started = time.monotonic()
    try:
        args = ['docker', 'create', '--pull=never', '--name', name, '--network', 'none', '--memory', '2g', '--cpus', '1', '-v', str(output.resolve()) + ':/out', IMAGE, 'sh', '-c', command]
        (output / 'command.json').write_text(json.dumps(args, indent=2))
        for label, args, limit in [
            ('create', args, 30),
            ('transfer', ['docker', 'cp', str(archive.resolve()), name + ':/tmp/source.tar.gz'], 60),
            ('run', ['docker', 'start', '-a', name], 480),
        ]:
            reply = subprocess.run(args, capture_output=True, encoding='utf-8', timeout=limit, env={**os.environ, 'PYTHONUTF8': '1'})
            (output / (label + '.json')).write_text(json.dumps({'exit': reply.returncode, 'stdout': reply.stdout, 'stderr': reply.stderr}))
            if reply.returncode:
                # Preserve partial metadata even on the first failed check.
                subprocess.run(['docker', 'cp', name + ':/tmp/cal-v6', str(output / 'failed-metadata')], capture_output=True, timeout=30)
                raise ValueError('FAILED_CONTROL_' + label)
        record = {'status': 'PASS', 'wall_seconds': time.monotonic() - started, 'image': IMAGE, 'research_executions': 0, 'AWS_changes': 0}
    except (subprocess.TimeoutExpired, ValueError) as error:
        subprocess.run(['docker', 'stop', '-t', '5', name], capture_output=True, timeout=15)
        record = {'status': 'FAIL_RETAINED', 'wall_seconds': time.monotonic() - started, 'error': str(error)}
    (output / 'qualification.json').write_text(json.dumps(record, indent=2))
    print(json.dumps(record))
    if record['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
