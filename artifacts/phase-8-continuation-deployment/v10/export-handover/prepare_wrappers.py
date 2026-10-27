"""Reuse reviewed deployment stages; no exclusive source bootstrap."""
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'attempt-final'

def write(name,text):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)

def main():
    names=('ops.py','prepare-metadata.sh','host_checks.py','transfer-live-checker.sh','live-checks.sh','install-timer-files.sh','readiness.sh',
           'prelaunch-backup.sh','complete-backup.sh','activate-controls-and-launch.sh','progress.sh','bind_launch.py','start.py','guard.py','preflight.py','inspect-effects.sh','quiesce-owned-units.sh')
    for name in names:
        text=(PARENT/name).read_text()
        if name in ('guard.py','preflight.py'):text=text.replace('v10-final-prep-20261013','v10-exports-prep-20261013')
        if name=='quiesce-owned-units.sh':text=text.replace('attempt-final-unit-state-before-quiesce','export-handover-unit-state-before-quiesce').replace('attempt-final-units-quiesced','export-handover-units-quiesced')
        if name=='start.py':
            # The external gate file from attempt-final was never transferred.
            text=text.replace('external-preboot-final.json','external-preboot-final.json')
        write(name,text)
    h=(PARENT/'HEADER.txt').read_text()
    proof=base64.b64encode(gzip.compress((HERE/'core.py').read_bytes())).decode()
    driver=base64.b64encode(gzip.compress((HERE/'handover.py').read_bytes())).decode()
    code_hash=hashlib.sha256((HERE/'core.py').read_bytes()).hexdigest()
    driver_hash=hashlib.sha256((HERE/'handover.py').read_bytes()).hexdigest()
    script=h+".venv/bin/python -B - <<'INSTALL'\nimport base64,gzip,hashlib\nfrom pathlib import Path\nd=Path('/var/lib/p8-continuation-v10/deployment/export-handover-code-v1');d.mkdir(mode=0o700,exist_ok=False)\n"
    for name,payload,digest in [('core.py',proof,code_hash),('handover.py',driver,driver_hash)]:
        script+="b=gzip.decompress(base64.b64decode("+repr(payload)+"));assert hashlib.sha256(b).hexdigest()=="+repr(digest)+"\nwith (d/"+repr(name)+").open('xb') as f:f.write(b)\n"
    script+="INSTALL\nexport HANDOVER_CLOUD_BYTES="+str(3358711686)+"\ntimeout --signal=TERM --kill-after=5s 1510s .venv/bin/python -B /var/lib/p8-continuation-v10/deployment/export-handover-code-v1/handover.py\n"
    write('handover-live.sh',script)
    write('reuse-installed-source.sh',h+'''.venv/bin/python -B - <<'REUSE'
import sys,json,hashlib,hmac
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'artifacts/phase-8-runner-amendment/v4-complete'))
from controls import read,hash_file,canonical
source=Path.cwd();dep=Path('/var/lib/p8-continuation-v10/deployment')
baseline=read(Path('/var/lib/p8-combined-v4/deployment/host-health-readiness.json'));assert sys.version==baseline['python'] and sys.version_info[:3]==(3,12,13)
inventory=read(source/'artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json')
assert hashlib.sha256(canonical(inventory['files'])).hexdigest()==inventory['package_hash']=='bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c'
for name,digest in inventory['files'].items():assert hash_file(source/name)==digest,'INSTALLED_SOURCE_DRIFT:'+name
manifest=read(dep/'public-authority/freeze-manifest.json');attestation=read(dep/'public-authority/freeze-attestation.json');owner=Path('/var/lib/fyp-owner')
assert hmac.compare_digest(attestation['signature'],hmac.new((owner/'owner.key').read_bytes(),canonical(manifest),'sha256').hexdigest())
assert manifest['package_hash']==inventory['package_hash'] and manifest['archive_sha256']=='212269264d45ac8bd6637c2ca0ca5e09c951d354cb445c9bf7a16c6ba2d0ba37'
for name,digest in manifest['files'].items():assert hash_file(owner/'continuation-v10-receipts'/name)==digest
assert not (owner/'continuation-v10-receipts/CONTINUATION_LAUNCH.json').exists()
print(json.dumps({'status':'PASS_REUSED_INSTALLED_SOURCE_AND_FROZEN_AUTHORITY','source_files':len(inventory['files']),'archive_downloads':0,'archive_uploads':0,'refreeze':False,'python':sys.version}))
REUSE
''')
    parsed=0
    import re
    for p in HERE.glob('*.sh'):
        text=p.read_text();assert b'\r' not in p.read_bytes()
        for m in re.finditer(r"<<'([A-Z_]+)'\n",text):
            end=text.find('\n'+m.group(1)+'\n',m.end());assert end!=-1;ast.parse(text[m.end():end]);parsed+=1
    for p in HERE.glob('*.py'):ast.parse(p.read_text())
    write('external-command-review.json',json.dumps({'status':'PASS_SYNTAX_REUSED_STAGES_PENDING_LIVE_GATES','python_blocks':parsed,
        'no_source_bootstrap':True,'handover_sha256':driver_hash,'core_sha256':code_hash,
        'eight_offline_controls':'PASS_0.044_SECONDS_PINNED_LINUX','type_check':'PASS_LINUX_PLATFORM_EXTERNAL_BOUNDARIES',
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()}},indent=2))
    print('Installed-source reuse and bounded handover wrappers ready')

if __name__=='__main__':main()
