from pathlib import Path
HERE=Path(__file__).resolve().parent
previous=HERE.parents[1]/'phase-8-continuation-deployment/v7-attempt3'
for name in ('ops.py','actual-deployment-binding.json'):
    with (HERE/name).open('xb') as out:out.write((previous/name).read_bytes())
