"""Metadata-only two-original handover; all historical bytes remain immutable."""

from __future__ import annotations

import shutil
import tarfile
import time
from pathlib import Path
from typing import Any

from controls import Journal, hash_file, read, write_new

SECOND = "01a11705-11f0-7826-bd9d-9066d82c4452"
SECOND_HASH = "bd4d32f4968eaff243d65d9cfe8fad36c603cd709c09ee7fdebd29746e90da42"
NEXT = "01a11705-11f0-7a68-8c68-4da5c8126c84"
IMMEDIATE_PARENT = "4b921d416b9111594531ca33f26b1b307e04b22241ef995b6e571ce96a21f3e7"
IDENTITY = ("sequence", "case_id", "arm", "attempt", "execution_id", "fixture_hash")


def boundary(rows: list[dict[str, Any]], saved: list[dict[str, Any]]) -> None:
    from handover import FIRST

    if len(rows) != 1500 or len(saved) != 1500:
        raise ValueError("EXACT_1500_ORIGINALS_REQUIRED")
    if len({r["execution_id"] for r in rows}) != 1500 or any(
        any(a[k] != b[k] for k in IDENTITY) for a, b in zip(rows, saved, strict=True)
    ):
        raise ValueError("SAVED_IDENTITY_ORDER_OR_ATTEMPT_DRIFT")
    if [r["execution_id"] for r in rows[:3]] != [FIRST, SECOND, NEXT]:
        raise ValueError("ORIGINALS_OR_NEXT_P2_DRIFT")
    if any(
        r["state"] != "BACKED_UP" or not r["backup_hash"] or not r["deadline"] for r in rows[:2]
    ):
        raise ValueError("TWO_ORIGINALS_NOT_BACKED_UP")
    if any(
        r["state"] != "PLANNED"
        or any(r[k] is not None for k in ("deadline", "backup_hash", "error"))
        for r in rows[2:]
    ):
        raise ValueError("ACTIVE_OR_CHANGED_SLOT_NO_COLD_HANDOVER")


def original_proof(
    master: Path, folder: Path, archive: Path, slot: dict[str, Any], sidecar: Path, expected: str
) -> dict[str, Any]:
    from handover import FIRST, HERE, verify_members
    from storage import verify_local

    verify_members(folder)
    manifest = read(folder / "manifest.json")
    if manifest.get("postgres_dumps") is not True or not {
        "setup_app.sql.gz",
        "setup_truth.sql.gz",
    }.issubset(manifest["files"]):
        raise ValueError("INCOMPLETE_POSTGRES_BACKUP")
    exported = folder / "executions" / slot["execution_id"] / "export.json"
    raw = read(exported)
    if (
        hash_file(exported) != expected
        or raw["status"] != "FAILED"
        or raw["execution_id"] != slot["execution_id"]
        or raw["attempt"] != slot["attempt"]
        or raw["arm"] != slot["arm"]
    ):
        raise ValueError("ORIGINAL_EXPORT_IDENTITY_OR_GRADE_DRIFT")
    receipt_path = master / "backups" / (slot["execution_id"] + ".json")
    receipt = read(receipt_path)
    cloud = receipt["cloud"]
    if (
        hash_file(receipt_path) != slot["backup_hash"]
        or receipt["execution_id"] != slot["execution_id"]
        or not cloud.get("version_id")
        or not cloud.get("bucket")
        or not cloud.get("key")
        or cloud["sha256"] != receipt["sha256"]
        or cloud["bytes"] != archive.stat().st_size
    ):
        raise ValueError("INCOMPLETE_OR_ALTERED_BACKUP_RECEIPT")
    verify_local(archive, receipt["sha256"])
    import json
    import tarfile

    with tarfile.open(archive, "r:gz") as incoming:
        stream = incoming.extractfile("slot/manifest.json")
        if stream is None or json.load(stream) != manifest:
            raise ValueError("ARCHIVE_EXTRACTION_MANIFEST_DRIFT")
    side = read(sidecar)
    pinned_side = HERE / (
        "first-original-proposed-sidecar.json"
        if slot["execution_id"] == FIRST
        else "second-original-proposed-sidecar.json"
    )
    if hash_file(sidecar) != hash_file(pinned_side):
        raise ValueError("TIMING_SIDECAR_HASH_DRIFT")
    if (
        side["execution_id"] != slot["execution_id"]
        or side["attempt"] != slot["attempt"]
        or side["original_export_sha256"] != expected
        or side["raw_status"] != "FAILED"
        or side["original_stored_analysis"] != raw["analysis_row"]
        or side["original_stored_grades"]["revised_grade"] != raw["revised_grade"]
        or not side["business_and_speech_outcome_values_unchanged"]
    ):
        raise ValueError("TIMING_SIDECAR_DRIFT")
    return {
        "execution_id": slot["execution_id"],
        "export_sha256": expected,
        "backup_receipt_sha256": hash_file(receipt_path),
        "archive_sha256": receipt["sha256"],
        "pinned_cloud": cloud,
        "sidecar_sha256": hash_file(sidecar),
        "raw_status": "FAILED",
    }


