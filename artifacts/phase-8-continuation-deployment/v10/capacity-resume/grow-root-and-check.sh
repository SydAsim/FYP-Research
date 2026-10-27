set -euo pipefail
umask 077
python3 - <<'GROW'
import json,os,shutil,subprocess
from pathlib import Path
from datetime import datetime,UTC
p=Path('/var/lib/p8-continuation-v10/deployment');before_path=p/'root-expansion-before.json';after_path=p/'root-expansion-after.json'
def run(args):return subprocess.run(args,capture_output=True,text=True,check=True,timeout=180).stdout
mounted=json.loads(run(['findmnt','--json','--target','/','--output','SOURCE,FSTYPE,TARGET,MAJ:MIN']))['filesystems'][0]
layout=json.loads(run(['lsblk','--bytes','--json','--output','NAME,PATH,SIZE,TYPE,FSTYPE,PKNAME,MAJ:MIN,SERIAL,UUID']))
flat=[]
def flatten(nodes):
 for n in nodes:flat.append(n);flatten(n.get('children',[]))
flatten(layout['blockdevices']);parts=[n for n in flat if n['maj:min']==mounted['maj:min']]
assert len(parts)==1;part=parts[0];assert part['type']=='part' and mounted['fstype']==part['fstype']=='ext4','UNQUALIFIED_ROOT_LAYOUT'
disks=[n for n in flat if n['name']==part['pkname']];assert len(disks)==1;disk=disks[0]
assert disk['type']=='disk' and str(disk['serial']).replace('-','')=='vol09dbb42bbf607f5de','ROOT_VOLUME_IDENTITY_DRIFT'
assert disk['size']==165*1024**3,'ACTUAL_BLOCK_DEVICE_SIZE_NOT_165GIB'
number=int(Path('/sys/class/block',part['name'],'partition').read_text());assert number==1
assert all(shutil.which(c) for c in ('growpart','resize2fs','sfdisk')),'REQUIRED_INSTALLED_TOOL_MISSING'
record={'at':datetime.now(UTC).isoformat(),'mount':mounted,'layout':layout,'partition_table':run(['sfdisk','--dump',disk['path']]),'fs_stat':dict(total=shutil.disk_usage('/').total,used=shutil.disk_usage('/').used,free=shutil.disk_usage('/').free),'root_uuid':part['uuid']}
with before_path.open('x') as f:json.dump(record,f,indent=2);f.flush();os.fsync(f.fileno())
# Boot may already have performed cloud-init growpart. Decide from actual sizes.
if disk['size']-part['size']>2*1024**3:
 result=run(['growpart',disk['path'],str(number)])
 with (p/'growpart-result.txt').open('x') as f:f.write(result)
else:result='Existing root partition already occupies expanded volume; no partition write needed.'
resized=run(['resize2fs',part['path']])
after=json.loads(run(['lsblk','--bytes','--json','--output','NAME,PATH,SIZE,TYPE,FSTYPE,PKNAME,MAJ:MIN,SERIAL,UUID']));flat=[];flatten(after['blockdevices']);current=[n for n in flat if n['maj:min']==mounted['maj:min']][0]
assert current['uuid']==part['uuid'] and current['path']==part['path'] and disk['size']-current['size']<2*1024**3,'ROOT_PARTITION_BINDING_OR_SIZE_DRIFT'
capacity=shutil.disk_usage('/');assert capacity.free>=145670462448+1073741824,'EXPANDED_USABLE_FREE_CAPACITY_OR_MARGIN_STOP'
proof={'status':'PASS_ACTUAL_FILESYSTEM_CAPACITY_NOT_REQUEST_ONLY','at':datetime.now(UTC).isoformat(),'volume_id':'vol-09dbb42bbf607f5de','requested_gib':165,'actual_block_bytes':disk['size'],'actual_partition_bytes':current['size'],'actual_filesystem_total_bytes':capacity.total,'actual_filesystem_free_bytes':capacity.free,'required_free_bytes':145670462448,'margin_bytes':capacity.free-145670462448,'minimum_margin_bytes':1073741824,'root_uuid_unchanged':True,'partition_operation':result,'resize2fs_output':resized,'after_layout':after,'evidence_deleted':False}
with after_path.open('x') as f:json.dump(proof,f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps(proof))
GROW
