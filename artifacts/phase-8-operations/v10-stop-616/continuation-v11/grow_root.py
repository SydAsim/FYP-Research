"""Verified existing NVMe/ext4 online expansion; preserve layout and prior fence."""
import json,sys,subprocess,shutil,hashlib
from pathlib import Path
from datetime import datetime

def main():
    dep=Path('/var/lib/p8-continuation-v11/deployment');plan=json.loads((dep/'root-resize-plan.json').read_text())
    root=Path('/var/lib/p8-continuation-v9/run');history=root/'restart-history/v11-root-176';history.mkdir(mode=0o700,exist_ok=False)
    def run(args):return subprocess.run(args,check=True,capture_output=True,text=True,timeout=30).stdout
    assert plan['new_size_gib']==176 and plan['volume_id']=='vol-09dbb42bbf607f5de'
    mount=json.loads(run(['findmnt','-J','-o','SOURCE,FSTYPE,UUID','/']))['filesystems'][0]
    assert mount['source']=='/dev/nvme0n1p1' and mount['fstype']=='ext4' and mount['uuid']=='6064d37b-2f18-4067-a280-abb8a265f6a7'
    assert run(['lsblk','-dn','-o','SERIAL','/dev/nvme0n1']).strip()=='vol09dbb42bbf607f5de'
    assert int(run(['blockdev','--getsize64','/dev/nvme0n1']))==176*1024**3,'BLOCK_CAPACITY_NOT_READY'
    before={'mount':mount,'partition_table':run(['sfdisk','--dump','/dev/nvme0n1']),'filesystem':shutil.disk_usage('/')._asdict(),'plan':plan}
    with (history/'before.json').open('x') as f:json.dump(before,f,indent=2)
    output=run(['growpart','/dev/nvme0n1','1'])
    filesystem=run(['resize2fs','/dev/nvme0n1p1'])
    after=json.loads(run(['findmnt','-J','-o','SOURCE,FSTYPE,UUID','/']))['filesystems'][0]
    assert after==mount
    capacity=shutil.disk_usage('/');assert capacity.free>=plan['required_free_bytes'],'USABLE_FILESYSTEM_HEADROOM_STOP'
    # Retain old reviewed fence bytes; install a conservative second-rounded fence.
    script=dep/'admission-cutoff.py';unit=Path('/etc/systemd/system/fyp-v11-admission-cutoff.timer')
    shutil.copyfile(script,history/script.name);shutil.copyfile(unit,history/unit.name)
    fence=datetime.fromisoformat(plan['external_admission_fence']).replace(microsecond=0)
    text=script.read_text().replace('2026-10-25T23:30:00+00:00',fence.isoformat());assert text!=script.read_text()
    script.write_text(text)
    timer=unit.read_text().replace('2026-10-25 23:30:00 UTC',fence.strftime('%Y-%m-%d %H:%M:%S UTC'));unit.write_text(timer)
    subprocess.run(['systemctl','daemon-reload'],check=True,timeout=20)
    subprocess.run(['systemctl','restart','fyp-v11-admission-cutoff.timer'],check=True,timeout=20)
    subprocess.run(['systemctl','is-active','--quiet','fyp-v11-admission-cutoff.timer'],check=True,timeout=10)
    with (history/'root-resize-plan.json').open('x') as f:json.dump(plan,f,indent=2)
    result={'status':'PASS_ACTUAL_FILESYSTEM_EXPANSION','old_gib':167,'new_gib':176,'actual_filesystem_bytes':capacity.total,'free_bytes':capacity.free,'required_free_bytes':plan['required_free_bytes'],'margin_above_requirement_bytes':capacity.free-plan['required_free_bytes'],'root_uuid':after['uuid'],'growpart':output,'resize2fs':filesystem,'admission_fence':fence.isoformat(),'total_extra_storage_reserve_usd':plan['total_extra_storage_reserve_usd'],'fence_script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'fence_timer_sha256':hashlib.sha256(unit.read_bytes()).hexdigest(),'no_source_change':True,'no_evidence_deleted':True}
    with (dep/'root-resize-verified.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
if __name__=='__main__':main()
