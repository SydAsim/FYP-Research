#!/bin/bash
# Proposed deployment artifact. Not executed during package preparation.
set -euo pipefail
umask 077
test "$(id -u)" -eq 0
test "$(date -u +%s)" -lt 1792682663
test ! -e /etc/systemd/system/fyp-p85-continuation-bootstrap-stop.service
test ! -e /etc/systemd/system/fyp-p85-continuation-bootstrap-stop.timer
test ! -e /etc/systemd/system/fyp-p85-continuation-preparation-stop.timer
install -d -m 700 /var/lib/p8-continuation
cat > /etc/systemd/system/fyp-p85-continuation-bootstrap-stop.service <<'UNIT'
[Unit]
Description=Phase 8 original absolute deadline; retain evidence
[Service]
Type=oneshot
ExecStart=/sbin/shutdown -h now
UNIT
cat > /etc/systemd/system/fyp-p85-continuation-bootstrap-stop.timer <<'UNIT'
[Unit]
Description=Original campaign deadline, including paused time
[Timer]
OnCalendar=2026-10-22 15:24:23 UTC
Persistent=true
AccuracySec=1s
Unit=fyp-p85-continuation-bootstrap-stop.service
[Install]
WantedBy=timers.target
UNIT
cat > /etc/systemd/system/fyp-p85-continuation-preparation-stop.timer <<'UNIT'
[Unit]
Description=Bounded fresh-host preparation, two hours maximum
[Timer]
OnActiveSec=2h
AccuracySec=1s
Unit=fyp-p85-continuation-bootstrap-stop.service
[Install]
WantedBy=timers.target
UNIT
systemctl daemon-reload
systemctl enable --now fyp-p85-continuation-bootstrap-stop.timer
systemctl enable --now fyp-p85-continuation-preparation-stop.timer
systemctl is-active fyp-p85-continuation-bootstrap-stop.timer
systemctl is-active fyp-p85-continuation-preparation-stop.timer
# No package installation, provisioning or campaign service start in this script.
