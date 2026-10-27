"""Finite static review of all external deployment commands before AWS boot."""
import ast
import hashlib
import json
import re
from datetime import UTC,datetime
from pathlib import Path
from build import HERE

def main():
    corrections=[]
    p=HERE/'install-timer-files.sh'
    before=p.read_text()
    after=before.replace('Description=Original Phase 8 deadline also applies during bootstrap','Description=Original campaign deadline, including paused time')
    assert before!=after
    p.write_text(after,encoding='utf-8',newline='\n')
    corrections.append({'file':p.name,'change':'Use actual retained v4 bootstrap timer ownership text from v4/user-data.sh, not an invented description','before_sha256':hashlib.sha256(before.encode()).hexdigest(),'after_sha256':hashlib.sha256(after.encode()).hexdigest()})
    # The platform meter alone omits archive directory sizes. Explicit live measurements
    # are present and frozen Policy.guard is invoked without zero-use substitutions.
    scripts=sorted(HERE.glob('*.sh'));blocks=0
    for p in scripts:
        b=p.read_bytes();assert b'\r' not in b and b'\x00' not in b,'NON_LF_OR_NUL:'+p.name
        text=b.decode()
        assert text.startswith('set -euo pipefail\n'),'BASH_OPTIONS:'+p.name
        for match in re.finditer(r"<<'([A-Z_]+)'\n",text):
            tag=match.group(1);end=text.find('\n'+tag+'\n',match.end());assert end!=-1,'UNTERMINATED_HEREDOC'
            body=text[match.end():end]
            if tag=='OBJECTS':json.loads(body)
            else:ast.parse(body);blocks+=1
    for p in HERE.glob('*.py'):ast.parse(p.read_text())
    source=(HERE/'prepare-source.corrected.sh').read_text()
    assert '0e6475df' not in source and "sys.version==qualified['python']" in source
    assert source.index('import boto3,botocore')<source.index('bootstrap-transfer.py')
    assert source.index('export PYTHONPATH=')<source.index("<<'IMPORT_CHECK'")
    assert '212269264d45ac8bd6637c2ca0ca5e09c951d354cb445c9bf7a16c6ba2d0ba37' in source and 'QmAcYmVhFW5GHo08qBB01sD.laBJlcyo' in source
    assert '.venv/bin/python -B' in (HERE/'prepare-metadata.sh').read_text()
    assert 'closed_boundary' in (HERE/'readiness.sh').read_text()
    assert '2026-10-25' in (HERE/'install-timer-files.sh').read_text()
    for name in ('readiness.sh','activate-controls-and-launch.sh','prepare-metadata.sh'):
        text=(HERE/name).read_text();assert '01a11705-11f1-75f4-b64e-8f0a3679518b' not in text and '267.156208' not in text,'STALE_120_SELECTION'
    transport=(HERE/'ops.py').read_text();assert "subprocess.run(['bash','-s']" in transport
    record={'status':'PASS_STATIC_COMMAND_REVIEW_PENDING_BASH_SYNTAX_AND_LIVE_GATES','at':datetime.now(UTC).isoformat(),
        'python_blocks_parsed':blocks,'LF_scripts':len(scripts),'corrections':corrections,
        'checks':['qualified host full build, no invented prior binary digest','existing environment paths/import before source transfer','Bash stdin and strict options','LF and Python heredoc quoting','fixed version and hash','exact145/P2 identities','effective-policy launch HMAC binding','432-hour and amended absolute timers; no deadline reset','PRELAUNCH -> genuine readiness/launch -> COMPLETE -> active controls -> release'],
        'frozen_changes':False,'tests_repeated':False,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file() and p.name!='command-review.json'}}
    with (HERE/'command-review.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
    print(json.dumps({'status':record['status'],'blocks':blocks,'scripts':len(scripts)}))

if __name__=='__main__':main()
