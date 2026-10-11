"""Diagnostic labels govern eligibility; original failures cannot be dropped."""

import importlib.util
from pathlib import Path
from typing import Any

import pytest


def select() -> Any:
    spec = importlib.util.spec_from_file_location(
        "qualification_selection", Path(__file__).with_name("selection.py")
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.original_attempts


def test_legacy_misnumbered_diagnostic_cannot_replace_failed_original() -> None:
    failed = {
        "execution_id": "original",
        "attempt_label": "ORIGINAL_PLANNED",
        "attempt": 1,
        "original_id": None,
        "status": "FAILED",
    }
    diagnostic = {
        "execution_id": "diagnostic",
        "attempt_label": "DIAGNOSTIC_RERUN",
        "attempt": 1,
        "original_id": "original",
        "status": "COMPLETED",
    }
    originals, excluded = select()([failed, diagnostic])
    assert originals == [failed] and excluded == ["diagnostic"]


@pytest.mark.parametrize("label", [None, "UNKNOWN"])
def test_missing_label_is_a_defect_not_automatic_original(label: str | None) -> None:
    with pytest.raises(ValueError, match="AMBIGUOUS_ATTEMPT_METADATA"):
        select()([{"execution_id": "uncertain", "attempt": 1, "attempt_label": label}])
