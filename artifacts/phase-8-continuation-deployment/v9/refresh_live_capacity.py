"""Account for measured real handover archives before any admission."""
from pathlib import Path
import json
from ops import HERE
from controls import read,write_new

def final_record(name):
    reply=read(HERE/name)['result']
    assert reply['Status']=='Success' and reply['ResponseCode']==0
    records=[json.loads(line) for line in reply['StandardOutputContent'].splitlines() if line.startswith('{')]
    found=[r for r in records if r.get('status')=='PASS' and 'proof' in r]
    assert len(found)==1
    return found[0]['proof']

def main():
    proofs=[final_record('prelaunch-backup-status2-result.json'),final_record('complete-backup-status1-result.json')]
    candidate=read(HERE.parents[1]/'phase-8-continuation/v9/estimates.json')
    base=max(p['cloud']['bytes'] for p in proofs)
    updated=candidate['capacity_planning_bytes']+(1380+2)*max(0,base-candidate['measured_new_metadata_archive_bytes'])+600*1024**2
    assert updated+1024**3<80*1024**3
    write_new(HERE/'measured-live-archive-projection.json',{'status':'PASS_BEFORE_ADMISSION',
      'measured_live_metadata_archive_bytes':base,'projection_excluding_new_inventory_delta_bytes':updated,
      'cloud_and_local_cap_bytes':80*1024**3,'slot_reserve_bytes':1024**3,
      'reviewed_time_and_ledger_growth_allowances_unchanged':True,'actual_backup_proofs':proofs,
      'live_inventory_delta_required_in_immediate_gate':True})
    p=HERE/'launch-service.sh';s=p.read_text()
    needle="assert reserved==0\n"
    insertion="assert reserved==0\n# Fresh live handover size replaces the earlier calibration size conservatively.\nprojected="+repr(updated)+"+max(0,cloud_bytes-"+str(candidate['current_cloud_all_versions_bytes'])+")\nassert projected+a.policy.slot_capacity_reserve_bytes<a.policy.cloud_limit_bytes, 'LIVE_ARCHIVE_PROJECTION_STOP'\n"
    assert s.count(needle)==1;s=s.replace(needle,insertion)
    s=s.replace("sample=host(root,root.parent/'backup');guard", "sample=host(root,root.parent/'backup')\nassert sample['system_free_bytes']>=145670462448, 'MEASURED_DISK_PROJECTION_STOP'\nguard")
    s=s.replace("'both_backups_verified':True,","'both_backups_verified':True,'live_capacity_projection_bytes':projected,")
    p.write_text(s)
    print(json.dumps({'status':'PASS','new_base_bytes':base,'projection_gib':updated/1024**3,'before_inventory_delta':True}))

if __name__=='__main__':main()