def stage(
    master: Path,
    first: Path,
    second: Path,
    first_archive: Path,
    second_archive: Path,
    destination: Path,
) -> dict[str, Any]:
    from handover import (
        FIRST_HASH,
        HERE,
        PARENT_FREEZE,
        RUN,
        original_policy,
        ro_rows,
        verify_members,
    )

    if destination.exists():
        raise ValueError("FRESH_IMPORT_ONLY_RETAIN_ATTEMPTS")
    master_proof = read(HERE / "retained-master-proof.json")
    if any(hash_file(master / name) != digest for name, digest in master_proof.items()):
        raise ValueError("RETAINED_MASTER_PROOF_DRIFT")
    verify_members(master)
    rows = ro_rows(master)
    saved = read(HERE / "saved-identities.json")["rows"]
    boundary(rows, saved)
    if rows != saved:
        raise ValueError("REVIEWED_CLOSED_BOUNDARY_DRIFT")
    config = read(master / "run.json")
    original_policy(config["policy"])
    bindings = read(master / "bindings.json")
    if bindings != [{k: r[k] for k in bindings[0]} for r in rows]:
        raise ValueError("ORIGINAL_BINDINGS_DRIFT")
    if read(master / "binding-seal.json") != {
        "run": hash_file(master / "run.json"),
        "bindings": hash_file(master / "bindings.json"),
    }:
        raise ValueError("ORIGINAL_BINDING_SEAL_DRIFT")
    sides = [
        HERE / "first-original-proposed-sidecar.json",
        HERE / "second-original-proposed-sidecar.json",
    ]
    proofs = [
        original_proof(master, f, a, s, side, digest)
        for f, a, s, side, digest in zip(
            (first, second),
            (first_archive, second_archive),
            rows[:2],
            sides,
            (FIRST_HASH, SECOND_HASH),
            strict=True,
        )
    ]
    # Every validation precedes the import. No services, DB restoration or driver exists here.
    destination.mkdir(parents=True)
    history = destination / "historical"
    for label, folder in (("master", master), ("first-slot", first), ("second-slot", second)):
        shutil.copytree(folder, history / label)
    for name in ("campaign.sqlite3", "bindings.json", "cloud.json"):
        shutil.copyfile(master / name, destination / name)
    shutil.copytree(master / "backups", destination / "backups")
    shutil.copyfile(HERE / "saved-identities.json", destination / "saved-identities.json")
    sides_dir = history / "timing-sidecars"
    sides_dir.mkdir()
    for side in sides:
        shutil.copyfile(side, sides_dir / side.name)
    # Retain the previously accepted first sidecar separately, with its own version.
    shutil.copyfile(
        HERE / "historical-accepted-first-v1.json",
        sides_dir / "historical-accepted-first-v1.json",
    )
    config.update(
        source="/opt/fyp-phase8-combined-v3",
        manifest="/opt/fyp-phase8-combined-v3/artifacts/phase-8-review-freeze/v2/review-inventory.json",
        backup="/var/lib/p8-combined/backup",
        continuation={
            "manifest": "artifacts/phase-8-runner-amendment/v3/candidate-inventory.json",
            "receipts": "/var/lib/fyp-owner/combined-v3-receipts",
        },
    )
    write_new(destination / "run.json", config)
    write_new(
        destination / "binding-seal.json",
        {
            "run": hash_file(destination / "run.json"),
            "bindings": hash_file(destination / "bindings.json"),
        },
    )
    record = {
        "version": "phase85-combined-amendment-v3",
        "kind": "CLOSED_TWO_ORIGINAL_METADATA_IMPORT_NOT_LAUNCH",
        "run_id": RUN,
        "originals": proofs,
        "planned": 1498,
        "backed_up": 2,
        "next_execution_id": NEXT,
        "source_ledger_sha256": hash_file(master / "campaign.sqlite3"),
        "saved_identities_sha256": hash_file(destination / "saved-identities.json"),
        "parent_freeze_sha256": PARENT_FREEZE,
        "immediate_parent_freeze_sha256": IMMEDIATE_PARENT,
        "history_files": {
            p.relative_to(history).as_posix(): hash_file(p)
            for p in history.rglob("*")
            if p.is_file()
        },
        "accepted": False,
        "frozen": False,
        "launch_authorized": False,
        "driver_calls": 0,
        "old_application_state_restored": False,
        "operational_clock_reset": False,
    }
    bundle = destination / "historical-evidence.tar.gz"
    with tarfile.open(bundle, "x:gz") as output:
        output.add(history, arcname="historical")
    record["historical_bundle_sha256"] = hash_file(bundle)
    write_new(destination / "handover.json", record)
    journal = Journal(destination)
    journal.verify()
    journal.event("CLOSED_TWO_ORIGINAL_IMPORT", proof=hash_file(destination / "handover.json"))
    journal.event(
        "BINDINGS_SEALED",
        run=hash_file(destination / "run.json"),
        bindings=hash_file(destination / "bindings.json"),
    )
    journal.pause("CONTINUATION_REVIEW_REQUIRED")
    verify(destination)
    return record


