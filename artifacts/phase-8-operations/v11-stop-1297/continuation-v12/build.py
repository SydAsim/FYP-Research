"""Separate v12 operational overlay; preserve every frozen v11 file in place."""
from __future__ import annotations

import difflib
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=Path('E:/p8v11/source')
SOURCE=Path('E:/p8v12/source')
PREFIX='artifacts/phase-8-runner-amendment/v4-complete/'
canon=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()


def digest(p:Path)->str:
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def write(p:Path,value:object)->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2)


def main()->None:
    assert not SOURCE.exists(),'NEW_VERSION_DIRECTORY_REQUIRED'
    parent=json.loads((PARENT/PREFIX/'candidate-inventory.json').read_bytes())
    assert hashlib.sha256(canon(parent['files'])).hexdigest()==parent['package_hash']=='e89ca0fbb9c9e7333a18af23014d0d00d4ffbc6dbe1298f0546620523626e348'
    for name,expected in parent['files'].items():
        assert digest(PARENT/name)==expected,name
        target=SOURCE/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(PARENT/name,target)
    shutil.copyfile(PARENT/PREFIX/'candidate-inventory.json',SOURCE/PREFIX/'parent-v11-inventory.json')
    runtime=SOURCE/PREFIX
    hours=(datetime.fromisoformat('2026-10-26T12:00:00+00:00')-datetime.fromisoformat('2026-10-07T15:24:23.810674+00:00')).total_seconds()/3600
    old_limits=json.loads((runtime/'operational-limit-proposal.json').read_bytes())
    limits={**old_limits,'version':'phase85-continuation-v12','amended_deadline':'2026-10-26T12:00:00Z','elapsed_host_limit_hours':hours,'retention_decision_deadline':'2026-10-28T12:00:00Z','admission_committed_usd':76,'budget_usd':77,'retention':'Owned root retained through this continuation and up to48hours after actual shutdown; decision no later than2026-10-28T12:00:00Z. No deletion authorized.'}
    (runtime/'operational-limit-proposal.json').write_text(json.dumps(limits,indent=2),encoding='utf-8',newline='\n')
    limhash=digest(runtime/'operational-limit-proposal.json')
    p=runtime/'controls.py';s=p.read_text()
    assert 'Literal[65, 75]' in s and 'Literal[55, 60, 70, 74]' in s
    s=s.replace('Literal[65, 75]','Literal[65, 75, 77]').replace('Literal[55, 60, 70, 74]','Literal[55, 60, 70, 74, 76]')
    s=s.replace('if value not in (360, 432, 440.5933859238889):','if value not in (360, 432, 440.5933859238889, '+repr(hours)+'):')
    p.write_text(s,encoding='utf-8',newline='\n')
    p=runtime/'operational_limits.py';s=p.read_text()
    s=s.replace('566556298a1135ed4f60cd78770415e74705a08a1dbff25398183ce863007869',limhash)
    s=s.replace('phase85-continuation-v11','phase85-continuation-v12').replace('2026-10-26T00:00:00Z','2026-10-26T12:00:00Z').replace('2026-10-28T00:00:00Z','2026-10-28T12:00:00Z')
    s=s.replace('440.5933859238889',repr(hours)).replace('admission_committed_usd: Literal[74]','admission_committed_usd: Literal[76]').replace('budget_usd: Literal[75]','budget_usd: Literal[77]')
    s=s.replace('budget_usd: Literal[65, 75] = 75','budget_usd: Literal[65, 75, 77] = 77').replace('admission_committed_usd: Literal[55, 60, 70, 74] = 74','admission_committed_usd: Literal[55, 60, 70, 74, 76] = 76')
    p.write_text(s,encoding='utf-8',newline='\n')
    # Reuse the qualified closed-boundary pattern, preserving old616 gates.
    s=(runtime/'closed616.py').read_text().replace('closed616','closed1297').replace('CLOSED616','CLOSED1297').replace('COUNT=616','COUNT=1297').replace('NEXT617','NEXT1298')
    s=s.replace("NEXT='01a11705-11f2-7276-8d5f-0277ced1a5f5'","NEXT='01a11705-11f4-7c05-9897-af35348a8028'")
    s=s.replace("MASTER='f1fbd0bfdbfda588bc9ef51a45142c72acdf0ee4a7772b53a02752fa66a020ba'","MASTER='98b581a9b3868d51f2bb8fafb1dde510c174970089bae488a1aea3677b61effe'")
    s=s.replace("PAUSE='b2cddd1475c8b1dd2e471b7bc2cde283dfb4ef23a928a12a56be06086d8840fc'","PAUSE='7cf255c9359c9c88951eac98eade347adad2831ad1fd522ea1eab33e1c616ab8'")
    s=s.replace('continuation-v11-boundary','continuation-v12-boundary').replace("rows[COUNT]['arm']!='P2'","rows[COUNT]['arm']!='B3'").replace('item.size>32*1024**2','item.size>128*1024**2')
    s=s.replace("return {'backed_up':616,'planned':884", "return {'backed_up':1297,'planned':203")
    (runtime/'closed1297.py').write_text(s,encoding='utf-8',newline='\n')
    p=runtime/'handover.py';s=p.read_text()
    s=s.replace('566556298a1135ed4f60cd78770415e74705a08a1dbff25398183ce863007869',limhash)
    s=s.replace('phase85-continuation-v11','phase85-continuation-v12').replace('retained-host-clock-before-v11.json','retained-host-clock-before-v12.json').replace('retained-driver616-pause-v11.json','retained-protocol1297-pause-v12.json')
    s=s.replace('b886fff14d4e8384c406deb68a875bc21a9c53e2bac5a17787d800fc1d2d192f','1de01eb9ce2a8ebfa9b8a2591bbf84f62abf031d7dadf32bfaffa3254164095a')
    # Change only reviewed current-boundary entry points; historical616 remains.
    s=s.replace('    from closed616 import REL, check_rows','    from closed1297 import REL, check_rows')
    marker='    verify616(root)'
    assert s.count(marker)==1
    s=s.replace(marker,marker+'\n    from closed1297 import verify as verify1297\n    verify1297(root)')
    s=s.replace('b2cddd1475c8b1dd2e471b7bc2cde283dfb4ef23a928a12a56be06086d8840fc','7cf255c9359c9c88951eac98eade347adad2831ad1fd522ea1eab33e1c616ab8')
    p.write_text(s,encoding='utf-8',newline='\n')
    write(runtime/'closed1297-reference.json',{'master_sha256':'98b581a9b3868d51f2bb8fafb1dde510c174970089bae488a1aea3677b61effe','master_s3_version':'pn_YI_TJ_E8f8w75te05AE1DELM5apFo','readback_sha256':'45663d96cc12318bd934fad04ebc528a4768347ad969457952c62a8643473d7b','pause_sha256':'7cf255c9359c9c88951eac98eade347adad2831ad1fd522ea1eab33e1c616ab8','boundary':{'BACKED_UP':1297,'PLANNED':203},'reuse':'Verified retained master/readback; no archive download or original replay required'})
    shutil.copyfile(HERE/'authorization.json',runtime/'conditional-human-authorization-v12.json')
    tests=(PARENT/PREFIX/'check_policy_boundary_v11.py').read_text().replace('closed616','closed1297').replace('616','1297').replace('884','203').replace('i<1297','i<1297').replace("rows[1297]['execution_id']='01a11705-11f2-7276-8d5f-0277ced1a5f5';rows[1297]['arm']='P2'","rows[1297]['execution_id']='01a11705-11f4-7c05-9897-af35348a8028';rows[1297]['arm']='B3'")
    tests=tests.replace('datetime(2026,10,26,tzinfo=UTC)','datetime(2026,10,26,12,tzinfo=UTC)').replace('policy.admission_committed_usd==74','policy.admission_committed_usd==76').replace('policy.budget_usd==75','policy.budget_usd==77').replace('OnCalendar=2026-10-26 00:00:00 UTC','OnCalendar=2026-10-26 12:00:00 UTC')
    (runtime/'check_policy_boundary_v12.py').write_text(tests,encoding='utf-8',newline='\n')
    files=dict(parent['files'])
    added=['parent-v11-inventory.json','closed1297.py','closed1297-reference.json','conditional-human-authorization-v12.json','check_policy_boundary_v12.py']
    changed=['controls.py','operational_limits.py','operational-limit-proposal.json','handover.py']
    diffs={}
    for name in changed+added:
        rel=PREFIX+name;files[rel]=digest(SOURCE/rel)
        if name in changed:
            diffs[rel]={'before':parent['files'][rel],'after':files[rel]}
            with (HERE/(name+'.diff')).open('x',newline='\n') as f:f.write(''.join(difflib.unified_diff((PARENT/rel).read_text().splitlines(True),(SOURCE/rel).read_text().splitlines(True),fromfile='frozen-v11/'+rel,tofile='v12/'+rel)))
    assert all(digest(SOURCE/n)==h for n,h in parent['files'].items() if n not in diffs)
    package=hashlib.sha256(canon(files)).hexdigest()
    write(runtime/'candidate-inventory.json',{'kind':'CONTINUATION_REVIEW_CANDIDATE_NOT_FREEZE','version':'phase85-continuation-v12','files':files,'package_hash':package,'parent_frozen_package_hash':parent['package_hash'],'operational_limits_sha256':limhash,'originals_retained':1297,'pending':203,'no_application_change':True,'historical_sidecar_applied':False})
    write(HERE/'runtime-differences.json',{'changed':diffs,'added':[PREFIX+n for n in added],'application_arm_fixture_oracle_analysis_changes':0,'boundary_sqlite_bound_change':'New1297 boundary uses128MiB upper bound for measured64,843,776-byte SQLite, old616 module unchanged','countermeasure':'Needrestart deferral external to frozen source, separately verified on retained root'})
    write(HERE/'source-prepared.json',{'source':str(SOURCE),'package_hash':package,'limits_sha256':limhash,'changed_files':changed,'added_files':added,'members':len(files),'hours':hours,'linux_qualification':'OUTSTANDING_ON_ACTUAL_VERIFIED_HOST_BEFORE_ADOPTION','local_docker':'UNAVAILABLE_NO_INSTALLATION_ATTEMPTED'})
    print(json.dumps({'package_hash':package,'limits_sha256':limhash,'source_members':len(files),'changed_runtime_files':changed,'no_application_changes':True}))


if __name__=='__main__':main()
