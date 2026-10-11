from ops import HERE

header='''set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v5
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v5:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
'''
content=header+'''cat >/var/lib/p8-continuation-v5/deployment/preserve_blocked.py <<'PRESERVE'
'''+(HERE/'preserve_blocked.py').read_text()+'''
PRESERVE
timeout --signal=TERM --kill-after=5s 300s .venv/bin/python -B /var/lib/p8-continuation-v5/deployment/preserve_blocked.py
'''
(HERE/'preserve-blocked.sh').write_text(content,encoding='utf-8',newline='\n')
