"""One fixed seven-check completion on retained outputs, capped at 180 seconds."""
from __future__ import annotations

import json
import subprocess
import tarfile
import time
from pathlib import Path

from prepare_candidate import HERE, PREFIX, SOURCE

IMAGE = 'sha256:5faee27d3793882b26aa166de48fc26d7939710ac9435b0fe7f988c8765497d8'
NAME = 'p85-v6-remaining-controls'


def main() -> None:
    output = HERE / 'remaining'
    output.mkdir()
    plan = {'declared_before_execution': True, 'remaining_checks': 7, 'reused_passed_controls': 5, 'maximum_test_seconds': 180, 'maximum_setup_seconds': 180, 'new_research_executions': 0, 'no_full_backup_regeneration': True, 'reason': 'Both full-suite attempts hit the 300s cap while redundantly rebuilding verified backups. Retain both; finish seven rejection controls on independently stored output copies. Final storage variable rename is typing only, and its verifier is rerun against all three actual archives.'}
    (HERE / 'qualification-plan-supplement.json').write_text(json.dumps(plan, indent=2))
    retained = Path('E:/p8v6/retained-controls')
    for phase, folder in [('prelaunch', 'test_prelaunch_roundtrip_witho0'), ('complete', 'test_complete_master_roundtrip0'), ('slot', 'test_complete_per_slot_roundtr0')]:
        target = retained / phase
        target.mkdir(parents=True, exist_ok=False)
        args = ['docker', 'cp', 'p85-v6-metadata-attempt2:/tmp/cal-v6/' + folder + '/proof/offline-versioned-copy/.', str(target)]
        reply = subprocess.run(args, capture_output=True, text=True, timeout=60)
        (output / (phase + '-preservation.json')).write_text(json.dumps({'exit': reply.returncode, 'stdout': reply.stdout, 'stderr': reply.stderr}))
        reply.check_returncode()
    archive = output / 'source.tar.gz'
    with tarfile.open(archive, 'x:gz') as outgoing:
        for path in sorted(SOURCE.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                outgoing.add(path, arcname=path.relative_to(SOURCE).as_posix(), recursive=False)
    command = (
        'set -eu; mkdir /tmp/candidate; tar -xzf /tmp/source.tar.gz -C /tmp/candidate; cd /tmp/candidate; '
        'export PYTHONDONTWRITEBYTECODE=1 AWS_EC2_METADATA_DISABLED=true PYTHONPATH=/tmp/candidate:/tmp/candidate/' + PREFIX + ':'
        '/opt/fyp-phase8-linux-v1/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-linux-v1/.venv-transport/lib/python3.12/site-packages; '
        'python -m research.execution_linux_v1.portable; timeout --signal=TERM --kill-after=5s 180s python /out/focused_rejections.py'
    )
    args = ['docker', 'create', '--pull=never', '--name', NAME, '--network', 'none', '--memory', '2g', '--cpus', '1', '-v', str(HERE.resolve()) + ':/out', '-v', str(retained) + ':/retained:ro', IMAGE, 'sh', '-c', command]
    (output / 'command.json').write_text(json.dumps(args))
    started = time.monotonic()
    for label, args, limit in [('create', args, 30), ('transfer', ['docker', 'cp', str(archive.resolve()), NAME + ':/tmp/source.tar.gz'], 60), ('run', ['docker', 'start', '-a', NAME], 360)]:
        reply = subprocess.run(args, capture_output=True, text=True, timeout=limit)
        (output / (label + '.json')).write_text(json.dumps({'exit': reply.returncode, 'stdout': reply.stdout, 'stderr': reply.stderr}))
        reply.check_returncode()
    (output / 'qualification.json').write_text(json.dumps({'status': 'PASS', 'wall_seconds': time.monotonic() - started, 'image': IMAGE}))


if __name__ == '__main__':
    main()
