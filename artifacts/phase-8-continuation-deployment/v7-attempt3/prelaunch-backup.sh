set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v7
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v7:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
timeout --signal=TERM --kill-after=5s 1000s .venv/bin/python -B artifacts/phase-8-runner-amendment/v4-complete/prelaunch_backup.py prelaunch --root /var/lib/p8-continuation-v7/run --destination /var/lib/p8-continuation-v7/backup
.venv/bin/python -B - <<'PY'
import json
from pathlib import Path
root=Path('/var/lib/p8-continuation-v7/run')
print(json.dumps({'status':'PASS','proof':json.loads((root/'prelaunch-backup-proof.json').read_text()),'main_admission':False}))
PY
