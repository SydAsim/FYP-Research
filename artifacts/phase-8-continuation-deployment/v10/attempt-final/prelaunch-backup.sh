set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v10
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v10:/opt/fyp-phase8-continuation-v10/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v10/.venv-transport/lib/python3.12/site-packages
timeout --signal=TERM --kill-after=5s 1000s .venv/bin/python -B artifacts/phase-8-runner-amendment/v4-complete/prelaunch_backup.py prelaunch --root /var/lib/p8-continuation-v9/run --destination /var/lib/p8-continuation-v9/backup
.venv/bin/python -B - <<'PROOF'
import json
from pathlib import Path
print(json.dumps({'status':'PASS','phase':'prelaunch','proof':json.loads(Path('/var/lib/p8-continuation-v9/run/prelaunch-backup-proof.json').read_text()),'main_admitted':False}))
PROOF
