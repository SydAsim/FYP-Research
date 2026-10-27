"""Metadata-only handover of the pinned 38-original stopped boundary."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import sqlite3
import tarfile
import time
from pathlib import Path
from typing import Any

from controls import Journal, hash_file, read, write_new

HERE = Path(__file__).resolve().parent
PREFIX = "artifacts/phase-8-runner-amendment/v4-complete"
PARENT = "49ec78e719d9d28e017f62e6a40dd69cc236a45c5406d5be1a209ef59b9d2c86"
COUNT = 38
NEXT = "01a11705-11f0-73c0-af15-dd9f1d590b08"
IDENTITY = ("sequence", "case_id", "arm", "attempt", "execution_id", "fixture_hash")


def boundary(rows: list[dict[str, Any]], saved: list[dict[str, Any]]) -> None:
    if len(rows) != 1500 or len(saved) != 1500:
        raise ValueError("EXACT_1500_ORIGINALS_REQUIRED")
    if len({r["execution_id"] for r in rows}) != 1500 or any(
        any(a[k] != b[k] for k in IDENTITY) for a, b in zip(rows, saved, strict=True)
    ):
        raise ValueError("SAVED_IDENTITY_ORDER_OR_ATTEMPT_DRIFT")
    if rows[38]["execution_id"] != NEXT or rows[38]["arm"] != "B3":
        raise ValueError("NEXT_SEQUENCE_39_B3_DRIFT")
    if rows[:COUNT] != saved[:COUNT] or any(
        r["state"] != "BACKED_UP" or not r["backup_hash"] or not r["deadline"] for r in rows[:COUNT]
    ):
        raise ValueError("CLOSED_38_BACKUP_OR_OUTCOME_DRIFT")
    if any(
        r["state"] != "PLANNED"
        or any(r[k] is not None for k in ("deadline", "backup_hash", "error"))
        for r in rows[COUNT:]
    ):
        raise ValueError("ACTIVE_OR_CHANGED_SLOT_NO_COLD_HANDOVER")


def verify_master(master: Path) -> list[dict[str, Any]]:
    from handover import original_policy, ro_rows

    members = read(HERE / "retained-boundary-members.json")
    if read(master / "manifest.json")["files"] != members:
        raise ValueError("AUTHORITATIVE_BOUNDARY_MANIFEST_DRIFT")
    for name, expected in members.items():
        path = (master / name).resolve()
        if master.resolve() not in path.parents or hash_file(path) != expected:
            raise ValueError("AUTHORITATIVE_BOUNDARY_MEMBER_DRIFT: " + name)
    rows = ro_rows(master)
    boundary(rows, read(HERE / "saved-boundary.json")["rows"])
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
    return rows


def archive_proof(master: Path, proof: dict[str, Any]) -> None:
    identity = proof["identity"]
    receipt_file = master / "backups" / (identity["execution_id"] + ".json")
    receipt = read(receipt_file)
    cloud = receipt["cloud"]
    archive = HERE / proof["archive"]
    if (
        hash_file(receipt_file) != proof["receipt_sha256"]
        or receipt["execution_id"] != identity["execution_id"]
        or cloud != proof["cloud"]
        or not cloud.get("version_id")
        or receipt["sha256"] != cloud["sha256"]
        or archive.stat().st_size != cloud["bytes"]
        or hash_file(archive) != cloud["sha256"]
    ):
        raise ValueError("INCOMPLETE_OR_ALTERED_PINNED_BACKUP")
    with tarfile.open(archive) as incoming:
        manifest_stream = incoming.extractfile("slot/manifest.json")
        if manifest_stream is None:
            raise ValueError("MISSING_BACKUP_MANIFEST")
        raw_manifest = manifest_stream.read()
        manifest = json.loads(raw_manifest)
        if (
            hashlib.sha256(raw_manifest).hexdigest() != proof["manifest_sha256"]
            or manifest["files"] != proof["members"]
            or manifest.get("postgres_dumps") is not True
            or not {"setup_app.sql.gz", "setup_truth.sql.gz"}.issubset(manifest["files"])
        ):
            raise ValueError("INCOMPLETE_POSTGRES_BACKUP")
        for name, digest in manifest["files"].items():
            path = Path(name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("UNSAFE_BACKUP_MEMBER")
            member = incoming.getmember("slot/" + name)
            if not member.isfile():
                raise ValueError("BACKUP_MEMBER_NOT_REGULAR")
            stream = incoming.extractfile(member)
            assert stream is not None
            digest_value = hashlib.sha256()
            while block := stream.read(1024**2):
                digest_value.update(block)
            if digest_value.hexdigest() != digest:
                raise ValueError("PINNED_BACKUP_MEMBER_DRIFT")
        # Check compressed SQL integrity without loading either application database.
        for name in ("setup_app.sql.gz", "setup_truth.sql.gz"):
            stream = incoming.extractfile("slot/" + name)
            assert stream is not None
            with gzip.GzipFile(fileobj=stream) as dump:
                while dump.read(1024**2):
                    pass
    exported = master / "exports" / f"{identity['sequence']:04d}" / "export.json"
    raw = read(exported)
    if hash_file(exported) != proof["export_sha256"] or any(
        raw[k] != identity[k] for k in ("execution_id", "arm", "attempt", "fixture_hash")
    ):
        raise ValueError("ORIGINAL_EXPORT_IDENTITY_OR_GRADE_DRIFT")


def stage(master: Path, destination: Path) -> dict[str, Any]:
    from handover import PARENT_FREEZE, RUN

    if destination.exists():
        raise ValueError("FRESH_IMPORT_ONLY_RETAIN_ATTEMPTS")
    rows = verify_master(master)
    proofs = read(HERE / "retained-slot-proofs.json")
    if len(proofs) != COUNT or [p["identity"] for p in proofs] != [
        {k: r[k] for k in IDENTITY} for r in rows[:COUNT]
    ]:
        raise ValueError("EXACT_38_PINNED_BACKUPS_REQUIRED")
    for proof in proofs:
        archive_proof(master, proof)
    destination.mkdir(parents=True)
    history = destination / "historical"
    shutil.copytree(
        master, history / "boundary", ignore=shutil.ignore_patterns("authoritative-snapshot.tar.gz")
    )
    # Materialize just the first two raw archives for the accepted timing sidecars.
    for index, label in ((0, "first-slot"), (1, "second-slot")):
        target = history / label
        with tarfile.open(HERE / proofs[index]["archive"]) as incoming:
            incoming.extractall(target, filter="data")
        (target / "slot").rename(history / (label + "-materialized"))
        target.rmdir()
        (history / (label + "-materialized")).rename(target)
    sides = history / "timing-sidecars"
    sides.mkdir()
    for name in (
        "first-original-proposed-sidecar.json",
        "second-original-proposed-sidecar.json",
        "historical-accepted-first-v1.json",
    ):
        shutil.copyfile(HERE / name, sides / name)
    for name in ("campaign.sqlite3", "bindings.json", "cloud.json"):
        shutil.copyfile(master / name, destination / name)
    shutil.copytree(master / "backups", destination / "backups")
    shutil.copyfile(HERE / "saved-boundary.json", destination / "saved-identities.json")
    config = read(master / "run.json")
    config.update(
        source="/opt/fyp-phase8-combined-v4",
        manifest="/opt/fyp-phase8-combined-v4/artifacts/phase-8-review-freeze/v2/review-inventory.json",
        backup="/var/lib/p8-combined-v4/backup",
        continuation={
            "manifest": PREFIX + "/candidate-inventory.json",
            "receipts": "/var/lib/fyp-owner/combined-v4-receipts",
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
    original_proofs = []
    for index, proof in enumerate(proofs[:2]):
        original_proofs.append(
            {
                "execution_id": proof["identity"]["execution_id"],
                "export_sha256": proof["export_sha256"],
                "backup_receipt_sha256": proof["receipt_sha256"],
                "archive_sha256": proof["cloud"]["sha256"],
                "pinned_cloud": proof["cloud"],
                "sidecar_sha256": hash_file(
                    sides
                    / (("first" if index == 0 else "second") + "-original-proposed-sidecar.json")
                ),
                "raw_status": "FAILED",
            }
        )
    record = {
        "version": "phase85-complete-continuation-v4",
        "kind": "CLOSED_38_ORIGINAL_METADATA_IMPORT_NOT_LAUNCH",
        "run_id": RUN,
        "backed_up": COUNT,
        "planned": 1462,
        "next_execution_id": NEXT,
        "originals": original_proofs,
        "closed_originals": proofs,
        "source_ledger_sha256": hash_file(master / "campaign.sqlite3"),
        "saved_identities_sha256": hash_file(destination / "saved-identities.json"),
        "parent_freeze_sha256": PARENT_FREEZE,
        "immediate_parent_freeze_sha256": PARENT,
        "stopped_boundary_reference": read(HERE / "stopped-boundary-reference.json"),
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
    with tarfile.open(destination / "historical-evidence.tar.gz", "x:gz") as output:
        output.add(history, arcname="historical")
    record["historical_bundle_sha256"] = hash_file(destination / "historical-evidence.tar.gz")
    write_new(destination / "handover.json", record)
    journal = Journal(destination)
    journal.verify()
    journal.event("CLOSED_38_ORIGINAL_IMPORT", proof=hash_file(destination / "handover.json"))
    journal.event(
        "BINDINGS_SEALED",
        run=hash_file(destination / "run.json"),
        bindings=hash_file(destination / "bindings.json"),
    )
    journal.pause("CONTINUATION_REVIEW_REQUIRED")
    verify(destination)
    return record


def verify(root: Path) -> None:
    from handover import ro_rows

    record = read(root / "handover.json")
    if (
        record["immediate_parent_freeze_sha256"] != PARENT
        or record["closed_originals"] != read(HERE / "retained-slot-proofs.json")
        or record["stopped_boundary_reference"] != read(HERE / "stopped-boundary-reference.json")
    ):
        raise ValueError("HANDOVER_CLOSED_PREFIX_PROOF_DRIFT")
    bundle = root / "historical-evidence.tar.gz"
    if hash_file(bundle) != record["historical_bundle_sha256"]:
        raise ValueError("HISTORICAL_BUNDLE_DRIFT")
    history = root / "historical"
    if not history.exists():
        partial = root / ("historical-extract-" + str(time.time_ns()))
        partial.mkdir()
        with tarfile.open(bundle) as incoming:
            for name, digest in record["history_files"].items():
                path = (partial / "historical" / name).resolve()
                if partial.resolve() not in path.parents:
                    raise ValueError("UNSAFE_HISTORICAL_MEMBER")
                member = incoming.getmember("historical/" + name)
                if not member.isfile():
                    raise ValueError("HISTORICAL_MEMBER_NOT_REGULAR")
                stream = incoming.extractfile(member)
                assert stream is not None
                data = stream.read()
                if hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError("HISTORICAL_BUNDLE_MEMBER_DRIFT")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        (partial / "historical").rename(history)
    for name, digest in record["history_files"].items():
        path = (history / name).resolve()
        if history.resolve() not in path.parents or hash_file(path) != digest:
            raise ValueError("HANDOVER_HISTORY_DRIFT")
    saved = read(HERE / "saved-boundary.json")["rows"]
    if (
        hash_file(root / "saved-identities.json") != record["saved_identities_sha256"]
        or read(root / "saved-identities.json")["rows"] != saved
    ):
        raise ValueError("SAVED_IDENTITY_INVENTORY_DRIFT")
    rows = ro_rows(root)
    if (
        len(rows) != 1500
        or rows[:COUNT] != saved[:COUNT]
        or any(any(a[k] != b[k] for k in IDENTITY) for a, b in zip(rows, saved, strict=True))
    ):
        raise ValueError("IMPORTED_IDENTITY_DRIFT")

    # Live root may have a WAL. The notice prefix read itself uses one explicit snapshot.
    def notices(folder: Path) -> list[tuple[Any, ...]]:
        uri = (folder / "campaign.sqlite3").resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            connection.execute("BEGIN")
            return connection.execute("SELECT * FROM notices ORDER BY n").fetchall()

    original_notices = notices(history / "boundary")
    if notices(root)[: len(original_notices)] != original_notices:
        raise ValueError("HISTORICAL_NOTICE_PREFIX_DRIFT")
    for proof in record["closed_originals"]:
        if (
            hash_file(root / "backups" / (proof["identity"]["execution_id"] + ".json"))
            != proof["receipt_sha256"]
        ):
            raise ValueError("IMPORTED_BACKUP_DRIFT")


def imported(root: Path, execution_id: str) -> bool:
    """Only reviewed closed identities may skip local retirement/use historical analysis."""
    if not (root / "handover.json").exists():
        return False
    record = read(root / "handover.json")
    return execution_id in {p["identity"]["execution_id"] for p in record["closed_originals"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("stage", "verify"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--master", type=Path, default=HERE / "boundary")
    args = parser.parse_args()
    if args.action == "stage":
        stage(args.master.resolve(), args.root.resolve())
    else:
        verify(args.root.resolve())
    print("PASS: metadata only; no drivers, database restore, freeze or launch")


if __name__ == "__main__":
    main()
