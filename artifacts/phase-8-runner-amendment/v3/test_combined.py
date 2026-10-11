"""Finite offline request-path and real retained-metadata qualification."""

from __future__ import annotations

import copy
import io
import json
import os
import shutil
from email.message import Message
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from uuid import uuid4

import collector
import pytest
from controls import Journal, hash_file, read, utc
from handover import ro_rows, stage, verify_imported_first
from pydantic import ValidationError
from response_guard import evaluate, finish_driver
from runner import prepare_slot
from test_controls import calibration, sample
from two_originals import boundary, original_proof

import research.study_v4.calibration as adapter
from research.execution_setup.core import Ledger

HERE = Path(__file__).resolve().parent
MASTER = Path(os.getenv("P85_MASTER", "C:/p8c1/m/x/slot"))
FIRST = Path(os.getenv("P85_FIRST", "C:/fyp-p85/stopped-attempt1/slot1/x/slot"))
SECOND = Path(os.getenv("P85_SECOND", "C:/p8c1/s/x/slot"))
ARCHIVES = (
    Path(os.getenv("P85_FIRST_ARCHIVE", "C:/fyp-p85/stopped-attempt1/slot1/t/e.tar.gz")),
    Path(os.getenv("P85_SECOND_ARCHIVE", "C:/p8c1/s/t/e.tar.gz")),
)
SERVICES = {
    k: str(getattr(adapter, n))
    for k, n in (("api", "API"), ("voice", "VOICE"), ("simulator", "SIMULATOR"))
}
RECORDS = [
    r
    for r in read(HERE / "recorded-response-inventory.json")
    if r["family"]
    in {"verified-stale-attempt", "queued-stale", "buffered-stale", "version-change-before-start"}
]


@pytest.mark.parametrize("index", range(len(RECORDS)))
def test_recorded_context_expected_refusals(index: int) -> None:
    record = RECORDS[index]
    row, call = record["row"], record["call"]
    result = evaluate(
        row, call, scenario=row["scenario_id"], item=row["fixture_identity"], services=SERVICES
    )
    assert result["classification"].startswith("EXPECTED_"), result


