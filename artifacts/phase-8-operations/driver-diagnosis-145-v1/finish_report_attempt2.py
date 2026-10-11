"""Retain first report attempt; read nested freeze paths with Windows long paths."""
import importlib.util
import json
import sys
from pathlib import Path

here = Path(__file__).parent
spec = importlib.util.spec_from_file_location("diagnostic_report", here / "finish_report.py")
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
original_sha = module.sha
original_save = module.save

def long_sha(path: Path) -> str:
    if sys.platform == "win32":
        path = Path("\\\\?\\" + str(path.resolve()))
    return original_sha(path)

def retained_save(name: str, value: object) -> None:
    path = here / name
    if path.exists():
        assert json.loads(path.read_text()) == value
        return
    original_save(name, value)

module.sha = long_sha
module.save = retained_save
# Preserve the identical already-written excerpt by using a separate attempt
# directory for regenerated reports; source and frozen paths stay unchanged.
report = here / "attempt2"
report.mkdir(exist_ok=False)
module.HERE = report
with (report / "original145-receipt.json").open("xb") as target:
    target.write((here / "original145-receipt.json").read_bytes())
module.REPO = here.parents[2]
module.main()
