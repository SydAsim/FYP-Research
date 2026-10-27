set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
python3 -B - <<'READ_ONLY'
import json
from pathlib import Path
r=Path('/var/lib/p8-continuation-v9/run/slots/1316')
p=r/'executions/01a11705-11f4-7875-b6f4-62729851bd64/checkpoint.json'
d=json.loads(p.read_bytes())
print(json.dumps({'execution':d.get('execution_id'),'status':d.get('status'),'driver_classification':d.get('driver_classification'),'classification_probe_failure':d.get('classification_probe_failure'),'response_guard':d.get('response_guard'),'collector_pause':json.loads((r/'pause.json').read_bytes()) if (r/'pause.json').exists() else None,'original_deadline':d.get('original_deadline'),'driver_finished_at':d.get('driver_finished_at')}))
READ_ONLY