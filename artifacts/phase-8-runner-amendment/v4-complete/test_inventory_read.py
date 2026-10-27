from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest
from botocore.exceptions import ClientError, ConnectionClosedError
from inventory_read import InventoryUnavailable, bounded_inventory, read_inventory


class Stub:
    def __init__(self, values: list[Any]) -> None:
        self.values = iter(values)
        self.calls: list[dict[str, Any]] = []

    def list_object_versions(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        value = next(self.values)
        if isinstance(value, Exception):
            raise value
        return dict(value)


def page(size: int = 7, *, truncated: bool = False) -> dict[str, Any]:
    value: dict[str, Any] = {
        "IsTruncated": truncated,
        "Versions": [{"Key": "cal/item", "VersionId": "v1", "Size": size}],
    }
    if truncated:
        value.update(NextKeyMarker="cal/item", NextVersionIdMarker="v1")
    return value


def lost() -> ConnectionClosedError:
    return ConnectionClosedError(endpoint_url="https://offline-stub.invalid")


def test_connection_failure_then_success() -> None:
    client = Stub([lost(), page()])
    waits: list[float] = []
    assert read_inventory(client, "cal-only", "cal/", sleep=waits.append) == 7
    assert len(client.calls) == 2 and waits == [1]


def test_retry_exhaustion_has_no_total() -> None:
    client = Stub([lost(), lost(), lost()])
    waits: list[float] = []
    with pytest.raises(InventoryUnavailable, match="RETRY_EXHAUSTED"):
        read_inventory(client, "cal-only", "cal/", sleep=waits.append)
    assert len(client.calls) == 3 and waits == [1, 2]


def test_later_page_failure_restarts_whole_listing() -> None:
    second = page(11)
    second["Versions"][0].update(Key="cal/next", VersionId="v2")
    client = Stub([page(999, truncated=True), lost(), page(7, truncated=True), second])
    assert read_inventory(client, "cal-only", "cal/", sleep=lambda _: None) == 18
    assert "KeyMarker" in client.calls[1] and "KeyMarker" not in client.calls[2]


def test_later_page_exhaustion_never_returns_partial() -> None:
    client = Stub([page(truncated=True), lost()] * 3)
    with pytest.raises(InventoryUnavailable, match="RETRY_EXHAUSTED"):
        read_inventory(client, "cal-only", "cal/", sleep=lambda _: None)
    assert len(client.calls) == 6


@pytest.mark.parametrize("code", ["AccessDenied", "NoSuchBucket", "InvalidArgument"])
def test_non_retryable_service_error(code: str) -> None:
    error = ClientError(
        {
            "Error": {"Code": code, "Message": "offline"},
            "ResponseMetadata": {"HTTPStatusCode": 500},
        },
        "ListObjectVersions",
    )
    client = Stub([error])
    waits: list[float] = []
    with pytest.raises(ClientError):
        read_inventory(client, "cal-only", "cal/", sleep=waits.append)
    assert len(client.calls) == 1 and not waits


def test_missing_completion_flag_is_not_zero_usage() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        read_inventory(Stub([{}]), "cal-only", "cal/")


def test_missing_pagination_marker_pauses() -> None:
    value = page()
    value["IsTruncated"] = True
    with pytest.raises(InventoryUnavailable, match="INCOMPLETE_PAGINATION"):
        read_inventory(Stub([value]), "cal-only", "cal/")


def test_repeated_marker_pauses() -> None:
    value = page(truncated=True)
    value["Versions"] = []
    with pytest.raises(InventoryUnavailable, match="REPEATED_PAGINATION"):
        read_inventory(Stub([value, value]), "cal-only", "cal/")


def test_delete_marker_boundary_and_complete_empty_page() -> None:
    value = {"IsTruncated": True, "NextKeyMarker": "cal/deleted", "DeleteMarkers": []}
    client = Stub([value, {"IsTruncated": False}])
    assert read_inventory(client, "cal-only", "cal/") == 0
    assert client.calls[-1]["KeyMarker"] == "cal/deleted"
    assert "VersionIdMarker" not in client.calls[-1]


def test_total_budget_blocks_more_attempts() -> None:
    ticks = [0.0]

    def sleep(seconds: float) -> None:
        ticks[0] += seconds

    client = Stub([lost(), lost()])
    with pytest.raises(InventoryUnavailable, match="TOTAL_TIME_LIMIT"):
        read_inventory(client, "cal-only", "cal/", clock=lambda: ticks[0], sleep=sleep, seconds=2)
    assert len(client.calls) == 2 and ticks[0] == 1


def test_hard_parent_deadline_kills_stalled_read(tmp_path: Path, monkeypatch: Any) -> None:
    import inventory_read

    script = tmp_path / "blocked-read.py"
    script.write_text("import time; time.sleep(5)")
    monkeypatch.setattr(inventory_read, "__file__", str(script))
    started = time.monotonic()
    with pytest.raises(InventoryUnavailable, match="TOTAL_TIME_LIMIT"):
        bounded_inventory("cal-only", "cal/", seconds=0.05)
    assert time.monotonic() - started < 1


def test_inventory_delegate_does_not_use_upload_client(monkeypatch: Any) -> None:
    import inventory_read
    from storage import S3Cloud

    cloud = object.__new__(S3Cloud)
    cloud.bucket = "cal-only"
    cloud.prefix = "cal/"
    cloud.client = object()
    monkeypatch.setattr(inventory_read, "bounded_inventory", lambda b, p: 123)
    assert cloud.inventory() == 123


def test_unavailable_inventory_durably_pauses_without_admission(
    tmp_path: Path, monkeypatch: Any
) -> None:
    import runner
    from controls import Journal, read, utc
    from test_controls import calibration, sample

    root, authority = calibration(tmp_path)

    class Unavailable:
        def inventory(self) -> int:
            raise InventoryUnavailable("S3_INVENTORY_RETRY_EXHAUSTED")

    monkeypatch.setattr(runner, "cloud_for", lambda _: Unavailable())
    monkeypatch.setattr(runner, "meter", lambda _: sample())
    monkeypatch.setattr(sys, "argv", ["runner.py", "watchdog", "--root", str(root)])
    with pytest.raises(SystemExit) as result:
        runner.main()
    assert result.value.code == 1 and read(root / "pause.json")["reason"] == "PROTOCOL_STOP"
    assert all(r["state"] == "PLANNED" for r in Journal(root).rows())
    with pytest.raises(ValueError, match="PAUSED_ADMISSIONS"):
        Journal(root).admit(authority, sample(), utc(), 0)


def test_unverified_child_result_is_rejected(monkeypatch: Any) -> None:
    import inventory_read

    monkeypatch.setattr(
        inventory_read.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, json.dumps({"bytes": 0}), ""),
    )
    with pytest.raises(InventoryUnavailable, match="INVALID_COMPLETE_RESULT"):
        bounded_inventory("cal-only", "cal/")