@pytest.mark.parametrize("arm", ["B3", "P1", "P2"])
@pytest.mark.parametrize("status", [409, 500])
def test_six_unexpected_http_responses_persist_even_if_driver_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, arm: str, status: int
) -> None:
    root, authority = calibration(tmp_path)
    slot = Journal(root).admit(authority, sample(), utc(), 0)
    assert slot is not None
    folder = prepare_slot(root, slot)
    ledger = Ledger(folder)
    record = copy.deepcopy(
        next(r for r in RECORDS if r["family"] == "buffered-stale" and r["arm"] == arm)
    )
    trial = collector.Trial.__new__(collector.Trial)
    trial.row, trial.item, trial.scenario = (
        record["row"],
        record["row"]["fixture_identity"],
        record["row"]["scenario_id"],
    )
    trial.ledger, trial.slot, trial.id = ledger, slot, slot["execution_id"]
    trial.execution_directory = folder / "executions" / trial.id
    trial.path = trial.execution_directory / "checkpoint.json"
    # Preserve recorded pre-call context but no later successful steps.
    call = record["call"]
    trial.row["http"] = [c for c in trial.row["http"] if c["received_at"] <= call["sent_at"]]
    path = call["path"]
    body = {
        "type": "https://example.invalid/problems/calibration-unrecognized-defect",
        "title": "Unrecognized injected defect",
        "status": status,
        "detail": "No declared scenario authorizes this problem",
        "instance": path,
        "trace_id": str(uuid4()),
        "retryable": False,
    }

    def fail(request: Any, **kwargs: Any) -> Any:
        raise HTTPError(
            request.full_url, status, "control", Message(), io.BytesIO(json.dumps(body).encode())
        )

    monkeypatch.setattr(adapter, "urlopen", fail)
    returned = trial.request(SERVICES["api"], "POST", path, call["request"], allow_failure=True)
    assert returned == body
    assert trial.row["permissive_response_errors"][0]["response"] == body
    assert read(root / "pause.json")["reason"] == "UNEXPECTED_PERMISSIVE_RESPONSE"
    trial.row["status"] = "COMPLETED"  # Later ordinary update cannot hide it.
    finish_driver(trial)
    trial.row["driver_finished_at"] = utc().isoformat()
    trial.save()
    assert trial.row["status"] == "FAILED" and "driver_classification" not in trial.row
    recovered = ledger.recover_checkpoint(trial.id)
    assert recovered["failure"]["type"] == "UNEXPECTED_PERMISSIVE_RESPONSE"
    # Existing active slot can finish collection/backup; closed slot cannot admit next.
    from controls import write_new
    from storage import complete_backup, make_backup

    for name in ("resources.json", "source-seal.json"):
        if not (folder / name).exists():
            write_new(folder / name, {"scope": "CALIBRATION_CONTROL_NO_PG_DUMPS"})
    exported = trial.execution_directory / "export.json"
    write_new(exported, trial.row)
    ledger.seal(exported)
    Journal(root).update(trial.id, state="EXPORTED")
    archive = make_backup(folder, tmp_path / "backup", dumps=False)
    complete_backup(
        Journal(root),
        __import__("storage").OfflineCloud(tmp_path / "remote-copy"),
        authority.policy,
        slot,
        archive,
    )
    assert Journal(root).rows()[0]["state"] == "BACKED_UP"
    with pytest.raises(ValueError, match="PAUSED"):
        Journal(root).admit(authority, sample(), utc(), 0)
    with pytest.raises(ValueError, match="NO_AUTO_UNPAUSE"):
        Journal(root).resume()
    ledger.verify()
    Journal(root).verify()


@pytest.mark.parametrize(
    "response",
    [
        {"detail": "Unknown barrier"},
        {"detail": "Unknown scenario"},
        {"detail": "Internal Server Error"},
    ],
)
def test_barrier_404_requires_declared_endpoint_and_exact_body(response: dict[str, str]) -> None:
    row = copy.deepcopy(RECORDS[0]["row"])
    row["input"]["provider"]["held_barriers"] = ["AFTER_COMMIT_BEFORE_RESPONSE"]
    scenario = row["scenario_id"]
    call: dict[str, Any] = {
        "base": SERVICES["simulator"],
        "method": "GET",
        "path": f"/internal/scenarios/{scenario}/barriers/AFTER_COMMIT_BEFORE_RESPONSE",
        "request": None,
        "response": response,
        "status": 404,
        "sent_at": utc().isoformat(),
        "received_at": utc().isoformat(),
    }
    result = evaluate(row, call, scenario=scenario, item=row["fixture_identity"], services=SERVICES)
    assert (result["classification"] == "EXPECTED_BARRIER_POLL") == (
        response == {"detail": "Unknown barrier"}
    )
    call["path"] = call["path"].replace(scenario, str(uuid4()))
    assert (
        evaluate(row, call, scenario=scenario, item=row["fixture_identity"], services=SERVICES)[
            "classification"
        ]
        == "UNEXPECTED_RESPONSE"
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "family",
        "request",
        "type",
        "detail",
        "retryable",
        "instance",
        "trace",
        "no-correction",
        "status",
    ],
)
def test_known_409_is_not_a_whitelist(mutation: str) -> None:
    r = copy.deepcopy(
        next(r for r in RECORDS if r["family"] == "buffered-stale" and r["arm"] == "P1")
    )
    row, call = r["row"], r["call"]
    if mutation == "family":
        row["input"]["generator_family"] = "clean-Asia/Karachi-30"
    elif mutation == "request":
        call["request"]["segment_id"] = str(uuid4())
    elif mutation == "no-correction":
        row["http"] = [c for c in row["http"] if not c["path"].endswith("/revisions")]
    elif mutation == "status":
        call["status"] = 500
    else:
        call["response"][{"trace": "trace_id"}.get(mutation, mutation)] = (
            True if mutation == "retryable" else "changed"
        )
    assert (
        evaluate(
            row, call, scenario=row["scenario_id"], item=row["fixture_identity"], services=SERVICES
        )["classification"]
        == "UNEXPECTED_RESPONSE"
    )


