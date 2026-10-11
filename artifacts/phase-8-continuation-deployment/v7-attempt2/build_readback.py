from pathlib import Path

here=Path(__file__).resolve().parent
text=(here.parent/'v7/readback_and_stop.py').read_text(encoding='utf-8')
text=text.replace('preserve-failed-bootstrap-status1-result.json','preserve-readiness-attempt2-status1-result.json')
text=text.replace('E:/p8v7/blocked-20261009-v7','E:/p8v7/blocked-20261009-v7-attempt2')
text=text.replace('V7_FROZEN_VERIFIED_BOOTSTRAP_BLOCKED_HOST_STOPPED','V7_FROZEN_VERIFIED_READINESS_BLOCKED_HOST_STOPPED')
text=text.replace('Deployment bootstrap used application .venv without qualified transport PYTHONPATH; import boto3 failed before transfer','OLD_OPERATIONAL_UNIT_RUNNING: a pre-existing enabled operational unit restarted at boot; read-only live gate failed before metadata import or main admission')
text=text.replace('750e4701-9cb8-4049-bb86-3596e7951565','34df8031-b7d8-4ddf-8d87-116a8d8b76b4')
with (here/'readback_and_stop.py').open('x',encoding='utf-8',newline='\n') as f:
    f.write(text)
