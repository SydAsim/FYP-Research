"""Read-only final checks and admission-history index; never rerun a scenario."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from prepare_dataset import HERE, PACKAGE, SOURCE, canonical, read, sha

MASTER = Path("D:/FYP-ResearchBackups/final-status-20261025")


def instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> None:
    dataset = read(HERE / "dataset/verification.json")
    analysis = read(HERE / "analysis/verification.json")
    packet = read(HERE / "extraction-control.json")
    rows = json.loads((HERE / "dataset/analysis-rows.json").read_bytes())
    records = json.loads((HERE / "dataset/recorded-results.json").read_bytes())
    for name, expected in analysis["files"].items():
        if sha((HERE / "analysis" / name).read_bytes()) != expected:
            raise ValueError("ANALYSIS_OUTPUT_CHANGED:" + name)
    for name, key in (
        ("analysis-rows.json", "analysis_rows_sha256"),
        ("recorded-results.json", "recorded_results_sha256"),
        ("accepted-timing-rows.json", "accepted_timing_rows_sha256"),
    ):
        if sha((HERE / "dataset" / name).read_bytes()) != dataset[key]:
            raise ValueError("DATASET_CHANGED:" + name)
    inventory = read(
        SOURCE / "artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json"
    )
    if sha(canonical(inventory["files"])) != PACKAGE:
        raise ValueError("FROZEN_PACKAGE_BINDING_DRIFT")
    for name, expected in inventory["files"].items():
        if sha((SOURCE / name).read_bytes()) != expected:
            raise ValueError("FROZEN_SOURCE_CHANGED:" + name)
    with (HERE / "analysis/original-results.csv").open(encoding="utf-8", newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    if len(csv_rows) != 1500 or len(records) != 1500 or len(rows) != 1500:
        raise ValueError("FINAL_ORIGINAL_DENOMINATOR")
    for record, row, exported in zip(records, rows, csv_rows, strict=True):
        for key in ("sequence", "case_id", "arm", "attempt", "execution_id", "raw_status"):
            if exported[key] != str(record[key]):
                raise ValueError("CSV_IDENTITY_OR_STATUS_DRIFT:" + key)
        for key, value in row["values"].items():
            if exported[key] != value or value != record["values"][key]:
                raise ValueError("CSV_OUTCOME_DRIFT:" + key)
        if float(exported["duration_seconds"]) != row["duration_seconds"]:
            raise ValueError("CSV_TIMING_DRIFT")

    connection = sqlite3.connect(
        (MASTER / "campaign.sqlite3").resolve().as_uri() + "?mode=ro", uri=True
    )
    connection.row_factory = sqlite3.Row
    if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        raise ValueError("MASTER_SQLITE_INTEGRITY")
    slots = [dict(row) for row in connection.execute("SELECT * FROM slots ORDER BY sequence")]
    if len(slots) != 1500 or Counter(row["state"] for row in slots) != {"BACKED_UP": 1500}:
        raise ValueError("MASTER_NOT_COMPLETE")
    original_bindings = json.loads((MASTER / "bindings.json").read_bytes())
    fields = ("sequence", "case_id", "arm", "attempt", "execution_id", "fixture_hash")
    if original_bindings != [{key: row[key] for key in fields} for row in packet["identities"]]:
        raise ValueError("ORIGINAL_BINDING_FILE_DRIFT")
    for slot, identity in zip(slots, packet["identities"], strict=True):
        if any(slot[key] != identity[key] for key in fields):
            raise ValueError("LEDGER_IDENTITY_OR_SAVED_ORDER_DRIFT")
        if (
            slot["backup_hash"] != identity["backup_hash"]
            or slot["deadline"] != identity["deadline"]
        ):
            raise ValueError("LEDGER_BACKUP_OR_DEADLINE_DRIFT")

    previous = "GENESIS"
    notice_count = 0
    binding: dict[str, Any] | None = None
    admissions: dict[str, Any] = {}
    exported_at: dict[str, Any] = {}
    backed_at: dict[str, Any] = {}
    segments: list[dict[str, Any]] = []
    for n in connection.execute("SELECT body,previous,hash FROM notices ORDER BY n"):
        digest = hashlib.sha256((n["body"] + previous).encode()).hexdigest()
        if n["previous"] != previous or n["hash"] != digest:
            raise ValueError("MASTER_NOTICE_CHAIN_CORRUPT")
        previous = digest
        notice_count += 1
        value = json.loads(n["body"])
        if value["kind"] == "BINDINGS_SEALED":
            binding = {**value, "notice_hash": digest}
            segments.append({**binding, "admitted_sequences": []})
        if value["kind"] == "ADMITTED":
            execution = value["execution_id"]
            if execution in admissions or binding is None:
                raise ValueError("DUPLICATE_OR_UNBOUND_ADMISSION")
            admissions[execution] = {"at": value["at"], "notice_hash": digest, "binding": binding}
        if value["kind"] == "TRANSITION" and value.get("state") in ("EXPORTED", "BACKED_UP"):
            index = exported_at if value["state"] == "EXPORTED" else backed_at
            execution = value["execution_id"]
            if execution in index:
                raise ValueError("DUPLICATE_COMPLETION_TRANSITION")
            index[execution] = value
    connection.close()
    ids = {row["execution_id"] for row in records}
    if any(set(index) != ids for index in (admissions, exported_at, backed_at)):
        raise ValueError("MISSING_ADMISSION_EXPORT_OR_BACKUP_NOTICE")
    segment_index = {s["notice_hash"]: s for s in segments}
    provenance = []
    for slot, record in zip(slots, records, strict=True):
        execution = slot["execution_id"]
        admission, exported, backup = (
            admissions[execution],
            exported_at[execution],
            backed_at[execution],
        )
        deadline = instant(slot["deadline"])
        if instant(exported["at"]) < deadline or instant(backup["at"]) < instant(exported["at"]):
            raise ValueError("EXPORT_OR_BACKUP_PRECEDES_SAVED_OBSERVATION_DEADLINE")
        if any(item["deadline"] != slot["deadline"] for item in (exported, backup)):
            raise ValueError("HISTORICAL_OBSERVATION_DEADLINE_DRIFT")
        if backup["backup_hash"] != slot["backup_hash"]:
            raise ValueError("HISTORICAL_BACKUP_REFERENCE_DRIFT")
        segment = admission["binding"]
        segment_index[segment["notice_hash"]]["admitted_sequences"].append(slot["sequence"])
        provenance.append(
            {
                **{key: slot[key] for key in fields},
                "admitted_at": admission["at"],
                "admission_notice_hash": admission["notice_hash"],
                "controller_run_hash": segment["run"],
                "binding_notice_hash": segment["notice_hash"],
                "saved_deadline": slot["deadline"],
                "exported_at": exported["at"],
                "backed_up_at": backup["at"],
                "backup_receipt_sha256": slot["backup_hash"],
                "archive_sha256": record["archive_sha256"],
                "pinned_version": record["pinned_version"],
                "original_export_sha256": record["export_sha256"],
            }
        )
    with (HERE / "analysis/operational-provenance.csv").open(
        "x", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(provenance[0]))
        writer.writeheader()
        writer.writerows(provenance)
    segment_summary = [
        {
            **{key: value for key, value in s.items() if key != "admitted_sequences"},
            "first_sequence": min(s["admitted_sequences"]),
            "last_sequence": max(s["admitted_sequences"]),
            "originals": len(s["admitted_sequences"]),
        }
        for s in segments
    ]
    with (HERE / "analysis/operational-segments.json").open("x", encoding="utf-8") as stream:
        json.dump(
            {
                "segments": segment_summary,
                "limitation": (
                    "Controller binding at admission is a provenance reference, "
                    "not per-process binary attestation"
                ),
            },
            stream,
            indent=2,
        )
    proof = {
        "status": "PASS_TECHNICAL_CLOSEOUT_SCIENTIFIC_LIMITATIONS_RETAINED",
        "originals": 1500,
        "inputs": 500,
        "arms": {"B3": 500, "P1": 500, "P2": 500},
        "unique_admissions": len(admissions),
        "exports_after_saved_deadlines": len(exported_at),
        "verified_backup_transitions": len(backed_at),
        "notice_chain_entries": notice_count,
        "controller_binding_segments": len(segments),
        "unchanged_source_files": len(inventory["files"]),
        "source_package": PACKAGE,
        "dataset_hashes_unchanged": True,
        "csv_matches_all_original_values": True,
        "raw_failures_retained": sum(r["raw_status"] == "FAILED" for r in records),
        "regrading": False,
        "new_timing_sidecar": False,
        "replay": False,
        "cloud_calls": 0,
        "original_analysis_file_hashes_still_match": True,
        "observation_limitation": (
            "Recorded post-deadline export supports full-window accounting, "
            "not proof of client silence or journal completeness"
        ),
        "inference_limitation": (
            "Original claim-permitted flags, UNKNOWNs and censoring/dependence limitations "
            "remain; no general superiority or human-voice claim"
        ),
    }
    with (HERE / "final-validation.json").open("x", encoding="utf-8") as stream:
        json.dump(proof, stream, indent=2)
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
