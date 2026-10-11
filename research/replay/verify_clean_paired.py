"""Offline clean-task replay verification using simulator truth and client exposure."""

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from research.analysis.metrics import clean_paired_difference, metric_rows, paired_counts
from research.oracle.grade import PlaybackAck, grade_clean
from research.runner.clean_paired import CLEAN_ANALYSIS_VERSION, RUNNER_VERSION
from research.scenario_dsl.models import CleanScenarioCase, stable_hash


def verify_clean_bundle(path: Path) -> dict[str, Any]:
    bundle: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    digest = bundle["bundle_hash"]
    if stable_hash({key: value for key, value in bundle.items() if key != "bundle_hash"}) != digest:
        raise ValueError("Clean replay bundle hash differs from contents")
    manifest = bundle["manifest"]
    if stable_hash(manifest) != bundle["manifest_hash"]:
        raise ValueError("Clean manifest hash differs from contents")
    if (
        manifest["runner_version"] != RUNNER_VERSION
        or manifest["analysis_version"] != CLEAN_ANALYSIS_VERSION
    ):
        raise ValueError("Clean replay version differs from the current protocol")
    case = CleanScenarioCase.model_validate(manifest["scenario"])
    if case.fixture_hash != manifest["fixture_hash"] or case.audio_hash != manifest["audio_hash"]:
        raise ValueError("Clean fixture hash differs from manifest")
    voice = manifest.get("voice_evidence")
    if voice is not None:
        from research.runner.acoustic_source import AcousticEvidence

        AcousticEvidence.model_validate(voice)
        if (
            stable_hash(voice) != manifest["voice_evidence_hash"]
            or voice["input_audio_hash"] != case.audio_hash
        ):
            raise ValueError("Local acoustic evidence differs from manifest")
    else:
        audio_path = (
            Path(__file__).resolve().parents[1] / "fixtures" / "audio" / "clean_booking.wav"
        )
        if hashlib.sha256(audio_path.read_bytes()).hexdigest() != case.audio_hash:
            raise ValueError("Clean audio fixture bytes differ from manifest")
    no_fault = {"fault": "NONE", "correction": False}
    if manifest["fault_schedule"] != {**no_fault, "hash": stable_hash(no_fault)}:
        raise ValueError("Clean task includes a fault or correction schedule")
    executions = bundle["executions"]
    if len(executions) != bundle["execution_count"] or {item["arm"] for item in executions} != set(
        manifest["arms"]
    ):
        raise ValueError("Clean replay execution arms or count differ")
    rows: list[dict[str, Any]] = []
    for execution in executions:
        clarification = voice is not None and voice["status"] == "CLARIFICATION"
        if clarification:
            if (
                execution["accepted_revision"] is not None
                or execution["simulator_truth"]
                or execution["playback_ack"]
                or execution["permit_id"]
            ):
                raise ValueError("Clarification caused a business effect or decisive claim")
        elif execution["accepted_revision"]["revision"] != 1:
            raise ValueError("Clean task did not accept exactly one revision")
        if not clarification and (
            execution["accepted_revision"]["desired_state"]["requested_start"]
            != (voice["proposal"]["requested_start"] if voice else case.final_start.isoformat())
        ):
            raise ValueError("Clean accepted intent differs from external fixture")
        if not clarification and [item["action"] for item in execution["simulator_truth"]] != [
            "CREATE"
        ]:
            raise ValueError("Clean provider truth is not one CREATE")
        if not clarification and execution["arm"] in ("P1", "P2") and not execution["permit_id"]:
            raise ValueError("Permit-bearing clean arm lacks a claim permit")
        if execution["arm"] == "B3" and execution["permit_id"] is not None:
            raise ValueError("B3 clean baseline unexpectedly has a claim permit")
        if execution["arm"] in ("B0", "B1", "B2") and not clarification:
            if execution["permit_id"] or execution["receipt_id"] or execution["provider_evidence"]:
                raise ValueError("Clean baseline used a proposed mechanism")
            events = execution["baseline_events"]
            for ordinal, event in enumerate(events, 1):
                if event["ordinal"] != ordinal or event["content_hash"] != stable_hash(
                    {
                        "event_kind": event["event_kind"],
                        "raw": event["raw_json"],
                        "normalized": event["normalized_json"],
                    }
                ):
                    raise ValueError("Clean baseline raw provider evidence differs")
            writes = [row["raw_json"] for row in events if row["event_kind"] == "REQUEST_SENT"]
            if len(writes) != 1 or writes[0]["operation_id"] != str(
                execution["simulator_truth"][0]["operation_id"]
            ):
                raise ValueError("Clean baseline write differs from independent truth")
        ack = PlaybackAck.model_validate(execution["playback_ack"]) if not clarification else None
        if ack and ack.permit_id != execution["permit_id"]:
            raise ValueError("Clean playback permit differs from execution")
        result = grade_clean(case, execution["simulator_truth"], [ack] if ack else [])
        if result != execution["oracle_result"]:
            raise ValueError("Clean independent oracle result differs")
        if metric_rows(result) != execution["metrics"]:
            raise ValueError("Clean metric rows differ from oracle")
        rows.append(
            {
                "scenario_key": case.scenario_key,
                "arm": execution["arm"],
                "metrics": {
                    item["metric_name"]: item["numeric_value"] for item in execution["metrics"]
                },
            }
        )
    summary = paired_counts(rows, "clean_task_success")
    if summary != bundle["paired_summary"]:
        raise ValueError("Clean paired summary differs from execution evidence")
    descriptive = {
        arm: clean_paired_difference(rows, "B3", arm) for arm in manifest["arms"] if arm != "B3"
    }
    if descriptive != bundle["noninferiority_descriptive"]:
        raise ValueError("Clean paired non-inferiority descriptive summary differs")
    if summary["independent_scenarios"] != bundle["independent_scenario_count"]:
        raise ValueError("Clean scenario count differs from fixture count")
    return {
        "run_id": bundle["run_id"],
        "bundle_hash": digest,
        "verified_executions": len(executions),
        "independent_scenarios": summary["independent_scenarios"],
    }


if __name__ == "__main__":
    print(json.dumps(verify_clean_bundle(Path(sys.argv[1])), indent=2))
