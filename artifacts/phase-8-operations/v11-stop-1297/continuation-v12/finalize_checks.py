"""Retain pre-freeze generator failure and install explicit verified control constants."""
from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent
R='artifacts/phase-8-runner-amendment/v4-complete/'
S=Path('E:/p8v12/source')
with (H/'prequalification-inventory.json').open('xb') as f:f.write((S/R/'candidate-inventory.json').read_bytes())
for n in ['closed1297.py','check_policy_boundary_v12.py']:
    shutil.copyfile(S/R/n,H/('generator-attempt1-'+n+'.txt'))
    shutil.copyfile(H/n,S/R/n)
inv=json.loads((S/R/'candidate-inventory.json').read_bytes())
for n in ['closed1297.py','check_policy_boundary_v12.py']:
    inv['files'][R+n]=hashlib.sha256((S/R/n).read_bytes()).hexdigest()
inv['package_hash']=hashlib.sha256(json.dumps(inv['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
(S/R/'candidate-inventory.json').write_text(json.dumps(inv,indent=2),encoding='utf-8',newline='\n')
with (H/'local-qualification-attempt1.json').open('x') as f:json.dump({'status':'FAILED_RETAINED','error':'Exact-deadline control retained old formatted v11 assertion due whitespace-sensitive generator replacement. Inspection also found old formatted closed-boundary constants not fully replaced. Before any freeze or cloud writes, replaced the two new files with explicit approved constants and qualified gate logic. Frozen v11 unchanged.','research_executions':0,'candidate_not_frozen':True},f,indent=2)
print(json.dumps({'package_hash':inv['package_hash'],'two_new_files_explicitly_corrected_before_freeze':True}))
