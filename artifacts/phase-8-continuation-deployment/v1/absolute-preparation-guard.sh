set -eu
python3 - <<'PY'
from pathlib import Path
p=Path('/etc/systemd/system/fyp-p85-continuation-preparation-absolute.timer')
with p.open('x') as f:
 f.write("[Unit]\nDescription=Original absolute preparation bound; does not reset campaign clock\n[Timer]\nOnCalendar=2026-10-07 22:26:52 UTC\nAccuracySec=1s\nPersistent=true\nUnit=fyp-p85-continuation-bootstrap-stop.service\n[Install]\nWantedBy=timers.target\n")
PY
systemctl daemon-reload
systemctl enable --now fyp-p85-continuation-preparation-absolute.timer
systemctl is-active fyp-p85-continuation-preparation-absolute.timer fyp-phase8-hardstop.timer fyp-phase8-watchdog.service fyp-p85-continuation-bootstrap-stop.timer
systemctl list-timers fyp-p85-continuation-preparation-absolute.timer fyp-phase8-hardstop.timer fyp-p85-continuation-bootstrap-stop.timer --no-pager

