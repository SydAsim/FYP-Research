"""Read-only checks after the retained first-original stop; never changes its outcome."""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
V2 = ROOT / 'artifacts/phase-8-review-freeze/v2'
sys.path.insert(0, str(V2))
from instrument import evidence_for
from research.study_v4.oracle import revised_evaluate

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            h.update(block)
    return h.hexdigest()

def main() -> None:
    freeze = ROOT/'artifacts/phase-8-freeze/v1'
    expected = json.loads((freeze/'checksums.json').read_text())['files']
    for name, sha in expected.items():
        if digest(freeze/name) != sha:
            raise ValueError('FREEZE_DRIFT:'+name)
    inventory = json.loads((V2/'review-inventory.json').read_text())['files']
    for name, sha in inventory.items():
        if digest(ROOT/name) != sha:
            raise ValueError('SOURCE_DRIFT:'+name)
    history = json.loads((V2/'preserved-before.json').read_text())
    for name, sha in history.items():
        if digest(ROOT/name) != sha:
            raise ValueError('HISTORY_DRIFT:'+name)
    final = json.loads((V2/'final-verification.json').read_text())
    if final['status'] != 'PASS':
        raise ValueError('ACCEPTED_VERIFICATION_NOT_PASS')
    for name, sha in final['verification_artifact_hashes'].items():
        if digest(V2/name) != sha:
            raise ValueError('VERIFICATION_EVIDENCE_DRIFT:'+name)
    archive = V2/'campaign-source.tar.gz'
    if digest(archive) != final['review_candidate']['sha256']:
        raise ValueError('ARCHIVE_DRIFT')
    trace = Path('C:/fyp-p85/stopped-attempt1/slot1/x/slot/executions/01a11705-11f0-79f1-9293-78f7f8207f70/export.json')
    x = json.loads(trace.read_text())
    case, evidence = evidence_for(x)
    accepted = [a.accepted_at for a in evidence.acceptances if a.revision>1 and a.accepted_at]
    grade, row = revised_evaluate(case,evidence,challenge_at=max(accepted) if accepted else None)
    if grade != x['revised_grade'] or row.model_dump(mode='json') != x['analysis_row']:
        raise ValueError('RECOVERED_ORACLE_OR_ANALYSIS_DRIFT')
    delta = (datetime.fromisoformat(x['original_deadline'])-datetime.fromisoformat(x['external_requests'][-1]['issued_at'])).total_seconds()
    if delta != 600 or datetime.fromisoformat(x['polls'][-1]['at']) < datetime.fromisoformat(x['original_deadline']):
        raise ValueError('SHORTENED_OBSERVATION')
    result = {'status':'PASS','at_utc':datetime.now(UTC).isoformat(),'sealed_freeze_files':len(expected),'source_files':len(inventory),'historical_files':len(history),'verification_artifacts':len(final['verification_artifact_hashes']),'accepted_verification':'PASS','archive_sha256':digest(archive),'oracle_grade_replay':'IDENTICAL','analysis_row_replay':'IDENTICAL','observation_seconds':delta,'polls':len(x['polls']),'max_poll_start_gap_seconds':max((datetime.fromisoformat(b['at'])-datetime.fromisoformat(a['at'])).total_seconds() for a,b in zip(x['polls'],x['polls'][1:])),'export_sha256':digest(trace),'export_path':str(trace),'raw_driver_status':x['status'],'analysis_censor_reason':x['analysis_row']['censor_reason'],'outcome_values':x['analysis_row']['values'],'frozen_changes':0,'replays_of_main_driver':0,'campaign_completed':False}
    with (ROOT/'artifacts/phase-8-launch/v1/after-stop-verification.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
    print(json.dumps(result))

if __name__ == '__main__':
    main()
