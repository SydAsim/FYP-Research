import os, json, hashlib, shutil
from pathlib import Path
from datetime import datetime, timezone

OUT = Path(__file__).parent
TARGET = 37906551
roots = [Path('D:/FYP-ResearchBackups'),Path('D:/P82'),Path('D:/P83'),Path('D:/P83R7'),Path('E:/'),Path.cwd()]
totals=[]; candidates=[]; exports=[]; checkpoints=[]; diagnostic=[]; errors=[]
for root in roots:
    total=0; count=0
    for base, dirs, files in os.walk('\\\\?\\'+str(root.resolve()), onerror=lambda e:errors.append(str(e))):
        dirs[:]=[d for d in dirs if d not in ('.git','node_modules','System Volume Information','$RECYCLE.BIN','.venv','__pycache__')]
        for name in files:
            p=Path(base)/name
            try: size=p.stat().st_size
            except OSError as e: errors.append(str(e));continue
            total+=size;count+=1
            item={'path':str(p),'bytes':size}
            if size==TARGET: item['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();candidates.append(item)
            if name=='export.json': exports.append(item)
            if any(s in name.lower() for s in ('checkpoint','identity.json','transport.lock')) and ('p8driver145' in str(p) or 'driver-diagnosis-145' in str(p)):checkpoints.append(item)
            if ('p8driver145v1' in str(p) or 'driver-diagnosis-145-v1' in str(p)):diagnostic.append(item)
    totals.append({'root':str(root),'files':count,'bytes':total})
result={'at':datetime.now(timezone.utc).isoformat(),'totals':totals,'target_size_candidates':candidates,'exports':exports,'checkpoints':checkpoints,'diagnostic_files':diagnostic,'errors':errors,'disk':{d:dict(zip(('total','used','free'),shutil.disk_usage(d))) for d in ('C:/','D:/','E:/')}}
OUT.mkdir(exist_ok=True)
(OUT/'local-inventory.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'totals':totals,'candidates':candidates,'exports':len(exports),'diagnostic_bytes':sum(x['bytes'] for x in diagnostic),'errors':len(errors)},indent=2))
