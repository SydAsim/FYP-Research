from pathlib import Path
import sys,json
from datetime import datetime,UTC
sys.path.insert(0,'/opt/fyp-phase8-continuation-v10/artifacts/phase-8-runner-amendment/v4-complete')
from controls import Journal,read,hash_file,utc
root=Path('/var/lib/p8-continuation-v9/run');capacity=read(Path('/var/lib/p8-continuation-v10/deployment/capacity-authorization.json'))
assert utc()>=datetime.fromisoformat(capacity['external_admission_cost_fence'])
assert read(root/'run.json')['source']=='/opt/fyp-phase8-continuation-v10'
j=Journal(root);j.verify();j.pause('EXPANDED_ROOT_COST_ADMISSION_STOP')
j.event('EXPANDED_ROOT_COST_ADMISSION_FENCE',additional_reserved_usd=capacity['added_storage_full_remaining_plus48h_reserve_usd'],admission_guard_usd=70,active_collection_continues=True)
print('STOP_NEW_ADMISSIONS; active collection deadline unchanged; historical outcomes unchanged')
