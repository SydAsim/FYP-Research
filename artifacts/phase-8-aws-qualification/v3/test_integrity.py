"""Real file drift must block admission without modifying original slot outcomes."""

import importlib.util
from pathlib import Path
from typing import Any

import pytest

from research.execution_setup.core import Ledger, digest, load


def boundary() -> Any:
    path = Path(__file__).with_name("integrity.py")
    spec = importlib.util.spec_from_file_location("executing_integrity_v3", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("damage", ["code", "missing", "manifest"])
def test_executing_code_drift_stops_without_replacing_outcomes(tmp_path: Path, damage: str) -> None:
    code = tmp_path / "adapters/collector.py"
    code.parent.mkdir()
    code.write_text("ORIGINAL")
    root = tmp_path / "evidence"
    ledger = Ledger(root)
    with ledger.connect() as conn:
        conn.execute(
            "INSERT INTO slots(sequence,case_id,arm,state,attempt,label) VALUES (?,?,?,?,?,?)",
            (1, "cal-v4-only", "B3", "PLANNED", 1, "ORIGINAL_PLANNED"),
        )
    adapter = boundary()
    adapter.register(root, {str(code.resolve()): digest(code)}, ledger)
    adapter.verify(root)
    original_rows = ledger.rows()
    if damage == "code":
        code.write_text("CHANGED")
    elif damage == "missing":
        code.unlink()
    else:
        (root / "executing-adapters-seal.json").write_text('{"files":{}}')
    with pytest.raises(ValueError, match="HASH_DRIFT"):
        adapter.verify(root)
    assert ledger.rows() == original_rows
    assert load(root / "pause.json")["reason"] == "EXECUTING_ADAPTER_SOURCE_DRIFT"
    with ledger.connect() as conn:
        assert (
            "EXECUTING_ADAPTER_SOURCE_DRIFT"
            in conn.execute("SELECT body FROM events ORDER BY n DESC LIMIT 1").fetchone()[0]
        )
