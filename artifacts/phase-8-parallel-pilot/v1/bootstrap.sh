#!/usr/bin/env bash
# Dedicated 8.3 host only; placeholders are filled by the guarded local deployer.
set -euo pipefail
umask 077
mkdir -p /srv/fyp-p83-control
cat >/etc/systemd/system/fyp-p83-stop.service <<'EOF'
[Service]
Type=oneshot
ExecStart=/usr/sbin/shutdown -h now
EOF
cat >/etc/systemd/system/fyp-p83-stop.timer <<'EOF'
[Timer]
OnCalendar=@STOP_CALENDAR@
Persistent=true
Unit=fyp-p83-stop.service
[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable --now fyp-p83-stop.timer
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y docker.io python3.12 python3.12-venv curl unzip
systemctl enable --now docker
curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o /srv/fyp-p83-control/awscli.zip
unzip -q /srv/fyp-p83-control/awscli.zip -d /srv/fyp-p83-control/awscli
/srv/fyp-p83-control/awscli/aws/install
useradd --create-home --shell /bin/bash fyp
usermod -aG docker fyp
mkdir -p /srv/fyp-p83-v1 /srv/fyp-p83-backup-v1
chown fyp:fyp /srv/fyp-p83-v1 /srv/fyp-p83-backup-v1
mkdir -p /opt/fyp-phase8-linux-v1 /opt/fyp-phase82-qualification-v2 /opt/fyp-phase82-qualification-v3.1 /opt/fyp-phase83-pilot-v1
fetch() {
  aws s3api get-object --bucket '@BUCKET@' --key "$1" --region ap-southeast-2 "$2" >"$2.response.json"
  echo "$3  $2" | sha256sum -c -
}
fetch source/linux-source.tar.gz /srv/fyp-p83-control/capsule.tar.gz 2cbc081470257e3fa7c9c9c25ec749af1024b2d29496f99fbaf6511d1e4a1fe5
fetch source/qualification-v2.zip /srv/fyp-p83-control/v2.zip '@V2_SHA@'
fetch source/integrity-v3.1.zip /srv/fyp-p83-control/v31.zip '@V31_SHA@'
fetch '@P83_KEY@' /srv/fyp-p83-control/p83.zip '@P83_SHA@'
tar -xzf /srv/fyp-p83-control/capsule.tar.gz -C /opt/fyp-phase8-linux-v1
unzip -q /srv/fyp-p83-control/v2.zip -d /opt/fyp-phase82-qualification-v2
unzip -q /srv/fyp-p83-control/v31.zip -d /opt/fyp-phase82-qualification-v3.1
unzip -q /srv/fyp-p83-control/p83.zip -d /opt/fyp-phase83-pilot-v1
chown -R fyp:fyp /opt/fyp-phase8-linux-v1 /opt/fyp-phase82-qualification-v2 /opt/fyp-phase82-qualification-v3.1 /opt/fyp-phase83-pilot-v1
# Execute an LF copy, not a modification of the sealed source script.
sed 's/\r$//' /opt/fyp-phase8-linux-v1/artifacts/phase-8-linux-setup/v1/bootstrap.sh >/srv/fyp-p83-control/bootstrap-lf.sh
chown fyp:fyp /srv/fyp-p83-control/bootstrap-lf.sh
chmod 700 /srv/fyp-p83-control/bootstrap-lf.sh
# Allow the research user to traverse only this public bootstrap derivative.
chmod 711 /srv/fyp-p83-control
runuser -u fyp -- bash -c 'cd /opt/fyp-phase8-linux-v1; bash /srv/fyp-p83-control/bootstrap-lf.sh' >/srv/fyp-p83-control/bootstrap.log 2>&1
docker pull 'ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55'
cat >/etc/systemd/system/fyp-p83-pilot.service <<'EOF'
[Unit]
After=docker.service network-online.target
[Service]
Type=oneshot
User=fyp
Group=fyp
SupplementaryGroups=docker
WorkingDirectory=/opt/fyp-phase8-linux-v1
Environment=PYTHONUNBUFFERED=1
Environment=P8_DOCKER_DATA_PATH=/var/lib/docker
Environment=P83_HOST_STOP_AT=@STOP_ISO@
Environment=P83_LANE_IMAGE=ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55
ExecStart=/opt/fyp-phase8-linux-v1/.venv/bin/python /opt/fyp-phase83-pilot-v1/pilot.py
TimeoutStartSec=6h
TimeoutStopSec=20min
KillMode=process
Restart=no
EOF
cat >/etc/systemd/system/fyp-p83-finish.service <<'EOF'
[Service]
Type=oneshot
Environment=P83_HOST_STOP_AT=@STOP_ISO@
Environment=P83_BUCKET=@BUCKET@
ExecStart=/usr/bin/bash /opt/fyp-phase83-pilot-v1/finish.sh
TimeoutStartSec=6h
Restart=no
EOF
systemctl daemon-reload
systemctl start --no-block fyp-p83-pilot.service
systemctl start --no-block fyp-p83-finish.service
