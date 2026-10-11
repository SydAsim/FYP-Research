#!/bin/bash
set -eu
ss -ltnp
ss -tan state time-wait | head -30
docker ps -a --format '{{.Names}} {{.Status}}'
python3 - <<'PY'
import json,socket,os
from pathlib import Path
result={}
for p in (16432,16433,19100,19101,19102,19110):
 try:
  with socket.socket() as s:s.bind(('127.0.0.1',p))
  result[p]='AVAILABLE'
 except OSError as e:result[p]=str(e)
root=Path('/var/lib/p8-combined/deployment/cal-v4-combined-v3-host-readiness-01')
print(json.dumps({'ports':result,'diagnostic_files':[str(x.relative_to(root)) for x in root.rglob('*') if x.is_file()]}))
for x in root.rglob('*.log'):
 print(str(x), x.read_text(errors='replace')[-1600:])
PY
