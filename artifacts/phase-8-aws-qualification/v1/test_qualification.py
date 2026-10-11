"""Reject false readiness from failed or incomplete real-window exports."""

import importlib.util
from pathlib import Path
from typing import Any

import pytest

from research.execution_setup.core import digest, immutable


def verifier() -> Any:
    path = Path(__file__).with_name("qualify.py")
    spec = importlib.util.spec_from_file_location("aws_qualification", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.verify_export


@pytest.mark.parametrize(
    ("change", "error"),
    [
        ({"status": "FAILED"}, "DRIVER_NOT_COMPLETED"),
        ({"status": "TIMEOUT"}, "DRIVER_NOT_COMPLETED"),
        ({"oracle_failure": {"detail": "independent truth unavailable"}}, "PROTOCOL_FAILURE"),
        ({"collection_errors": [{"detail": "truth query lost"}]}, "PROTOCOL_FAILURE"),
        ({"missing_final_anchor": True}, "FULL_FINAL_REQUEST_WINDOW"),
        ({"polls": [{"at": "2026-10-05T17:09:59+00:00"}]}, "FULL_FINAL_REQUEST_WINDOW"),
    ],
)
def test_incomplete_attempt_cannot_become_readiness_pass(
    tmp_path: Path, change: dict[str, Any], error: str
) -> None:
    slot = {
        "state": "EXPORTED",
        "execution_id": "original",
        "deadline": "2026-10-05T17:10:00+00:00",
        "case_id": "cal-v4-only",
        "arm": "P2",
    }
    path = tmp_path / "executions/original/export.json"
    trace = {
        "status": "COMPLETED",
        "missing_final_anchor": False,
        "polls": [{"at": "2026-10-05T17:10:00+00:00"}],
        **change,
    }
    immutable(path, trace)
    original_hash = digest(path)
    with pytest.raises(ValueError, match=error):
        verifier()(tmp_path, slot)
    assert digest(path) == original_hash


def test_complete_window_uses_original_anchor_and_retains_outcome(tmp_path: Path) -> None:
    slot = {
        "state": "EXPORTED",
        "execution_id": "original",
        "deadline": "2026-10-05T17:10:00+00:00",
        "case_id": "cal-v4-only",
        "arm": "B3",
    }
    path = tmp_path / "executions/original/export.json"
    immutable(
        path,
        {
            "status": "COMPLETED",
            "missing_final_anchor": False,
            "polls": [{"at": "2026-10-05T17:09:55+00:00"}, {"at": "2026-10-05T17:10:01+00:00"}],
            "revised_grade": {"claim_truth": "UNKNOWN"},
            "resource_start": {},
            "resource_end": {},
        },
    )
    original_hash = digest(path)
    result = verifier()(tmp_path, slot)
    assert result["execution_id"] == "original" and result["deadline"] == slot["deadline"]
    assert result["deadline_overshoot_seconds"] == 1
    assert result["grade"]["claim_truth"] == "UNKNOWN"
    assert result["export_hash"] == original_hash == digest(path)
