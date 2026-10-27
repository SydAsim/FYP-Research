"""Record successful returned phase evidence without repeating the remote action."""
import hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent
label,file=sys.argv[1:]
p=H/file
reply=json.loads(p.read_bytes())['result']
assert reply['Status']=='Success' and reply['ResponseCode']==0
objects=[]
for line in reply['StandardOutputContent'].splitlines():
    if line.startswith('{'):objects.append(json.loads(line))
value={'status':'REMOTE_PHASE_SUCCESS','label':label,'command_id':reply['CommandId'],'response_record_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'stdout':reply['StandardOutputContent'],'last_json':objects[-1] if objects else None}
with (H/(label+'-verified.json')).open('x') as f:json.dump(value,f,indent=2)
print(json.dumps({'status':value['status'],'label':label,'command_id':reply['CommandId'],'result':value['last_json']}))