def verify(root: Path) -> None:
    from handover import FIRST_HASH, RUN, ro_rows

    record = read(root / "handover.json")
    if (
        record["run_id"] != RUN
        or record["immediate_parent_freeze_sha256"] != IMMEDIATE_PARENT
        or [p["export_sha256"] for p in record["originals"]] != [FIRST_HASH, SECOND_HASH]
    ):
        raise ValueError("HANDOVER_ORIGINAL_PROOF_DRIFT")
    history = root / "historical"
    bundle = root / "historical-evidence.tar.gz"
    if hash_file(bundle) != record["historical_bundle_sha256"]:
        raise ValueError("HISTORICAL_BUNDLE_DRIFT")
    if not history.exists():
        # Metadata/evidence materialization only: SQL files are never executed.
        # A partial extraction stays under its own attempt directory on any error.
        partial = root / ("historical-extract-" + str(time.time_ns()))
        partial.mkdir()
        with tarfile.open(bundle, "r:gz") as source:
            for name, digest in record["history_files"].items():
                member = source.getmember("historical/" + name)
                target = (partial / "historical" / name).resolve()
                if partial.resolve() not in target.parents or not member.isfile():
                    raise ValueError("UNSAFE_HISTORICAL_MEMBER")
                incoming = source.extractfile(member)
                if incoming is None:
                    raise ValueError("MISSING_HISTORICAL_MEMBER")
                data = incoming.read()
                import hashlib

                if hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError("HISTORICAL_BUNDLE_MEMBER_DRIFT")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        (partial / "historical").rename(history)
    from handover import HERE

    if any(
        hash_file(history / "master" / name) != digest
        for name, digest in read(HERE / "retained-master-proof.json").items()
    ):
        raise ValueError("RETAINED_MASTER_PROOF_DRIFT")
    for name, digest in record["history_files"].items():
        target = (history / name).resolve()
        if history.resolve() not in target.parents or hash_file(target) != digest:
            raise ValueError("HANDOVER_HISTORY_DRIFT")
    saved = read(root / "saved-identities.json")["rows"]
    if hash_file(root / "saved-identities.json") != record["saved_identities_sha256"]:
        raise ValueError("SAVED_IDENTITY_INVENTORY_DRIFT")
    rows = ro_rows(root)
    if (
        len(rows) != 1500
        or rows[:2] != saved[:2]
        or any(any(a[k] != b[k] for k in IDENTITY) for a, b in zip(rows, saved, strict=True))
    ):
        raise ValueError("IMPORTED_IDENTITY_DRIFT")
    import sqlite3

    def notices(folder: Path) -> list[tuple[Any, ...]]:
        uri = (folder / "campaign.sqlite3").resolve().as_uri() + "?mode=ro&immutable=1"
        with sqlite3.connect(uri, uri=True) as connection:
            return connection.execute("SELECT * FROM notices ORDER BY n").fetchall()

    original_notices = notices(history / "master")
    if notices(root)[: len(original_notices)] != original_notices:
        raise ValueError("HISTORICAL_NOTICE_PREFIX_DRIFT")
    for proof in record["originals"]:
        if (
            hash_file(root / "backups" / (proof["execution_id"] + ".json"))
            != proof["backup_receipt_sha256"]
        ):
            raise ValueError("IMPORTED_BACKUP_DRIFT")
