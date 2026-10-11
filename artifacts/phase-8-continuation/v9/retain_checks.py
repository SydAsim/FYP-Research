import json
from pathlib import Path
from prepare import HERE,write

write(HERE/'retained-preparation-attempt1.json',{'status':'FAILED_STRESS_ESTIMATE_RETAINED',
 'command':'prepare_final.py first attempt','error':'RECORDED_HOST_HEADROOM_INSUFFICIENT',
 'assumption':'Simultaneous 80GiB backup + 50GiB working + 20GiB free',
 'qualification_affected':False,'AWS_mutations':0,
 'disposition':'Not a promise made by independent caps. Measured working projection and this failing stress sensitivity are separately reported; existing live guards unchanged.'})
write(HERE/'static-checks.json',{'ruff':'PASS four modified runtime Python files',
 'initial_mypy':'FAIL: eight missing boto3/botocore third-party imports in this Windows interpreter; no local code type errors',
 'final_mypy':'PASS configured strict mode with --ignore-missing-imports at third-party SDK import boundary; four runtime files',
 'SDK_import':'Pinned Linux offline runtime imported SDK successfully through existing qualified transport environment. No dependencies installed.'})
path=HERE/'REPORT.md'
path.write_text(path.read_text()+'''\n## Disk planning limitation\n\nThe latest original-120 host reading had 142.1GiB free. Future local archives\nare bounded by 80GiB; measured raw payload maximum (26,194,780 bytes per slot)\nfor all 1,380 slots plus 2GiB mutable/source allowance projects 35.67GiB working\ngrowth. Together with 20GiB free, this fits with about 6.4GiB remaining. The\nunchanged 50GiB working cap is a stop threshold, not a promise of simultaneous\nmaximum occupancy. Both the initial 150GiB simultaneous-cap assumption and a\ndoubled raw-payload sensitivity fail and are retained. This does not reduce\nthe separately reviewed doubled compressed-ledger or runtime allowances.\nActual payload growth can cause a safe resource pause before study completion.\nFresh host headroom is mandatory before admission.\n''')
print('Failed stress estimate and SDK static boundary limitation retained.')
