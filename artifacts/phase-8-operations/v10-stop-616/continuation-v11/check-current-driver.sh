set -euo pipefail
umask 077
python3 - <<'READ_ONLY'
import json
from pathlib import Path
root=Path('/var/lib/p8-continuation-v9/run/slots/0617')
p=root/'executions/01a11705-11f2-7276-8d5f-0277ced1a5f5/checkpoint.json'
data=json.loads(p.read_text())
proof=data.get('driver_classification')
print(json.dumps({'execution_id':data.get('execution_id'),'driver_finished_at':data.get('driver_finished_at'),'raw_driver_status':data.get('status'),'recognized_refusal':proof.get('classification') if proof else None,'recognizer_version':proof.get('version') if proof else None,'predicate_result':proof.get('predicate_result') if proof else None,'refusal_retried':proof.get('retry_performed') if proof else None,'slot_pause_exists':(root/'pause.json').exists(),'collection_deadline':data.get('original_deadline'),'collection_errors':data.get('collection_errors'),'source_drift':data.get('source_drift')}))
READ_ONLY
