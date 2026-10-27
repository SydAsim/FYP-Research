set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v11
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v11:/opt/fyp-phase8-continuation-v11/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v11/.venv-transport/lib/python3.12/site-packages
.venv/bin/python -B artifacts/phase-8-runner-amendment/v4-complete/check_policy_boundary_v11.py /opt/fyp-phase8-continuation-v11
timeout --signal=TERM --kill-after=5s 180s .venv/bin/python -B /var/lib/p8-continuation-v11/deployment/host_metadata.py
