set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
/opt/fyp-phase8-combined-v4/.venv/bin/python -B - <<'READ_ONLY'
import json,hashlib,sys,importlib.metadata
from pathlib import Path
import boto3,botocore
baseline=json.loads(Path('/var/lib/p8-combined-v4/deployment/host-health-readiness.json').read_text())
p=Path(sys.executable).resolve()
result={'kind':'READ_ONLY_FAILED_GATE_DIAGNOSIS','python':sys.version,'interpreter':sys.executable,
    'resolved_interpreter':str(p),'actual_binary_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
    'qualified_host_python':baseline.get('python'),'qualified_host_binary_sha256':baseline.get('python_binary_sha256'),
    'baseline_keys':list(baseline),'boto3':boto3.__version__,'botocore':botocore.__version__,
    'v10_source_exists':Path('/opt/fyp-phase8-continuation-v10').exists(),
    'new_source_archive_exists':Path('/var/lib/p8-continuation-v10/deployment/package.tar.gz').exists(),
    'original_pause':json.loads(Path('/var/lib/p8-continuation-v9/run/pause.json').read_text())}
print(json.dumps(result))
READ_ONLY
