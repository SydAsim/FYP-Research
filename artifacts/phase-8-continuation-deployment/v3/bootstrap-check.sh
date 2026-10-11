#!/bin/bash
set -eu
systemctl is-active fyp-p85-continuation-bootstrap-stop.timer fyp-p85-continuation-preparation-stop.timer fyp-p85-combined-preparation-absolute.timer
systemctl list-timers fyp-p85-continuation-bootstrap-stop.timer fyp-p85-combined-preparation-absolute.timer --no-pager
python3 - <<'PY'
import json
from pathlib import Path
print(json.dumps({'public_key':Path('/var/lib/fyp-owner/transfer-public.pem').read_text(),'source_ready':Path('/var/lib/p8-combined/deployment/source-ready.json').exists(),'dependencies_ready':Path('/var/lib/p8-combined/deployment/dependencies-ready.json').exists(),'main_started':False}))
PY
