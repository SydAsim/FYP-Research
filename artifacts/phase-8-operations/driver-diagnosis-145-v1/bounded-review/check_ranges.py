import hashlib, json
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).parent
results=[]
for name in ('transport2','transport3'):
    root=Path('E:/p8driver145v1')/name
    identity=json.loads((root/'identity.json').read_text());verified=[];rejected=[]
    for proof_path in sorted((root/'pieces').glob('*.json')):
        p=proof_path.with_suffix('.bin');proof=json.loads(proof_path.read_text())
        begin,end=proof['range'];raw=p.read_bytes() if p.exists() else b''
        valid=(begin==int(proof_path.stem)*identity['chunk'] and end==min(begin+identity['chunk']-1,identity['receipt']['bytes']-1) and len(raw)==proof['bytes']==end-begin+1 and proof['version']==identity['receipt']['version_id'] and hashlib.sha256(raw).hexdigest()==proof['sha256'])
        (verified if valid else rejected).append({'range':[begin,end],'path':str(p)})
    results.append({'transport':name,'receipt':identity['receipt'],'deadline':identity['deadline'],'deadline_expired':datetime.now(timezone.utc).timestamp()>identity['deadline'],'verified_ranges':len(verified),'verified_bytes':sum(r['range'][1]-r['range'][0]+1 for r in verified),'rejected':rejected,'ranges':verified,'eligible_for_original145_merge':False,'reason':'Different object/version: inspection archive, not original145'})
(HERE/'range-audit.json').write_text(json.dumps(results,indent=2))
print(json.dumps([{k:v for k,v in r.items() if k not in ('ranges','receipt')} for r in results],indent=2))
