"""One-request recorder for the unchanged v10 external deployment controller."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent

def record(name: str, value: object) -> None:
    with (HERE / name).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2)

def call(label: str, args: list[str], *, seconds: int = 45, region: str = 'ap-southeast-2') -> dict:
    command = ['aws', *args, '--profile', 'fyp-research', '--region', region,
               '--cli-connect-timeout', '5', '--cli-read-timeout', '25', '--output', 'json', '--no-cli-pager']
    record(label+'-request.json', {'at':datetime.now(UTC).isoformat(),'command':command,'process_deadline_seconds':seconds,'automatic_retries':0})
    env={**os.environ,'AWS_MAX_ATTEMPTS':'1','AWS_RETRY_MODE':'standard','AWS_PAGER':''}
    tick=time.monotonic()
    try:
        p=subprocess.run(command,capture_output=True,text=True,timeout=seconds,env=env)
        result={'exit':p.returncode,'stderr':p.stderr,'result':json.loads(p.stdout) if p.returncode==0 and p.stdout.strip() else p.stdout}
    except subprocess.TimeoutExpired:
        result={'exit':'PROCESS_TIMEOUT','result':None,'deadline_seconds':seconds}
    result.update(seconds=time.monotonic()-tick,at=datetime.now(UTC).isoformat())
    record(label+'-result.json',result)
    if result['exit']!=0:
        raise RuntimeError('CONTROL_REQUEST_FAILED_PRESERVED:'+label)
    return result['result']

def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument('label');parser.add_argument('arguments',nargs=argparse.REMAINDER)
    a=parser.parse_args()
    result=call(a.label,a.arguments)
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
