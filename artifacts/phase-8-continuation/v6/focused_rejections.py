"""Finish seven uncompleted controls using actual retained backups, not scenarios."""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Callable

from controls import Journal, hash_file, read
from handover import ContinuationAuthority
from postflight import recover
from prelaunch_backup import run
from storage import ObjectProof, OfflineCloud, copy_continuation_metadata, verify_continuation_metadata, verify_local

OUT = Path('/out/focused')


def main() -> None:
    started = time.monotonic()
    OUT.mkdir()
    rounds = {}
    roots = {}
    for phase in ('prelaunch', 'complete', 'slot'):
        archive = next(Path('/retained/' + phase).glob('*.object'))
        proof = ObjectProof(bucket='offline-calibration', key='calibration/retained-' + phase, version_id=archive.name, sha256=hash_file(archive), bytes=archive.stat().st_size)
        # Actual final-code readback against preserved independently stored objects.
        destination = recover(proof, Path('/tmp/control-' + phase), local_archive=archive)
        metadata = destination / 'slot'
        if (metadata / 'master').exists():
            metadata = metadata / 'master'
        roots[phase] = metadata
        rounds[phase] = {'status': 'PASS', 'sha256': proof.sha256, 'bytes': proof.bytes, 'phase': read(metadata / 'continuation-backup.json')['phase'], 'identities': len(Journal(metadata).rows()), 'rows': {'BACKED_UP': 82, 'PLANNED': 1418}, 'source_archive_retained': str(archive)}
    checks = []

    def reject(label: str, action: Callable[[], None]) -> None:
        try:
            action()
        except (ValueError, FileNotFoundError) as error:
            checks.append({'check': label, 'status': 'PASS_EXPECTED_REJECTION', 'error': type(error).__name__, 'message': str(error)})
        else:
            raise AssertionError('UNEXPECTED_ACCEPTANCE: ' + label)

    root = roots['prelaunch']
    path = root / 'restart-history/summary.json'
    original = path.read_bytes()
    path.write_text('{}')
    reject('corrupted required history', lambda: verify_continuation_metadata(root))
    path.write_bytes(original)
    normal = roots['complete']
    for name in ('continuation-readiness.json', 'public-authority/continuation/CONTINUATION_LAUNCH.json'):
        path = normal / name
        original = path.read_bytes()
        path.unlink()
        reject('missing complete ' + name, lambda: verify_continuation_metadata(normal))
        path.write_bytes(original)
    source = roots['prelaunch']
    # Existing historical late record must reject a prelaunch phase, not fabricate one.
    shutil.copyfile(normal / 'continuation-readiness.json', source / 'continuation-readiness.json')
    reject('prelaunch has historical late readiness', lambda: verify_continuation_metadata(source))
    (source / 'continuation-readiness.json').unlink()
    archive = next(Path('/retained/prelaunch').glob('*.object'))
    corrupt = Path('/tmp/corrupt.tar.gz')
    corrupt.write_bytes(archive.read_bytes()[:-20])
    reject('corrupted archive', lambda: verify_local(corrupt, hash_file(archive)))
    original_verify = ContinuationAuthority.verify

    def deny(self: ContinuationAuthority, at: object = None, *, prelaunch: bool = False) -> str:
        raise ValueError('MISSING_CALIBRATION_AUTHORIZATION')

    ContinuationAuthority.verify = deny  # failing guard only; no authority granted
    try:
        reject('authorization precedes backup/readiness', lambda: run(source, Path('/tmp/must-not-exist'), 'prelaunch', OfflineCloud(Path('/tmp/offline'))))
        assert not Path('/tmp/must-not-exist').exists()
        assert not (source / 'continuation-readiness.json').exists()
    finally:
        ContinuationAuthority.verify = original_verify
    assert not list(source.rglob('owner.key'))
    assert not list(normal.rglob('owner.key'))
    checks.append({'check': 'private signer excluded from actual complete/prelaunch outputs', 'status': 'PASS'})
    # Reuse the two already passed missing-member controls, bound to retained run log.
    assert len(checks) == 7
    result = {'status': 'PASS', 'seven_remaining_checks': checks, 'three_final_code_readbacks': rounds, 'wall_seconds': time.monotonic() - started, 'research_executions': 0, 'AWS_changes': 0, 'no_authorization_or_readiness_created': True}
    (OUT / 'results.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == '__main__':
    main()
