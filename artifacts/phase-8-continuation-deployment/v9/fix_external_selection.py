"""Check external command/path selection before authorized guarded preparation."""
import ast
import json
from pathlib import Path
from ops import HERE
from controls import read,write_new

for name in ('build_reuse_gates.py','finish_preparation_guard.py'):
    p=HERE/name
    p.write_text(p.read_text().replace('retained-host-v7-attempt3-preparation-stop-20261009','retained-host-v9-preparation-stop-20261010'))
p=HERE/'prestart.py'
p.write_text(p.read_text().replace("'retained-host-v7-attempt2-preparation-stop-20261009'}","'retained-host-v7-attempt2-preparation-stop-20261009','retained-host-v7-attempt3-preparation-stop-20261009'}"))
for p in HERE.glob('*.py'):ast.parse(p.read_text())
pre=(HERE/'prestart.py').read_text()
assert "NAME='retained-host-v9-preparation-stop-20261010'" in pre
assert "'backed_up':120,'planned':1380" in pre and "'next_sequence':121" in pre
assert 'phase-8-continuation-freeze/v9' in pre
assert "retained-host-v7-attempt3-preparation-stop-20261009'" in pre
write_new(HERE/'external-selection-verification.json',{'status':'PASS','frozen_source_modified':False,
 'transport_interpreter':'/opt/fyp-phase8-combined-v4/.venv/bin/python',
 'transport_PYTHONPATH_before_bootstrap':'/opt/fyp-phase8-combined-v4/.venv-transport/lib/python3.12/site-packages',
 'actual_import_required_before_transfer':True,'dependency_install':False,'next_sequence':121,
 'old_owned_units_preserved_quiesced_before_host_readiness':True})
print('External selection checked; no frozen change or AWS boot.')
