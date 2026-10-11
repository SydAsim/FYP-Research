#!/usr/bin/env bash
set -euo pipefail
umask 077
# Cost control precedes installation. Guest shutdown stops EC2 and retains its disk.
cat >/etc/systemd/system/fyp-p82-stop.service <<'EOF'
[Unit]
Description=Finite Phase 8.2 four-hour host stop (retain disk)
[Service]
Type=oneshot
ExecStart=/usr/sbin/shutdown -h now
EOF
cat >/etc/systemd/system/fyp-p82-stop.timer <<'EOF'
[Unit]
Description=Bounded Phase 8.2 powered session
[Timer]
OnBootSec=4h
Unit=fyp-p82-stop.service
[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable --now fyp-p82-stop.timer
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y docker.io python3.12 python3.12-venv curl unzip
systemctl enable --now docker
curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o /tmp/awscli.zip
unzip -q /tmp/awscli.zip -d /tmp/fyp-awscli
/tmp/fyp-awscli/aws/install
useradd --create-home --shell /bin/bash fyp
usermod -aG docker fyp
mkdir -p /opt/fyp-phase8-linux-v1 /opt/fyp-phase82-qualification /srv/fyp-p82 /srv/fyp-p82-backup
aws s3 cp s3://@BUCKET@/source/linux-source.tar.gz /tmp/linux-source.tar.gz --region ap-southeast-2
echo '2cbc081470257e3fa7c9c9c25ec749af1024b2d29496f99fbaf6511d1e4a1fe5  /tmp/linux-source.tar.gz' | sha256sum -c -
tar -xzf /tmp/linux-source.tar.gz -C /opt/fyp-phase8-linux-v1
aws s3 cp s3://@BUCKET@/source/qualification.zip /tmp/qualification.zip --region ap-southeast-2
echo '@ADDON_SHA@  /tmp/qualification.zip' | sha256sum -c -
unzip -q /tmp/qualification.zip -d /opt/fyp-phase82-qualification
chown -R fyp:fyp /opt/fyp-phase8-linux-v1 /opt/fyp-phase82-qualification /srv/fyp-p82 /srv/fyp-p82-backup
cd /opt/fyp-phase8-linux-v1
# The preserved Windows capsule may contain CRLF shell lines. Execute an LF
# derivative outside sealed sources; retain original bytes and its hashes.
sed 's/\r$//' artifacts/phase-8-linux-setup/v1/bootstrap.sh >/opt/fyp-phase82-qualification/bootstrap-lf.sh
su -s /bin/bash fyp -c 'cd /opt/fyp-phase8-linux-v1; bash /opt/fyp-phase82-qualification/bootstrap-lf.sh' > /srv/fyp-p82/bootstrap.log 2>&1
cat >/etc/systemd/system/fyp-p82-qualification.service <<'EOF'
[Unit]
Description=Finite Phase 8.2 calibration only, main study disabled
After=docker.service network-online.target
[Service]
Type=oneshot
User=fyp
Group=fyp
SupplementaryGroups=docker
WorkingDirectory=/opt/fyp-phase8-linux-v1
Environment=PYTHONUNBUFFERED=1
Environment=P8_DOCKER_DATA_PATH=/var/lib/docker
ExecStart=/opt/fyp-phase8-linux-v1/.venv/bin/python /opt/fyp-phase82-qualification/qualify.py /srv/fyp-p82/native-original /srv/fyp-p82-backup/native-original
KillMode=process
TimeoutStartSec=40min
Restart=no
StandardOutput=journal
StandardError=journal
EOF
systemctl daemon-reload
# Bootstrap prepares dependencies only. Admission is a separate finite SSM command
# after the preserved source, tests, timer and resource checks are reviewed.
echo 'READY_FOR_BOUNDED_QUALIFICATION_MAIN_BLOCKED' > /srv/fyp-p82/bootstrap-ready.txt
