set -euo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 AWS_METADATA_SERVICE_TIMEOUT=3 AWS_METADATA_SERVICE_NUM_ATTEMPTS=3
export PYTHONPATH=/opt/fyp-phase8-continuation-v12:/opt/fyp-phase8-continuation-v12/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v12/.venv-transport/lib/python3.12/site-packages
timeout --signal=TERM --kill-after=5s 180s /opt/fyp-phase8-continuation-v12/.venv/bin/python -B /var/lib/p8-continuation-v12/recovery1315/recover1315.py release
