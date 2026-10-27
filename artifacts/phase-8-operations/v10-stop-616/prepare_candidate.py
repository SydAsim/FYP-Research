from pathlib import Path
import difflib,hashlib,json

here=Path(__file__).resolve().parent
folder=here/'candidate';folder.mkdir(exist_ok=False)
source=Path('E:/p8v10/source/artifacts/phase-8-runner-amendment/v4-complete/refusal.py')
old=source.read_text()
new=old.replace('        if chain:\n            # Bind','        resource_unavailable = bool(chain and resources[0]["raw"]["status"] == 501)\n        if chain:\n            # Bind')
new=new.replace('or any(o["raw"]["status"] != 200 for o in ordered)','or any(o["raw"]["status"] != 200 for o in ordered[1:])')
new=new.replace('            if replacement.result is not Result.SATISFIED or verdict.result is not Result.VIOLATED:\n                return None','            expected_pair = (\n                (Result.UNKNOWN, Result.UNKNOWN) if resource_unavailable\n                else (Result.SATISFIED, Result.VIOLATED)\n            )\n            if (replacement.result, verdict.result) != expected_pair:\n                return None')
new=new.replace('        if chain:\n            body["mechanism"]','        if resource_unavailable:\n            body["version"] = "phase85-slot616-declared-resource-absence-v1"\n            body["declared_resource_lookup_absent"] = True\n        if chain:\n            body["mechanism"]')
assert old!=new
(folder/'refusal.py').write_text(new,encoding='utf-8',newline='\n')
(folder/'refusal.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='frozen-v10/refusal.py',tofile='candidate616/refusal.py')),encoding='utf-8',newline='\n')
(folder/'parent.json').write_text(json.dumps({'frozen_package':'bcc12985051c93a2051dca8b0e69e28cad6dc35f39fef66f45e921a01a40790c','parent_refusal_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256((folder/'refusal.py').read_bytes()).hexdigest(),'deployed':False},indent=2),encoding='utf-8')
