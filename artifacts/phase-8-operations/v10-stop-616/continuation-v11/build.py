from pathlib import Path
from datetime import datetime
import hashlib,json,shutil,difflib

HERE=Path(__file__).resolve().parent
PARENT=Path('E:/p8v10/source');SOURCE=Path('E:/p8v11/source')
PREFIX='artifacts/phase-8-runner-amendment/v4-complete/'
canon=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2),encoding='utf-8',newline='\n')
def main():
    assert not SOURCE.exists()
    parent=json.loads((PARENT/PREFIX/'candidate-inventory.json').read_text())
    assert hashlib.sha256(canon(parent['files'])).hexdigest()==parent['package_hash']=='bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c'
    for n,h in parent['files'].items():
        assert hashfile(PARENT/n)==h,n
        dest=SOURCE/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(PARENT/n,dest)
    runtime=SOURCE/PREFIX
    shutil.copyfile(HERE.parent/'candidate/refusal.py',runtime/'refusal.py')
    hours=(datetime.fromisoformat('2026-10-26T00:00:00+00:00')-datetime.fromisoformat('2026-10-07T15:24:23.810674+00:00')).total_seconds()/3600
    oldlimits=json.loads((runtime/'operational-limit-proposal.json').read_text())
    limits={**oldlimits,'version':'phase85-continuation-v11','amended_deadline':'2026-10-26T00:00:00Z','elapsed_host_limit_hours':hours,'retention_decision_deadline':'2026-10-28T00:00:00Z','admission_committed_usd':74}
    write(runtime/'operational-limit-proposal.json',limits);limhash=hashfile(runtime/'operational-limit-proposal.json')
    p=runtime/'controls.py';s=p.read_text();s=s.replace('host_hours: Literal[360, 432] = 360','host_hours: Literal[360, 432] | float = 360').replace('Literal[55, 60, 70]','Literal[55, 60, 70, 74]');marker='    @field_validator("host_started_at")';s=s.replace(marker,'    @field_validator("host_hours")\n    @classmethod\n    def allowed_host_hours(cls, value: float) -> float:\n        if value not in (360, 432, '+repr(hours)+'):\n            raise ValueError("UNAPPROVED_HOST_LIMIT")\n        return value\n\n'+marker)
    # Preserve old integer serialization so historical policy signatures remain valid.
    s=s.replace('def allowed_host_hours(cls, value: float) -> float:','def allowed_host_hours(cls, value: int | float) -> int | float:')
    p.write_text(s,encoding='utf-8',newline='\n')
    p=runtime/'operational_limits.py';s=p.read_text().replace('6d86b62931593e80e7cedd5371d9a72c14075b17d9a30c541e950e0f6af9af68',limhash).replace('phase85-continuation-v10','phase85-continuation-v11').replace('2026-10-25T15:24:23.810674Z','2026-10-26T00:00:00Z').replace('2026-10-27T15:24:23.810674Z','2026-10-28T00:00:00Z').replace('elapsed_host_limit_hours: Literal[432]','elapsed_host_limit_hours: float = Field(ge='+repr(hours)+', le='+repr(hours)+')').replace('admission_committed_usd: Literal[70]','admission_committed_usd: Literal[74]').replace('host_hours: Literal[360, 432] = 432','host_hours: Literal[360, 432] | float = '+repr(hours)).replace('admission_committed_usd: Literal[55, 60, 70] = 70','admission_committed_usd: Literal[55, 60, 70, 74] = 74').replace('from pydantic import','from pydantic import')
    s=s.replace('from controls import Policy, Strict, hash_file, read','from controls import Policy, Strict, hash_file, read\nfrom pydantic import Field');p.write_text(s,encoding='utf-8',newline='\n')
    p=runtime/'handover.py';s=p.read_text().replace('6d86b62931593e80e7cedd5371d9a72c14075b17d9a30c541e950e0f6af9af68',limhash).replace('phase85-continuation-v10','phase85-continuation-v11').replace('retained-host-clock-before-v10.json','retained-host-clock-before-v11.json').replace('retained-driver145-pause-v10.json','retained-driver616-pause-v11.json').replace('92ef953de04518facf4c6dcc72d13572e1648ccad28001bad58ee435969a5162','b886fff14d4e8384c406deb68a875bc21a9c53e2bac5a17787d800fc1d2d192f')
    begin=s.index('def closed_boundary(');end=s.index('\n\ndef ',begin+5)
    s=s[:begin]+'''def closed_boundary(rows: list[dict[str, Any]], saved: list[dict[str, Any]]) -> None:
    from closed616 import check_rows, REL
    if any(any(a[k] != b[k] for k in ("sequence","case_id","arm","attempt","fixture_hash")) for a,b in zip(rows,saved,strict=True)):
        raise ValueError("SAVED_ORDER_OR_BINDING_DRIFT")
    check_rows(rows,read(Path("/var/lib/p8-continuation-v9/run") / REL)["rows"])
'''+s[end:]
    s=s.replace('        verify_imported_first(self.root)','        verify_imported_first(self.root)\n        from closed616 import verify as verify616\n        verify616(self.root)')
    s=s.replace('hash_file(HERE / "closed-145/pause.json")','"b2cddd1475c8b1dd2e471b7bc2cde283dfb4ef23a928a12a56be06086d8840fc"')
    p.write_text(s,encoding='utf-8',newline='\n')
    shutil.copyfile(HERE/'closed616.py',runtime/'closed616.py')
    write(runtime/'closed616-reference.json',{'master_sha256':'f1fbd0bfdbfda588bc9ef51a45142c72acdf0ee4a7772b53a02752fa66a020ba','master_s3_version':'R4nE4l2ASxFLolEQKfZpmoGmkeXv6gQ4','readback_sha256':'9c61e51d54dc6070114dd8348ae6d9e2f904a72ed920aa0e2dabceafc0f9014a','boundary':{'BACKED_UP':616,'PLANNED':884},'no_new_evidence_download':'Use verified retained master under guarded preparation'})
    write(runtime/'conditional-human-authorization-v11.json',json.loads((HERE/'authorization.json').read_text()))
    diffs={}
    for name in parent['files']:
        if hashfile(SOURCE/name)!=parent['files'][name]:
            assert name.startswith(PREFIX),name
            diffs[name]={'before':parent['files'][name],'after':hashfile(SOURCE/name)}
            if name.endswith('.py') or name.endswith('.json'):
                (HERE/(Path(name).name+'.diff')).write_text(''.join(difflib.unified_diff((PARENT/name).read_text().splitlines(True),(SOURCE/name).read_text().splitlines(True),fromfile='frozen-v10/'+name,tofile='v11/'+name)),encoding='utf-8',newline='\n')
    assert set(Path(n).name for n in diffs)=={'controls.py','operational_limits.py','operational-limit-proposal.json','handover.py','refusal.py'},diffs
    write(HERE/'runtime-differences.json',diffs)
    write(HERE/'source-prepared.json',{'source':str(SOURCE),'hours':hours,'limits_sha256':limhash,'parent_files':len(parent['files']),'changed':len(diffs),'application_files_changed':0})
    print(json.dumps({'source':str(SOURCE),'hours':hours,'limits_sha256':limhash,'changed':len(diffs)}))
if __name__=='__main__':main()
