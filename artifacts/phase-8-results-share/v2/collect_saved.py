"""External read-only extraction of existing grades; never imports an oracle/runner."""
import base64
import collections
import gzip
import hashlib
import json
import os
import signal
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path('/var/lib/p8-continuation-v9/run')
SOURCE = Path('/opt/fyp-phase8-continuation-v11')
STAGE = Path('/var/tmp/fyp-phase8-saved-results-20261018-v2')
MAX_FILE = 64 * 1024**2
MAX_TOTAL = 5 * 1024**3
MAX_OUTPUT = 8 * 1024**2
total = 0


def deadline(*_args):
    raise TimeoutError('BOUNDED_READ_ONLY_REVIEW_DEADLINE')


def raw(path):
    global total
    size = path.stat().st_size
    if size > MAX_FILE or total + size > MAX_TOTAL:
        raise ValueError('READ_BUDGET_EXCEEDED')
    total += size
    return path.read_bytes()


def read(path):
    return json.loads(raw(path))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(240)
    os.nice(15)
    sys.path.insert(0, str(SOURCE / 'artifacts/phase-8-runner-amendment/v4-complete'))
    from closed145 import snapshot

    at = datetime.now(UTC).isoformat()
    rows, notices = snapshot(ROOT / 'campaign.sqlite3')
    bindings = read(ROOT / 'bindings.json')
    assert len(rows) == len(bindings) == 1500
    assert len({r['execution_id'] for r in rows}) == 1500
    for i, (row, bound) in enumerate(zip(rows, bindings, strict=True)):
        assert row['sequence'] == i + 1 and row['attempt'] == 1
        assert all(row[k] == bound[k] for k in bound), 'SAVED_IDENTITY_DRIFT'
    provenance = read(ROOT / 'restart-history/export-layout-v1/provenance.json')
    historical = {r['identity']['sequence']: r for r in provenance['records']}
    closed = [r for r in rows if r['state'] == 'BACKED_UP']
    results, failures = [], []
    for row in closed:
        entry = dict(row)
        try:
            receipt_bytes = raw(ROOT / 'backups' / (row['execution_id'] + '.json'))
            assert sha(receipt_bytes) == row['backup_hash'], 'BACKUP_RECEIPT_HASH'
            receipt = json.loads(receipt_bytes)
            assert receipt['execution_id'] == row['execution_id']
            assert receipt['sha256'] == receipt['cloud']['sha256']
            assert receipt['cloud']['version_id'] and receipt['cloud']['bytes'] > 0
            if row['sequence'] <= 145:
                origin = historical[row['sequence']]
                assert origin['receipt_sha256'] == row['backup_hash']
                assert origin['cloud'] == receipt['cloud']
                path = ROOT / origin['target']
                expected = origin['manifest_committed_export_sha256']
                verification = 'EXACT145_RETAINED_MANIFEST_COMMITMENT'
            else:
                folder = ROOT / 'slots' / f"{row['sequence']:04d}"
                path = folder / 'executions' / row['execution_id'] / 'export.json'
                with sqlite3.connect((folder / 'ledger.sqlite3').resolve().as_uri() + '?mode=ro', uri=True) as db:
                    db.execute('BEGIN')
                    expected_row = db.execute('SELECT hash FROM files WHERE path=?', (path.relative_to(folder).as_posix(),)).fetchone()
                    local_slot = db.execute('SELECT export_hash FROM slots WHERE execution_id=?', (row['execution_id'],)).fetchone()
                    assert expected_row and local_slot and expected_row[0] == local_slot[0], 'SLOT_SEAL_BINDING'
                    expected = expected_row[0]
                verification = 'SEALED_EXPORT_HASH_AND_SLOT_LEDGER'
            export_bytes = raw(path)
            assert sha(export_bytes) == expected, 'EXPORT_HASH_DRIFT'
            trace = json.loads(export_bytes)
            assert all(trace[k] == row[k] for k in ('execution_id', 'arm', 'attempt', 'fixture_hash'))
            assert trace['input']['case_id'] == row['case_id']
            grade = trace['revised_grade']
            analysis = trace['analysis_row']
            assert grade['values'] == analysis['values'], 'RECORDED_GRADE_ANALYSIS_DISAGREEMENT'
            classification = trace.get('driver_classification') or {}
            failure = trace.get('failure') or {}
            entry.update(
                available=True, export_sha256=expected,
                export_relative_path=str(path.relative_to(ROOT)), integrity=verification,
                archive_sha256=receipt['sha256'], cloud=receipt['cloud'],
                raw_status=trace['status'], values=grade['values'],
                voice_evidence=grade['observable'].get('voice_evidence'),
                delivery_evidence=grade.get('delivery_evidence'),
                oracle_hash=grade.get('hash'), oracle_version=grade.get('version'),
                stratum=trace['input']['stratum'], generator_family=trace['input']['generator_family'],
                cluster_id=trace['input']['cluster_id'],
                duration_seconds=analysis.get('duration_seconds'),
                event_observed=analysis.get('event_observed'), censor_reason=analysis.get('censor_reason'),
                failure_type=failure.get('type'),
                driver_classification=classification,
                collection_errors=len(trace.get('collection_errors') or []),
                oracle_failure=trace.get('oracle_failure'),
                obligations=collections.Counter(o.get('status', o.get('state', 'UNRECORDED_STATE')) for o in trace.get('snapshot', {}).get('obligations', [])),
            )
        except (OSError, ValueError, KeyError, TypeError, AssertionError, sqlite3.Error) as error:
            entry.update(available=False, verification_error={'type': type(error).__name__, 'detail': str(error)[:300]})
            failures.append({'sequence': row['sequence'], **entry['verification_error']})
        results.append(entry)
    available = [r for r in results if r['available']]
    def pooled(items):
        keys = sorted({k for r in items for k in r['values']})
        return {k: dict(collections.Counter(r['values'].get(k, 'MISSING_RECORDED_ENDPOINT') for r in items)) for k in keys}
    arms_by_case = collections.defaultdict(set)
    available_by_case = collections.defaultdict(set)
    for row in closed:
        arms_by_case[row['case_id']].add(row['arm'])
    for row in available:
        available_by_case[row['case_id']].add(row['arm'])
    service = subprocess.run(['systemctl', 'show', 'fyp-phase8-campaign.service', 'fyp-phase8-watchdog.service', '--property=Id,ActiveState,SubState,MainPID'], check=True, capture_output=True, text=True, timeout=10).stdout
    payload = {
        'kind': 'INTERIM_POOLED_RECORDED_GRADES_NO_REGRADING_OR_INFERENCE',
        'snapshot_at': at, 'finished_at': datetime.now(UTC).isoformat(),
        'run_id': read(ROOT / 'run.json')['policy']['run_id'],
        'counts': dict(collections.Counter(r['state'] for r in rows)),
        'planned_originals': 1500, 'completed_originals': len(closed),
        'unique_completed_inputs': len(arms_by_case),
        'complete_three_arm_sets': sum(v == {'B3', 'P1', 'P2'} for v in arms_by_case.values()),
        'completed_arm_counts': dict(collections.Counter(r['arm'] for r in closed)),
        'available_grades': len(available), 'verification_failures': failures,
        'available_complete_three_arm_sets': sum(v == {'B3', 'P1', 'P2'} for v in available_by_case.values()),
        'unique_inputs_by_stratum': {s: len({r['case_id'] for r in available if r['stratum'] == s}) for s in sorted({r['stratum'] for r in available})},
        'pooled_raw_status': dict(collections.Counter(r['raw_status'] for r in available)),
        'pooled_censor_reasons': dict(collections.Counter(str(r['censor_reason']) for r in available)),
        'pooled_values': pooled(available),
        'pooled_values_by_stratum': {s: pooled([r for r in available if r['stratum'] == s]) for s in sorted({r['stratum'] for r in available})},
        'voice_evidence': dict(collections.Counter(str(r['voice_evidence']) for r in available)),
        'service_state': service, 'pause': read(ROOT / 'pause.json') if (ROOT / 'pause.json').exists() else None,
        'snapshot_rows': rows, 'last_notice': notices[-1] if notices else None,
        'rows': results, 'input_bytes_read': total,
        'limitations': ['Read saved grades only; no oracle executed or historical sidecar applied', 'Sealed export and master-bound receipts checked; no fresh full archive or S3 object readback', 'Unstarted/active slots excluded from interim outcome denominators, retained explicitly in snapshot', 'No arm ranking, inferential tests, resampling, early stopping or schedule change', 'Scripted tone/playback protocol evidence does not demonstrate human understanding or real speech performance'],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
    assert len(encoded) <= MAX_OUTPUT, 'OUTPUT_BOUND'
    packed = gzip.compress(encoded, mtime=0)
    b64 = base64.b64encode(packed)
    chunks = (len(b64) + 17999) // 18000
    assert chunks <= 8, 'TRANSFER_REQUEST_BOUND'
    STAGE.mkdir(mode=0o700, exist_ok=False)
    assert sum(p.stat().st_size for p in STAGE.iterdir()) + len(packed) + len(b64) < MAX_OUTPUT
    (STAGE / 'saved-results.json.gz').write_bytes(packed)
    (STAGE / 'download.base64').write_bytes(b64)
    print(json.dumps({'path': str(STAGE / 'download.base64'), 'gzip_sha256': sha(packed), 'gzip_bytes': len(packed), 'json_sha256': sha(encoded), 'json_bytes': len(encoded), 'base64_bytes': len(b64), 'chunks': chunks, 'snapshot_at': at, 'completed': len(closed), 'available': len(available), 'verification_failures': failures, 'pooled_values': payload['pooled_values']}))


if __name__ == '__main__':
    main()
