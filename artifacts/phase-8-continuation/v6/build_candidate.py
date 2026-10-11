"""Package exact local-qualified bytes and unchanged evidence; no freeze or cloud writes."""
from __future__ import annotations

import difflib
import hashlib
import json
import shutil
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path

from prepare_candidate import HERE, PARENT, PREFIX, SOURCE, canonical, digest, verify_parent

RUNTIME = SOURCE / PREFIX
PARENT_FREEZE = '95d48df4494ad022808c172238596f7761582781108b3f9f982088f8a50dfe26'


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as output:
        json.dump(value, output, indent=2, default=str)


def main() -> None:
    parent = json.loads((PARENT / PREFIX / 'candidate-inventory.json').read_text())
    expected = {PREFIX + '/' + n for n in ('storage.py', 'postflight.py', 'handover.py', 'closed_restart.py')}
    changed = {n for n, sha in parent['files'].items() if digest(SOURCE / n) != sha}
    assert changed == expected, changed
    write(HERE / 'preservation-after.json', verify_parent())
    tested = ('storage.py', 'postflight.py', 'prelaunch_backup.py', 'test_backup_closure.py', 'handover.py', 'closed_restart.py')
    result = json.loads((HERE / 'remaining/qualification.json').read_text())
    assert result['status'] == 'PASS'
    with tarfile.open(HERE / 'remaining/source.tar.gz') as archive:
        for name in tested:
            member = archive.extractfile(PREFIX + '/' + name)
            assert member is not None
            qualified = member.read()
            if name == 'storage.py':
                import ast
                previous_ast = ast.parse(qualified)
                function = next(n for n in previous_ast.body if isinstance(n, ast.FunctionDef) and n.name == 'copy_continuation_metadata')
                outer = function.body[1]
                assert isinstance(outer, ast.If) and isinstance(outer.body[0], ast.If)
                outer.body[0].test = ast.parse('prelaunch or ((source / "run.json").exists() and "continuation" in read(source / "run.json"))', mode='eval').body
                assert ast.dump(previous_ast, include_attributes=False) == ast.dump(ast.parse((RUNTIME / name).read_text()), include_attributes=False)
                assert json.loads((HERE / 'final-two-check-results.json').read_text())['exit'] == 0
            else:
                assert hashlib.sha256(qualified).hexdigest() == digest(RUNTIME / name), name
    focused = json.loads((HERE / 'focused/results.json').read_text())
    assert focused['status'] == 'PASS' and len(focused['seven_remaining_checks']) == 7
    prior_log = json.loads((HERE / 'attempt2/run.json').read_text())['stdout']
    assert prior_log.count('PASSED [') == 5
    # The final typing fix changes only a local dictionary variable name. Verify
    # strict AST alpha-equivalence against the copier used for actual roundtrips.
    import ast
    with tarfile.open(HERE / 'attempt2/source.tar.gz') as prior:
        stream = prior.extractfile(PREFIX + '/storage.py')
        assert stream is not None
        old = ast.parse(stream.read())
    final = ast.parse((RUNTIME / 'storage.py').read_text())
    function = next(n for n in old.body if isinstance(n, ast.FunctionDef) and n.name == 'verify_local')
    rename = False
    class Rename(ast.NodeTransformer):
        def visit_Name(self, node: ast.Name) -> ast.Name:
            if node.id == 'expected':
                node.id = 'expected_members'
            return node
    for statement in function.body:
        if isinstance(statement, ast.Assign) and isinstance(statement.value, ast.DictComp):
            rename = True
        if rename:
            Rename().visit(statement)
    copier = next(n for n in old.body if isinstance(n, ast.FunctionDef) and n.name == 'copy_continuation_metadata')
    outer = copier.body[1]
    assert isinstance(outer, ast.If) and isinstance(outer.body[0], ast.If)
    outer.body[0].test = ast.parse('prelaunch or ((source / "run.json").exists() and "continuation" in read(source / "run.json"))', mode='eval').body
    assert ast.dump(old, include_attributes=False) == ast.dump(final, include_attributes=False)
    chunks = []
    for path in sorted(RUNTIME.glob('*.py')):
        previous = PARENT / PREFIX / path.name
        if previous.exists() and digest(path) == digest(previous):
            continue
        before = previous.read_text().splitlines(keepends=True) if previous.exists() else []
        chunks.extend(difflib.unified_diff(before, path.read_text().splitlines(keepends=True), fromfile='frozen-v5/' + path.name if previous.exists() else '/dev/null', tofile='candidate-v6/' + path.name))
    (HERE / 'runtime.diff').write_text(''.join(chunks))
    write(HERE / 'qualified-source-closure.json', {'status': 'PASS', 'files': {n: digest(RUNTIME / n) for n in tested}, 'distinct_controls_demonstrated': 14, 'completed_full_suite_controls': 5, 'remaining_focused_controls': 7, 'final_missing_handover_copier_checks': 2, 'focused_seconds': focused['wall_seconds'], 'pinned_image': result['image'], 'final_qualification_archive_sha256': digest(HERE / 'remaining/source.tar.gz'), 'both_timed_attempts_retained': True, 'strict_AST_closure_except_qualified_missing_handover_guard_and_typing_local_rename': 'PASS', 'final_verifier_all_three_actual_archives': 'PASS', 'complete_pytest_suite_status': 'TIMED_OUT_NOT_PASS'})
    # Pin historical package/receipts and authoritative postboot stopped evidence.
    historical = RUNTIME / 'parent-v5-provenance'
    historical.mkdir()
    frozen = HERE.parents[1] / 'phase-8-continuation-freeze/v5'
    for name in ('freeze-manifest.json', 'freeze-attestation.json'):
        shutil.copyfile(frozen / name, historical / name)
    shutil.copyfile(PARENT / PREFIX / 'candidate-inventory.json', historical / 'candidate-inventory.json')
    deployment = HERE.parents[1] / 'phase-8-continuation-deployment/v5'
    for name in ('REPORT.md', 'final-status.json', 'blocked-preservation-proof.json', 'blocked-evidence-readback.json', 'backup-gate-result.json'):
        shutil.copyfile(deployment / name, historical / name)
    shutil.copyfile(Path('E:/p8v5/blocked-20261009/campaign.sqlite3'), historical / 'postboot-stopped-campaign.sqlite3')
    # Local calibration payloads remain independent, referenced by immutable hashes.
    retained = {}
    for attempt in ('attempt1', 'attempt2', 'remaining'):
        folder = HERE / attempt
        for name in ('source.tar.gz', 'control-metadata.tar.gz'):
            path = folder / name
            if path.exists():
                retained[str(path)] = {'sha256': digest(path), 'bytes': path.stat().st_size}
    write(HERE / 'retained-calibration-payloads.json', {'files': retained, 'failed_first_control_container': 'p85-v6-metadata-attempt1', 'partial_first_extraction_retained': str(HERE / 'attempt1/failed-metadata'), 'not_main_evidence': True})
    for phase in ('prelaunch', 'complete', 'slot'):
        archive = next(Path('E:/p8v6/retained-controls', phase).glob('*.object'))
        assert digest(archive) == focused['three_final_code_readbacks'][phase]['sha256']
    for path in sorted(HERE.rglob('*')):
        relative = path.relative_to(HERE)
        if not path.is_file() or '__pycache__' in relative.parts or 'failed-metadata' in relative.parts or path.suffix in ('.gz', '.pyc'):
            continue
        if path.name in ('candidate-inventory.json', 'candidate-package.json', 'final-verification.json'):
            continue
        target = SOURCE / 'artifacts/phase-8-continuation/v6' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    inventory_name = PREFIX + '/candidate-inventory.json'
    files = {p.relative_to(SOURCE).as_posix(): digest(p) for p in sorted(SOURCE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc' and p.relative_to(SOURCE).as_posix() != inventory_name}
    package_hash = hashlib.sha256(canonical(files)).hexdigest()
    inventory = {'kind': 'CONTINUATION_REVIEW_CANDIDATE_NOT_FREEZE', 'version': 'phase85-continuation-v6', 'files': files, 'package_hash': package_hash, 'parent_package_hash': parent['package_hash'], 'parent_freeze_sha256': PARENT_FREEZE, 'accepted': False, 'frozen': False, 'launch_authorized': False, 'closed_originals': 82, 'planned_originals': 1418, 'next_sequence': 83, 'next_execution_id': '01a11705-11f1-792b-ae1e-36bfc6773842'}
    # Copied parent inventory is replaced only in the separate candidate.
    (RUNTIME / 'candidate-inventory.json').unlink()
    write(RUNTIME / 'candidate-inventory.json', inventory)
    write(HERE / 'candidate-inventory.json', inventory)
    archive = HERE / 'v6-complete-continuation-review-candidate.tar.gz'
    with tarfile.open(archive, 'x:gz') as outgoing:
        for name in sorted([*files, inventory_name]):
            outgoing.add(SOURCE / name, arcname=name, recursive=False)
    # Single forward read verifies complete member closure and every hash.
    expected_hashes = {**files, inventory_name: digest(RUNTIME / 'candidate-inventory.json')}
    seen = set()
    with tarfile.open(archive, 'r|gz') as incoming:
        for member in incoming:
            assert member.isfile() and member.name in expected_hashes and member.name not in seen
            assert not member.name.startswith('/') and '..' not in Path(member.name).parts
            stream = incoming.extractfile(member)
            assert stream is not None and hashlib.sha256(stream.read()).hexdigest() == expected_hashes[member.name], member.name
            seen.add(member.name)
    assert seen == expected_hashes.keys()
    assert all(digest(SOURCE / n) == sha for n, sha in files.items())
    package = {k: v for k, v in inventory.items() if k != 'files'}
    package.update(archive_sha256=digest(archive), archive_bytes=archive.stat().st_size, inventory_sha256=digest(RUNTIME / 'candidate-inventory.json'), archive_members=len(expected_hashes), source=str(SOURCE))
    write(HERE / 'candidate-package.json', package)
    write(HERE / 'final-verification.json', {**package, 'status': 'PASS', 'scope': 'LOCAL_METADATA_REVIEW_CANDIDATE_NOT_LIVE_DEPLOYMENT', 'at_utc': datetime.now(UTC).isoformat(), 'distinct_checks_demonstrated': 14, 'focused_seconds': focused['wall_seconds'], 'full_pytest_suite_status': 'TIMED_OUT_NOT_PASS', 'unsuccessful_attempts_retained': ['attempt1 300-second timeout; preservation-copy/stop timeouts', 'attempt2 300-second timeout; preservation-copy/stop timeouts', 'initial mypy variable-shadowing failure corrected by AST-equivalent local rename'], 'parent_source_freeze_and_signature': 'PASS', 'all_1500_identities_and_82_evidence_preserved': 'PASS', 'application_fixtures_oracle_analysis_windows_changes': 0, 'AWS_start_freeze_launch': False, 'feasibility': json.loads((HERE / 'feasibility-final.json').read_text())})
    print(json.dumps(package, indent=2))


if __name__ == '__main__':
    main()
