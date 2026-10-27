set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v12
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v12:/opt/fyp-phase8-continuation-v12/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v12/.venv-transport/lib/python3.12/site-packages
timeout --signal=TERM --kill-after=5s 480s .venv/bin/python -B /var/lib/p8-continuation-v12/deployment/host_deployment.py live
