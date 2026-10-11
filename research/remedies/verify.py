"""Offline verification of every planned slot and arm-neutral outcome replay."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from research.oracle.readiness_v2 import RevisionTarget, grade_observable, repair_telemetry
from research.remedies.plan import FIXTURES
from research.remedies.preserve import OUTPUT
from research.remedies.provenance import verify_source
from research.scenario_dsl.models import stable_hash


def check_hash(body: dict[str, Any], key: str) -> None:
    if stable_hash({k: v for k, v in body.items() if k != key}) != body[key]:
        raise ValueError(f"Hash mismatch: {key}")


def regrade(row: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    return grade_observable(
        [RevisionTarget.model_validate(t) for t in row["targets"]],
        snapshot["truth"], snapshot["segments"], row["client_playback"], snapshot["observations"],
    )


def verify() -> dict[str, Any]:
    manifest = json.loads((OUTPUT / "planned/manifest.json").read_text(encoding="utf-8"))
    check_hash(manifest, "manifest_hash")
    plan = manifest["plan"]
    check_hash(plan, "plan_hash")
    source = json.loads((OUTPUT / "source-freeze.json").read_text(encoding="utf-8"))
    verify_source(source)
    if manifest["source_hash"] != source["source_hash"]:
        raise ValueError("Execution source mismatch")
    expected = {(f["id"], a) for f in FIXTURES for a in ("B3", "P1", "P2")}
    if len(manifest["planned_slots"]) != 18 or {
        (s["fixture"], s["arm"]) for s in manifest["planned_slots"]
    } != expected:
        raise ValueError("Planned accounting mismatch")
    verified = []
    for execution in manifest["executions"]:
        path = Path(execution["path"])
        row = json.loads(path.read_text(encoding="utf-8"))
        check_hash(row, "trace_hash")
        if execution["trace_hash"] != row["trace_hash"]:
            raise ValueError("Manifest trace mismatch")
        if row["fixture_hash"] != stable_hash(row["fixture"]):
            raise ValueError("Fixture mismatch")
        if row["source_hash"] != source["source_hash"]:
            raise ValueError("Trace source mismatch")
        if stable_hash(row["configuration"]) != row["configuration_hash"]:
            raise ValueError("Configuration hash mismatch")
        if row["started_at"] < plan["created_at"]:
            raise ValueError("Outcome preceded plan")
        resource = f"property:{row['fixture_identity']['property_id']}:maintenance"
        for target, hour in zip(row["targets"], row["fixture"]["hours"], strict=False):
            if target["resource_key"] != resource or target["requested_start"] != (
                f"2026-11-01T{hour:02d}:00:00+05:00"
            ):
                raise ValueError("External target differs from planned script")
        if "snapshot" in row:
            if regrade(row, row["snapshot"]) != row["grade"]:
                raise ValueError("Independent replay grade mismatch")
            if repair_telemetry(row["snapshot"]["obligations"]) != row["repair_telemetry"]:
                raise ValueError("Repair telemetry mismatch")
            for observation in row["snapshot"]["observations"]:
                if stable_hash(observation["raw"]) != observation["raw_hash"]:
                    raise ValueError("Raw observation mismatch")
            for segment in row["snapshot"]["segments"]:
                if hashlib.sha256(Path(segment["audio_artifact"]).read_bytes()).hexdigest() != (
                    segment["audio_hash"]
                ):
                    raise ValueError("Audio artifact mismatch")
            for label in ("B3", "P1", "P2"):
                altered = deepcopy(row["snapshot"])
                for segment in altered["segments"]:
                    segment.update(research_arm=label, claim_permit_id=None)
                if regrade(row, altered) != row["grade"]:
                    raise ValueError("Outcome depends on label/internal permit")
        for checkpoint in row["checkpoints"]:
            if regrade(checkpoint, checkpoint["snapshot"]) != checkpoint["grade"]:
                raise ValueError("Checkpoint replay mismatch")
        verified.append({"fixture": execution["fixture"], "arm": row["arm"],
                         "status": row["status"], "trace_hash": row["trace_hash"]})
    result = {"planned": 18, "verified": len(verified), "executions": verified,
              "phase8_started": False, "source_hash": source["source_hash"]}
    (OUTPUT / "offline-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
