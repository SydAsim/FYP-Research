"""External guarded controller records; unchanged frozen v10 runtime."""
from __future__ import annotations
import base64
import gzip
import json
import sys
import os
os.environ["PYTHONIOENCODING"]="utf-8"
os.environ["PYTHONUTF8"]="1"
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'attempt2'))
import read_control as recorder
recorder.HERE=HERE
call=recorder.call
record=recorder.record
HOST='i-057344e5372faf62f'

def send(label: str, script: Path, *, execution_seconds: int=1200) -> dict:
    packed=base64.b64encode(gzip.compress(script.read_bytes())).decode()
    # Execute from stdin. No exclusive transfer target from the ambiguous request is reused.
    commands=['set -eu','umask 077',"python3 - <<'CONTROLLER'\nimport base64,gzip,subprocess\nscript=gzip.decompress(base64.b64decode('"+packed+"')).decode()\nsubprocess.run(['bash','-s'],input=script,text=True,check=True)\nCONTROLLER"]
    params=HERE/(label+'-parameters.json')
    record(params.name,{'commands':commands,'executionTimeout':[str(execution_seconds)]})
    return call(label,['ssm','send-command','--instance-ids',HOST,'--document-name','AWS-RunShellScript',
                       '--comment','Frozen v10 guarded continuation: '+label,'--parameters','file://'+str(params),
                       '--timeout-seconds','60'])

def poll(label: str, command_id: str) -> dict:
    return call(label,['ssm','get-command-invocation','--instance-id',HOST,'--command-id',command_id])
