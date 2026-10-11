from pathlib import Path

here=Path(__file__).resolve().parent
header='''set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v7
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v7:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
'''
with (here/'live-checks-attempt2.sh').open('x',encoding='utf-8',newline='\n') as f:
    f.write(header+"cat >/var/lib/p8-continuation-v7/deployment/host_checks-attempt2.py <<'CHECKS'\n"+(here/'host_checks.py').read_text()+"\nCHECKS\ntimeout --signal=TERM --kill-after=5s 600s .venv/bin/python -B /var/lib/p8-continuation-v7/deployment/host_checks-attempt2.py\n")
with (here/'local-render-command-failure.txt').open('x',encoding='utf-8') as f:
    f.write('Local python -c quoting failed with SyntaxError before rendering. No AWS command or frozen file changed. Rendered with render_live.py instead. Source transfer independently PASS.\n')
