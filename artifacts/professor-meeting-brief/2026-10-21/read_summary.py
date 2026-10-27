"""Reuse qualified read-only export checks; obtain one bounded pooled summary."""
from pathlib import Path
import hashlib
import importlib.util
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
previous = ROOT / 'artifacts/phase-8-results-share/v3'
spec = importlib.util.spec_from_file_location('preserved_download', previous / 'download.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.HERE = HERE

body = (previous / 'collect_saved.py').read_text(encoding='utf-8')
body = body.replace("driver_classification_kind=classification.get('kind')", "driver_classification_kind=classification.get('classification')")
begin = body.index('    encoded = json.dumps(payload,')
tail = '''    payload['grade_record_commitment_sha256'] = sha(json.dumps(results,sort_keys=True,separators=(',',':')).encode())
    payload['recorded_driver_classifications'] = dict(collections.Counter(str(r.get('driver_classification_kind')) for r in available))
    payload['adverse_record_sequences'] = {k:[r['sequence'] for r in available if r['values'].get(k)=='TRUE'] for k in ['unsupported_exposed_claim','forbidden_effect']}
    payload['collection_error_executions'] = sum(r['collection_errors']>0 for r in available)
    payload['oracle_failure_executions'] = sum(bool(r['oracle_failure']) for r in available)
    payload.pop('rows')
    encoded = json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
    assert len(encoded) <= 20000, 'SUMMARY_OUTPUT_BOUND'
    print(json.dumps({'summary':payload,'summary_sha256':sha(encoded),'canonical_json_bytes':len(encoded)}))

if __name__ == '__main__':
    main()
'''
body = body[:begin] + tail
with (HERE / 'collect-summary.py').open('x', encoding='utf-8', newline='\n') as f:
    f.write(body)
compile(body, 'collect-summary.py', 'exec')
command = "cd /opt/fyp-phase8-continuation-v11\nexport PYTHONDONTWRITEBYTECODE=1\n.venv/bin/python -B - <<'READ_SAVED_POOLED_ONLY'\n" + body + "\nREAD_SAVED_POOLED_ONLY\n"
result = json.loads(module.run('pooled-outcomes', command))
encoded = json.dumps(result['summary'], sort_keys=True, separators=(',', ':')).encode()
assert len(encoded) == result['canonical_json_bytes'] and hashlib.sha256(encoded).hexdigest() == result['summary_sha256']
module.save('pooled-outcomes.json', result['summary'])
module.save('verification.json', {'summary_sha256': result['summary_sha256'], 'summary_bytes': len(encoded), 'download_hash_matches': True, 'source_collector_sha256': hashlib.sha256((previous/'collect_saved.py').read_bytes()).hexdigest(), 'source_download_sha256':hashlib.sha256((previous/'download.py').read_bytes()).hexdigest(), 'regrading':False, 'campaign_mutations':False, 'new_driver_classification_field':'Recorded classification key read correctly in derivative only; no outcome classification recomputed'})
print(json.dumps(result, indent=2))
