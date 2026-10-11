"""Render read-only verification, preserving prior transfer records."""
from pathlib import Path
from ops import HERE

def main():
    original=(HERE/'prepare-source.sh').read_text()
    code=original[original.index(".venv/bin/python -B - <<'PY'"):]
    code=code.replace('receipt_dir.mkdir(mode=0o700,exist_ok=False)','assert receipt_dir.is_dir()')
    code=code.replace('shutil.copyfile(p,receipt_dir/p.name);(receipt_dir/p.name).chmod(0o600)','assert hash_file(p)==hash_file(receipt_dir/p.name)')
    code=code.replace("dep/'source-ready.json'","dep/'source-and-authority-ready.json'")
    header='''set -euo pipefail
umask 077
cd /opt/fyp-phase8-continuation-v5
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PYTHONPATH=/opt/fyp-phase8-continuation-v5:/opt/fyp-phase8-combined-v4/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages
'''
    (HERE/'verify-transferred-authority.sh').write_text(header+code,encoding='utf-8',newline='\n')
    content=(HERE/'host_checks.py').read_text()
    script=header+'''cat >/var/lib/p8-continuation-v5/deployment/host_checks.py <<'CHECKS'
'''+content+'''
CHECKS
timeout --signal=TERM --kill-after=5s 600s .venv/bin/python -B /var/lib/p8-continuation-v5/deployment/host_checks.py
'''
    (HERE/'live-checks.sh').write_text(script,encoding='utf-8',newline='\n')

if __name__=='__main__':
    main()
