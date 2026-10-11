"""Record explicit human acceptance; freeze exact bytes without any AWS operation."""
from __future__ import annotations

import hashlib
import hmac
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CANDIDATE = REPO / 'artifacts/phase-8-continuation/v1'
sys.path.insert(0, str(CANDIDATE))
from controls import Authority, Policy, canonical, hash_file, read, write_new
from handover import FIRST_HASH, PARENT_FREEZE, verify_chain
from verify_package import verify


def main() -> None:
    checked = verify()
    final = read(CANDIDATE / 'final-verification.json')
    inventory = read(CANDIDATE / 'candidate-inventory.json')
    package = 'c308222096cf3c9026aa275e73fd7d75bce386e641824330f385dab02d4b609f'
    if final['status'] != 'PASS' or inventory['package_hash'] != package:
        raise ValueError('ACCEPTED_PACKAGE_OR_PASS_MISMATCH')
    old = Path.home() / '.fyp-research/phase8-owner/phase84-final-v2'
    parent = REPO / 'artifacts/phase-8-review-freeze/v2'
    policy = Policy.model_validate(read(old / 'launch-policy.json'))
    Authority(REPO, parent / 'review-inventory.json', policy,
              hash_file(parent / 'schedule.json'), old / 'receipts', old / 'owner.key').verify()
    if hash_file(old / 'receipts/FREEZE.json') != PARENT_FREEZE:
        raise ValueError('ORIGINAL_PARENT_FREEZE_DRIFT')
    frozen = REPO / 'artifacts/phase-8-continuation-freeze/v1'
    if sys.platform == 'win32':
        frozen = Path('\\\\?\\' + str(frozen.resolve()))
    receipts = Path.home() / '.fyp-research/phase8-owner/phase85-continuation-v1/receipts'
    frozen.mkdir(parents=True, exist_ok=False)
    receipts.mkdir(parents=True, exist_ok=False)
    at = datetime.now(timezone.utc).isoformat()
    statement = {
        'kind': 'EXPLICIT_HUMAN_ACCEPTANCE', 'at_utc': at, 'package_hash': package,
        'authority': 'User instruction in this conversation on 8 October 2026 Asia/Karachi',
        'accepted': ['narrow refusal amendment', 'first-original timing sidecar',
                     'documented heading discrepancy', 'fresh-host metadata handover',
                     'US$1.25 reserve within unchanged US$55 admission guard and US$65 total policy'],
        'first_export_sha256': FIRST_HASH, 'parent_freeze_sha256': PARENT_FREEZE,
        'original_policy_sha256': hashlib.sha256(canonical(policy.model_dump(mode='json'))).hexdigest(),
        'acceptance_is_not_actual_launch': True,
    }
    write_new(frozen / 'acceptance-statement.json', statement)
    write_new(frozen / 'pre-freeze-verification.json', checked)
    # Separate snapshots, never overwrite accepted candidates or historical receipts.
    for name in ('candidate-inventory.json', 'bundle-receipt.json', 'final-verification.json',
                 'continuation-delta.tar.gz', 'REVIEW.md', 'READINESS.md'):
        shutil.copyfile(CANDIDATE / name, frozen / name)
    files = {}
    for name, expected in inventory['files'].items():
        dst = frozen / 'source' / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / name, dst)
        if hash_file(dst) != expected:
            raise ValueError('FREEZE_COPY_DRIFT: ' + name)
        files[name] = expected
    key = (old / 'owner.key').read_bytes()
    predecessor = hashlib.sha256(canonical(read(old / 'receipts/LAUNCH.json'))).hexdigest()
    identities = hash_file(CANDIDATE / 'saved-identities.json')
    for kind in ('CONTINUATION_ACCEPTED', 'CONTINUATION_FREEZE'):
        body = dict(kind=kind, package_hash=package, predecessor_hash=predecessor,
                    policy_sha256=statement['original_policy_sha256'], identities_sha256=identities,
                    parent_freeze_sha256=PARENT_FREEZE, first_export_sha256=FIRST_HASH,
                    expires_at=policy.stop_at.isoformat(),
                    signer='Explicit human instruction recorded by local FYP operator',
                    readiness_sha256=None, instance_id=None)
        receipt = {**body, 'signature': hmac.new(key, canonical(body), 'sha256').hexdigest()}
        write_new(receipts / (kind + '.json'), receipt)
        shutil.copyfile(receipts / (kind + '.json'), frozen / (kind + '.json'))
        predecessor = hashlib.sha256(canonical(receipt)).hexdigest()
    verify_chain(receipts, key, package, policy, identities,
                 hashlib.sha256(canonical(read(old / 'receipts/LAUNCH.json'))).hexdigest(),
                 datetime.now(timezone.utc), prelaunch=True)
    manifest = {
        'kind': 'IMMUTABLE_CONTINUATION_FREEZE', 'version': 'phase85-continuation-v1',
        'created_at_utc': at, 'package_hash': package,
        'parent_package_hash': inventory['parent_package_hash'],
        'parent_freeze_sha256': PARENT_FREEZE,
        'parent_archive_sha256': inventory['parent_archive_sha256'],
        'files': {p.relative_to(frozen).as_posix(): hash_file(p)
                  for p in frozen.rglob('*') if p.is_file()},
        'source_members': len(files), 'accepted': True, 'frozen': True,
        'actual_host_bound': False, 'main_continuation_started': False,
        'private_key_included': False,
    }
    write_new(frozen / 'freeze-manifest.json', manifest)
    write_new(frozen / 'freeze-attestation.json', {
        'kind': 'LOCAL_OPERATOR_HMAC_FREEZE_ATTESTATION',
        'manifest_sha256': hash_file(frozen / 'freeze-manifest.json'),
        'signature': hmac.new(key, canonical(manifest), 'sha256').hexdigest(),
        'human_identity_signature_claimed': False,
    })
    for name, expected in manifest['files'].items():
        if hash_file(frozen / name) != expected:
            raise ValueError('FROZEN_MEMBER_DRIFT')
    write_new(frozen / 'freeze-verification.json', {
        'status': 'PASS', 'at_utc': datetime.now(timezone.utc).isoformat(),
        'package_hash': package, 'parent_chain': 'PASS', 'continuation_chain': 'PASS',
        'freeze_manifest_sha256': hash_file(frozen / 'freeze-manifest.json'),
        'freeze_attestation_sha256': hash_file(frozen / 'freeze-attestation.json'),
        'verified_members': len(manifest['files']),
        'historical_preservation': checked, 'main_continuation_started': False,
    })
    for p in frozen.rglob('*'):
        if p.is_file(): p.chmod(0o444)
    print(json.dumps({'status': 'PASS', 'freeze': str(frozen),
                      'package_hash': package, 'frozen_files': len(manifest['files']),
                      'main_started': False}, indent=2))


if __name__ == '__main__':
    main()