def test_baseline_version_changed_positive_start_is_an_observable_result() -> None:
    r = copy.deepcopy(next(r for r in RECORDS if r["family"] == "version-change-before-start"))
    row, call = r["row"], r["call"]
    row["arm"] = "B3"
    call.update(
        status=202,
        response={
            "event_id": call["request"]["event_id"],
            "segment_id": call["request"]["segment_id"],
            "state": "STARTED",
            "repair_obligation_id": None,
        },
    )
    assert (
        evaluate(
            row, call, scenario=row["scenario_id"], item=row["fixture_identity"], services=SERVICES
        )["classification"]
        == "OBSERVABLE_ACCEPTANCE"
    )


def test_provider_unavailability_does_not_masquerade_as_version_refusal() -> None:
    r = copy.deepcopy(next(r for r in RECORDS if r["family"] == "version-change-before-start"))
    row, call = r["row"], r["call"]
    row["snapshot"]["observations"] = []
    assert (
        evaluate(
            row, call, scenario=row["scenario_id"], item=row["fixture_identity"], services=SERVICES
        )["classification"]
        == "UNEXPECTED_RESPONSE"
    )


@pytest.mark.parametrize(
    "kind", ["CONTINUATION_ACCEPTED", "CONTINUATION_FREEZE", "CONTINUATION_LAUNCH"]
)
def test_previous_one_original_receipts_do_not_authorize_this_candidate(kind: str) -> None:
    from handover import ContinuationReceipt

    old = read(SECOND / "master/public-authority/continuation" / (kind + ".json"))
    with pytest.raises(ValidationError):
        ContinuationReceipt.model_validate(old)


@pytest.mark.parametrize("changed", ["event_id", "segment_id"])
def test_positive_status_with_wrong_playback_binding_is_a_defect(changed: str) -> None:
    r = copy.deepcopy(next(r for r in RECORDS if r["family"] == "version-change-before-start"))
    row, call = r["row"], r["call"]
    row["arm"] = "B3"
    response = {
        "event_id": call["request"]["event_id"],
        "segment_id": call["request"]["segment_id"],
        "state": "STARTED",
        "repair_obligation_id": None,
    }
    response[changed] = str(uuid4())
    call.update(status=202, response=response)
    assert (
        evaluate(
            row, call, scenario=row["scenario_id"], item=row["fixture_identity"], services=SERVICES
        )["classification"]
        == "UNEXPECTED_RESPONSE"
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "attempt",
        "identity",
        "order",
        "active",
        "deadline",
        "backup",
        "first-open",
        "second-open",
    ],
)
def test_closed_two_original_boundary_rejects_changes(mutation: str) -> None:
    saved = read(HERE / "saved-identities.json")["rows"]
    rows = copy.deepcopy(saved)
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[2]["execution_id"] = rows[0]["execution_id"]
    elif mutation == "attempt":
        rows[2]["attempt"] = 2
    elif mutation == "identity":
        rows[2]["execution_id"] = str(uuid4())
    elif mutation == "order":
        rows[2], rows[3] = rows[3], rows[2]
    elif mutation == "active":
        rows[2]["state"] = "RUNNING"
    elif mutation == "deadline":
        rows[2]["deadline"] = utc().isoformat()
    elif mutation == "backup":
        rows[1]["backup_hash"] = None
    elif mutation == "first-open":
        rows[0]["state"] = "EXPORTED"
    else:
        rows[1]["state"] = "RUNNING"
    with pytest.raises(ValueError):
        boundary(rows, saved)


