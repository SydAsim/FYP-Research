"""No executed slots is an explicit retained result, never a successful campaign."""

from pathlib import Path

from postprocess import summarize


def test_all_unadmitted_slots_retained_without_inventing_measurements(tmp_path: Path) -> None:
    result = summarize(tmp_path / "root", tmp_path / "backup")
    assert result["planned_executions"] == len(result["slots"]) == 24
    assert all(s["state"] == "NOT_ADMITTED" and "measurement" not in s for s in result["slots"])
    assert sum(s["label"] == "PLANNED_SCHEDULE_REPEAT" for s in result["slots"]) == 6
    assert result["serial_1500_reference_hours"] is None
    assert result["main_inferential_inputs"] == 0 and result["main_started"] is False
