"""Recorded single-send transport; never automatically resends a mutation."""
from __future__ import annotations
import importlib.util,json,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'v11-stop-1297/continuation-v12/ops.py'
spec=importlib.util.spec_from_file_location('prior_ops',PRIOR)
assert spec and spec.loader
ops=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)
ops.HERE=HERE
ops.r.HERE=HERE

def main():
    ops.main()

if __name__=='__main__':
    main()