def test_real_two_original_import(tmp_path: Path) -> None:
    root = tmp_path / "import"
    result = stage(
        MASTER, FIRST, root, second=SECOND, first_archive=ARCHIVES[0], second_archive=ARCHIVES[1]
    )
    verify_imported_first(root)
    rows = ro_rows(root)
    assert len(rows) == 1500 and sum(r["state"] == "BACKED_UP" for r in rows) == 2
    assert sum(r["state"] == "PLANNED" for r in rows) == 1498 and rows[2]["arm"] == "P2"
    assert result["driver_calls"] == 0 and not result["old_application_state_restored"]
    assert not (root / "slots").exists() and not (root / "host-clock.json").exists()
    for label, original in [("first-slot", FIRST), ("second-slot", SECOND)]:
        files = read(original / "manifest.json")["files"]
        assert all(
            hash_file(root / "historical" / label / name) == digest
            for name, digest in files.items()
        )
    assert read(root / "pause.json")["reason"] == "CONTINUATION_REVIEW_REQUIRED"
    recovered = tmp_path / "packed-recovery"
    recovered.mkdir()
    for name in (
        "campaign.sqlite3",
        "saved-identities.json",
        "handover.json",
        "historical-evidence.tar.gz",
    ):
        shutil.copyfile(root / name, recovered / name)
    shutil.copytree(root / "backups", recovered / "backups")
    assert not (recovered / "historical").exists()
    verify_imported_first(recovered)
    assert not (recovered / "slots").exists() and not (recovered / "host-clock.json").exists()
    from imported_analysis import imported_row

    for slot in rows[:2]:
        analysis, provenance = imported_row(root, slot["execution_id"])
        assert analysis.values["correction_success"] == "TRUE"
        assert analysis.values["correct_final_update"] == "FALSE"
        assert analysis.duration_seconds == 600 and analysis.event_observed is False
        assert analysis.censor_reason == "NO_SUPPORTED_COMPLETION"
        assert (
            provenance["raw_status"] == "FAILED" and not provenance["replacement_or_driver_replay"]
        )
    with pytest.raises(ValueError, match="RETAIN_ATTEMPTS"):
        stage(
            MASTER,
            FIRST,
            root,
            second=SECOND,
            first_archive=ARCHIVES[0],
            second_archive=ARCHIVES[1],
        )
    (root / "historical/timing-sidecars/second-original-proposed-sidecar.json").write_text(
        "altered"
    )
    with pytest.raises(ValueError, match="HISTORY_DRIFT"):
        verify_imported_first(root)


@pytest.mark.parametrize("mutation", ["missing-dump", "archive", "sidecar", "receipt"])
def test_incomplete_original_backup_rejected(tmp_path: Path, mutation: str) -> None:
    master, second = tmp_path / "master", tmp_path / "second"
    shutil.copytree(MASTER, master)
    shutil.copytree(SECOND, second)
    slot = ro_rows(master)[1]
    side = tmp_path / "sidecar.json"
    shutil.copyfile(HERE / "second-original-proposed-sidecar.json", side)
    archive = tmp_path / "archive.tar.gz"
    shutil.copyfile(ARCHIVES[1], archive)
    if mutation == "missing-dump":
        (second / "setup_truth.sql.gz").unlink()
    elif mutation == "archive":
        archive.write_bytes(archive.read_bytes()[:-8])
    elif mutation == "sidecar":
        side.write_text(side.read_text().replace("NO_SUPPORTED_COMPLETION", "INVALID"))
    else:
        receipt = master / "backups" / (slot["execution_id"] + ".json")
        data = read(receipt)
        data["cloud"]["version_id"] = None
        receipt.write_text(json.dumps(data))
    from two_originals import SECOND_HASH

    with pytest.raises((ValueError, OSError, EOFError)):
        original_proof(master, second, archive, slot, side, SECOND_HASH)
