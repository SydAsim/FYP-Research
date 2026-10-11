import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'phase-8-continuation-deployment/v3'))
import ops
p=HERE/'pattern-inspection-lf.sh'
t=p.read_text().replace('pattern-inspection-20261008-1','pattern-inspection-20261008-2')
t=t.replace("verify_local(Path(p['local']),p['sha256']);cloud.verify(ObjectProof.model_validate(p['cloud']))", "local=Path(p['local']) if r['sequence']>2 else root.parent/'retained'/('first' if r['sequence']==1 else 'second')/'t/e.tar.gz'\n verify_local(local,p['sha256']);cloud.verify(ObjectProof.model_validate(p['cloud']))")
q=HERE/'pattern-inspection-attempt2.sh'
with q.open('xb') as f:f.write(t.encode())
print(ops.send(q,'pattern-observation-2')['Command']['CommandId'])
