from pathlib import Path
import hashlib,json,difflib
H=Path(__file__).resolve().parent
S=Path('E:/p8v11/source');P=Path('E:/p8v10/source');R='artifacts/phase-8-runner-amendment/v4-complete/'
def main():
    r=S/R
    p=r/'operational-limit-proposal.json';oldhash=hashlib.sha256(p.read_bytes()).hexdigest();v=json.loads(p.read_text())
    v['retention']='Owned root retained through this continuation and up to48 hours after shutdown; decision no later than2026-10-28T00:00:00Z. No deletion authorized.'
    p.write_text(json.dumps(v,indent=2),encoding='utf-8',newline='\n');newhash=hashlib.sha256(p.read_bytes()).hexdigest()
    for name in ['operational_limits.py','handover.py']:
        p=r/name;s=p.read_text().replace(oldhash,newhash)
        if name=='handover.py':
            s=s.replace('        verify_imported_first(self.root)\n        from closed616 import verify as verify616\n        verify616(self.root)','        verify_imported_first(self.root)')
            marker='    from closed_prefix import verify\n\n    verify(root)'
            assert marker in s
            s=s.replace(marker,marker+'\n    from closed616 import verify as verify616\n    verify616(root)')
        p.write_text(s,encoding='utf-8',newline='\n')
    import shutil
    shutil.copyfile(H/'check_policy_boundary.py',r/'check_policy_boundary_v11.py')
    # New executable is inventoried and directly executable; not a production scenario.
    parent=json.loads((P/R/'candidate-inventory.json').read_text());files=dict(parent['files']);diffs={}
    for name in ['refusal.py','controls.py','handover.py','operational_limits.py','operational-limit-proposal.json','closed616.py','closed616-reference.json','conditional-human-authorization-v11.json','check_policy_boundary_v11.py']:
        rel=R+name;files[rel]=hashlib.sha256((S/rel).read_bytes()).hexdigest()
        if rel in parent['files'] and files[rel]!=parent['files'][rel]:
            diffs[rel]={'before':parent['files'][rel],'after':files[rel]}
            (H/(name+'.diff')).write_text(''.join(difflib.unified_diff((P/rel).read_text().splitlines(True),(S/rel).read_text().splitlines(True),fromfile='frozen-v10/'+rel,tofile='v11/'+rel)),encoding='utf-8',newline='\n')
    package=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    inventory={'kind':'CONTINUATION_REVIEW_CANDIDATE_NOT_FREEZE','version':'phase85-continuation-v11','files':files,'package_hash':package,'parent_frozen_package_hash':parent['package_hash'],'operational_limits_sha256':newhash,'amended_deadline':'2026-10-26T00:00:00Z','authority':'Explicit conditional authorization; no claim of personal review of unseen final bytes','historical_timing_sidecar_applied':False}
    (r/'candidate-inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8',newline='\n')
    (H/'runtime-differences.json').write_text(json.dumps(diffs,indent=2))
    (H/'source-ready-for-freeze.json').write_text(json.dumps({'package_hash':package,'limits_sha256':newhash,'members':len(files),'source':str(S),'added_executables':['closed616.py','check_policy_boundary_v11.py'],'changed':len(diffs),'application_changes':0},indent=2))
    print(package,newhash)
if __name__=='__main__':main()
