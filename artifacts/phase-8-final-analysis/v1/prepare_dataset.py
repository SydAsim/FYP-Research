"""Verify a returned evidence bundle and assemble unchanged original analysis rows.

No network, oracle, driver, application import, or historical timing reclassification.
Imports the frozen research value models only after checking their source hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tarfile
from pathlib import Path
from typing import Any, cast

HERE = Path(__file__).resolve().parent
SOURCE = Path("E:/p8v12/source")
PACKAGE = "cad8fb4960c0e451e7d749ce2ce29cb386216611acd552424714f2f03fba7c9d"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError("JSON_OBJECT_REQUIRED")
    return cast(dict[str, Any], value)


def source_gate() -> None:
    proof = read(HERE / "source-verification.json")
    if proof["status"] != "PASS" or proof["package_hash"] != PACKAGE:
        raise ValueError("FROZEN_SOURCE_VERIFICATION_REQUIRED")
    inventory = SOURCE / "artifacts/phase-8-runner-amendment/v4-complete/candidate-inventory.json"
    data = read(inventory)
    if sha(inventory.read_bytes()) != proof["source_inventory_sha256"]:
        raise ValueError("INVENTORY_DRIFT")
    if sha(canonical(data["files"])) != PACKAGE:
        raise ValueError("PACKAGE_DRIFT")
    for name, expected in data["files"].items():
        if name.startswith("research/") and Path(name).suffix in (".py", ".json", ".txt"):
            if sha((SOURCE / name).read_bytes()) != expected:
                raise ValueError("FROZEN_RESEARCH_SOURCE_DRIFT:" + name)


def restore_row(record: dict[str, Any], case: Any, row_model: Any) -> dict[str, Any]:
    """Restore metadata absent from the old compact derivative, never outcomes/times."""
    if "analysis_row" in record:
        row = row_model.model_validate(record["analysis_row"])
    else:
        row = row_model(
            classification="CAMPAIGN",
            case_id=case.case_id,
            cluster_id=case.cluster_id,
            generator_family=case.generator_family,
            stratum=case.stratum,
            member=case.member,
            cluster_representative=case.cluster_representative,
            arm=record["arm"],
            attempt=record["attempt"],
            execution_id=record["execution_id"],
            values=record["values"],
            duration_seconds=record["duration_seconds"],
            event_observed=record["event_observed"],
            censor_reason=record["censor_reason"],
            oracle_hash=record["oracle_hash"],
            phase=case.correction_barrier,
            fault=case.fault_label,
            revision_type="NONE" if case.stratum.value == "CLEAN" else "PARAMETER_CORRECTION",
            action_class=(
                "CREATE"
                if case.stratum.value == "CLEAN"
                else "CREATE_RESCHEDULE"
                if case.provider.supports_reschedule
                else "CREATE_CANCEL_CREATE"
            ),
        )
    if row.classification != "CAMPAIGN" or row.attempt != 1:
        raise ValueError("ORIGINAL_CAMPAIGN_ROWS_REQUIRED")
    if row.values != record["values"]:
        raise ValueError("RECORDED_OUTCOME_DRIFT")
    return cast(dict[str, Any], row.model_dump(mode="json"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    if args.bundle.stat().st_size > 32 * 1024**2:
        raise ValueError("BUNDLE_SIZE_BOUND")
    if sha(args.bundle.read_bytes()) != args.sha256:
        raise ValueError("RETURNED_BUNDLE_HASH_MISMATCH")
    source_gate()
    sys.path.insert(0, str(SOURCE))
    from research.study.models import AnalysisRow, StudyCase

    selected: dict[str, bytes] = {}
    with tarfile.open(args.bundle) as archive:
        for member in archive:
            if not member.isfile() or member.name not in (
                "all-results.json",
                "verification.json",
                "attempt.json",
                "prerequisites.json",
            ):
                raise ValueError("UNEXPECTED_BUNDLE_MEMBER")
            if member.name in selected or member.size > 64 * 1024**2:
                raise ValueError("DUPLICATE_OR_OVERSIZE_BUNDLE_MEMBER")
            stream = archive.extractfile(member)
            assert stream is not None
            selected[member.name] = stream.read()
    if len(selected) != 4:
        raise ValueError("INCOMPLETE_RETURNED_BUNDLE")
    manifest = json.loads(selected["verification.json"])
    if manifest["status"] != "PASS" or manifest["records"] != 1500:
        raise ValueError("EXTRACTION_INCOMPLETE")
    for name in ("all-results.json", "attempt.json", "prerequisites.json"):
        if sha(selected[name]) != manifest["files"][name]:
            raise ValueError("RETURNED_MEMBER_HASH_MISMATCH:" + name)
    payload = json.loads(selected["all-results.json"])
    packet = read(HERE / "extraction-control.json")
    if payload["control_sha256"] != sha((HERE / "extraction-control.json").read_bytes()):
        raise ValueError("WRONG_EXTRACTION_CONTROL")
    if payload["master_archive_sha256"] != packet["master_archive_sha256"]:
        raise ValueError("WRONG_MASTER_BOUNDARY")
    records = payload["records"]
    if len(records) != 1500 or len({r["execution_id"] for r in records}) != 1500:
        raise ValueError("ORIGINAL_DENOMINATOR_OR_DUPLICATE")
    if records[:735] != packet["cached_originals"]:
        raise ValueError("CACHED_ORIGINALS_REPLACED")
    if sha(canonical(records[:735])) != manifest["files"]["cached-originals.json"]:
        raise ValueError("CACHED_MEMBER_COMMITMENT")
    cases = {
        key: StudyCase.model_validate(value)
        for key, value in read(HERE / "frozen-cases.json").items()
    }
    rows = []
    counts: dict[str, set[str]] = {}
    for identity, record in zip(packet["identities"], records, strict=True):
        for key in ("sequence", "case_id", "arm", "attempt", "execution_id"):
            if identity[key] != record[key]:
                raise ValueError("SAVED_IDENTITY_DRIFT:" + key)
        receipt = packet["receipts"][record["execution_id"]]["receipt"]
        if record["archive_sha256"] != receipt["sha256"]:
            raise ValueError("ARCHIVE_BINDING_DRIFT")
        if record["pinned_version"] != receipt["cloud"]["version_id"]:
            raise ValueError("PINNED_VERSION_DRIFT")
        case = cases[record["case_id"]]
        if case.fixture_hash != identity["fixture_hash"]:
            raise ValueError("FIXTURE_BINDING_DRIFT")
        if identity["sequence"] > 735:
            name = f"records/{identity['sequence']:04d}.json"
            if sha(canonical(record)) != manifest["files"][name]:
                raise ValueError("INDIVIDUAL_RECORD_COMMITMENT")
        row = restore_row(record, case, AnalysisRow)
        if any(row[k] != record[k] for k in ("case_id", "arm", "attempt", "execution_id")):
            raise ValueError("ANALYSIS_IDENTITY_DRIFT")
        rows.append(row)
        counts.setdefault(record["case_id"], set()).add(record["arm"])
    if len(counts) != 500 or any(arms != {"B3", "P1", "P2"} for arms in counts.values()):
        raise ValueError("COMPLETE_PAIRED_FRAME_REQUIRED")
    timing_rows = list(rows)
    sidecar_proof = read(HERE / "accepted-existing-sidecars/verification.json")
    if sidecar_proof["status"] != "PASS_EXISTING_ACCEPTED_SIDECARS_ONLY":
        raise ValueError("ACCEPTED_SIDECAR_BINDING_REQUIRED")
    for item in sidecar_proof["sidecars"]:
        path = HERE / "accepted-existing-sidecars" / (item["label"] + ".json")
        if sha(path.read_bytes()) != item["sha256"]:
            raise ValueError("ACCEPTED_SIDECAR_DRIFT")
        sidecar = read(path)
        index = next(i for i, row in enumerate(rows) if row["execution_id"] == item["execution_id"])
        if rows[index] != sidecar["original_stored_analysis"]:
            raise ValueError("SIDECAR_ORIGINAL_BINDING_DRIFT")
        proposed = sidecar["proposed_analysis"]
        if any(
            rows[index][key] != proposed[key]
            for key in ("values", "duration_seconds", "event_observed")
        ):
            raise ValueError("UNREVIEWED_OUTCOME_OR_NUMERIC_TIMING_CHANGE")
        timing_rows[index] = AnalysisRow.model_validate(proposed).model_dump(mode="json")
    output = HERE / "dataset"
    output.mkdir(exist_ok=False)
    for name, value in (("analysis-rows.json", rows), ("recorded-results.json", records)):
        (output / name).write_bytes(canonical(value))
    (output / "accepted-timing-rows.json").write_bytes(canonical(timing_rows))
    proof = {
        "status": "PASS_DATASET_NOT_ANALYSIS",
        "originals": 1500,
        "inputs": 500,
        "complete_three_arm_sets": 500,
        "bundle_sha256": args.sha256,
        "source_package_hash": PACKAGE,
        "analysis_rows_sha256": sha(canonical(rows)),
        "recorded_results_sha256": sha(canonical(records)),
        "grades_or_raw_statuses_rewritten": False,
        "historical_timing_sidecars_applied": False,
        "existing_accepted_sidecars_reused_in_separate_timing_view": 2,
        "accepted_timing_rows_sha256": sha(canonical(timing_rows)),
        "cached_rows": 735,
        "new_pinned_archives": 765,
    }
    (output / "verification.json").write_bytes(canonical(proof))
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
