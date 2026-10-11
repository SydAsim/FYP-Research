"""Create a separate candidate from the verified immutable v5 inventory."""
from __future__ import annotations

import hashlib
import hmac
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path('E:/p8v6/source')
PARENT = Path('E:/p8v5/source')
PREFIX = 'artifacts/phase-8-runner-amendment/v4-complete'


def digest(path: Path) -> str:
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), default=str).encode()


def verify_parent() -> dict[str, object]:
    inventory = json.loads((PARENT / PREFIX / 'candidate-inventory.json').read_text())
    assert inventory['package_hash'] == '805d905760ff2565ef4f3813c0062b073d210de4e10b1fee35d3dfd2377c3627'
    assert hashlib.sha256(canonical(inventory['files'])).hexdigest() == inventory['package_hash']
    for name, sha in inventory['files'].items():
        assert digest(PARENT / name) == sha, name
    frozen = Path('\\\\?\\' + str((HERE.parents[1] / 'phase-8-continuation-freeze/v5').resolve()))
    manifest = json.loads((frozen / 'freeze-manifest.json').read_text())
    attestation = json.loads((frozen / 'freeze-attestation.json').read_text())
    sha = digest(frozen / 'freeze-manifest.json')
    assert sha == '95d48df4494ad022808c172238596f7761582781108b3f9f982088f8a50dfe26'
    key = (Path.home() / '.fyp-research/phase8-owner/phase84-final-v2/owner.key').read_bytes()
    assert attestation['manifest_sha256'] == sha
    assert hmac.compare_digest(attestation['signature'], hmac.new(key, canonical(manifest), 'sha256').hexdigest())
    for name, sha in manifest['files'].items():
        assert digest(frozen / name) == sha, name
    return {'status': 'PASS', 'at_utc': datetime.now(UTC).isoformat(), 'source_files': len(inventory['files']), 'frozen_files': len(manifest['files']), 'parent_package_hash': inventory['package_hash'], 'parent_freeze_sha256': digest(frozen / 'freeze-manifest.json')}


if __name__ == '__main__':
    result = verify_parent()
    (HERE / 'preservation-before.json').write_text(json.dumps(result, indent=2))
    SOURCE.mkdir(parents=True, exist_ok=False)
    inventory = json.loads((PARENT / PREFIX / 'candidate-inventory.json').read_text())
    for name in [*inventory['files'], PREFIX + '/candidate-inventory.json']:
        target = SOURCE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PARENT / name, target)
    (HERE / 'qualification-plan.json').write_text(json.dumps({
        'kind': 'LOCAL_METADATA_CONTROLS_ONLY', 'declared_before_execution': True,
        'at_utc': datetime.now(UTC).isoformat(), 'tests': 12,
        'maximum_test_wall_seconds_per_attempt': 300, 'maximum_attempts': 2,
        'maximum_setup_wall_seconds_per_attempt': 180,
        'checks': ['prelaunch final backup + offline versioned upload + actual readback, without readiness/launch', 'complete normal final backup roundtrip', 'complete normal per-slot metadata roundtrip', 'missing restart boundary rejected', 'missing restart history member rejected', 'corrupted restart history rejected', 'missing normal readiness rejected', 'missing normal launch rejected', 'prelaunch rejects late-stage authority artifacts', 'actual archive corruption rejection/partial retention', 'ordering rejects missing authorization before backup or readiness', 'copier cannot introduce signing key'],
        'stop': 'Stop on a failed check; retain it; at most one corrected diagnostic attempt, labelled separately.',
        'research_scenarios': 0, 'live_application_stacks': 0, 'observation_windows': 0,
        'files': {'storage.py': 'Complete required restart/receipt/pause metadata; explicit prelaunch phase', 'postflight.py': 'Use actual continuation readback verifier after extraction', 'prelaunch_backup.py': 'Verified backup before genuine readiness; complete backup before pause release', 'handover.py': 'v6 parent provenance and verified backup prerequisite for release', 'closed_restart.py': 'v6 paths/version only; original 82 boundary unchanged', 'test_backup_closure.py': '12 temporary calibration metadata controls', 'review files': 'Exact diff, measured results, unchanged limits and feasibility'}
    }, indent=2))
    print(json.dumps(result))
