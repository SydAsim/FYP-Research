from pathlib import Path
import json,base64,gzip
H=Path(__file__).resolve().parent
def main():
    read=lambda n:json.loads((H/n).read_text())
    authority={n:base64.b64encode((H/n).read_bytes()).decode() for n in ['CONTINUATION_ACCEPTED.json','CONTINUATION_FREEZE.json','freeze-manifest.json','freeze-attestation.json']}
    value={'package':read('candidate-package.json'),'delta':read('delta-object.json'),'authority':authority,'external':read('independent-guards-verified.json')}
    (H/'external-input.json').write_text(json.dumps(value,indent=2))
    scripts={n:base64.b64encode(gzip.compress((H/n).read_bytes())).decode() for n in ['host_prepare.py','host_metadata.py']}
    raw=base64.b64encode(gzip.compress((H/'external-input.json').read_bytes())).decode()
    setup="set -euo pipefail\numask 077\nexport PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\nexport PYTHONPATH=/opt/fyp-phase8-continuation-v10:/opt/fyp-phase8-continuation-v10/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v10/.venv-transport/lib/python3.12/site-packages\npython3 - <<'FILES'\nimport base64,gzip\nfrom pathlib import Path\np=Path('/var/lib/p8-continuation-v11/deployment');p.mkdir(mode=0o700,parents=True,exist_ok=True)\nfiles="+repr({**scripts,'external-input.json':raw})+"\nfor name,data in files.items():\n    with (p/name).open('xb') as f:f.write(gzip.decompress(base64.b64decode(data)))\nFILES\ntimeout --signal=TERM --kill-after=5s 240s /opt/fyp-phase8-continuation-v10/.venv/bin/python -B /var/lib/p8-continuation-v11/deployment/host_prepare.py\n"
    (H/'install-source.sh').write_text(setup,encoding='utf-8',newline='\n')
    meta="set -euo pipefail\numask 077\ncd /opt/fyp-phase8-continuation-v11\nexport PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\nexport PYTHONPATH=/opt/fyp-phase8-continuation-v11:/opt/fyp-phase8-continuation-v11/.venv-analysis/lib/python3.12/site-packages:/opt/fyp-phase8-continuation-v11/.venv-transport/lib/python3.12/site-packages\n.venv/bin/python -B artifacts/phase-8-runner-amendment/v4-complete/check_policy_boundary_v11.py /opt/fyp-phase8-continuation-v11\ntimeout --signal=TERM --kill-after=5s 180s .venv/bin/python -B /var/lib/p8-continuation-v11/deployment/host_metadata.py\n"
    (H/'bind-metadata.sh').write_text(meta,encoding='utf-8',newline='\n')
if __name__=='__main__':main()
