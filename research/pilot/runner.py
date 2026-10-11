"""Run fresh pilot cases and retain all attempts and inspected failure evidence."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from research.analysis.completion_metrics import secondary_metrics, timeline_snapshot
from research.analysis.pilot import analyze
from research.arms import Arm
from research.pilot.plan import pilot_plan
from research.replay.verify_clean_paired import verify_clean_bundle
from research.replay.verify_p8_paired import verify_p8_paired
from research.replay.verify_phase6 import verify_bundle
from research.replay.verify_playout_paired import verify_playout_paired
from research.runner.acoustic import capture_local
from research.runner.clean_paired import run_clean_paired
from research.runner.p8_paired import run_p8_paired
from research.runner.paired import run_paired
from research.runner.playout_paired import run_playout_paired
from research.scenario_dsl.models import Barrier, CleanScenarioCase, ScenarioCase, stable_hash

VERIFIERS = {
    "provider": verify_bundle,
    "clean": verify_clean_bundle,
    "p8": verify_p8_paired,
    "playout": verify_playout_paired,
}


def write(path: Path, value: dict[str, Any], *, immutable: bool = False) -> None:
    if immutable and path.exists():
        raise FileExistsError(f"Immutable evidence already exists: {path}")
    path.write_text(json.dumps(value, indent=2, default=str) + "\n", encoding="utf-8")


def inspect_failure(row: dict[str, Any], case: dict[str, Any], kind: str) -> dict[str, Any] | None:
    result = row["oracle_result"]
    problems = [
        name
        for name in (
            "correction_success",
            "clean_task_success",
            "outcome_coverage",
            "safe_resolution",
            "played_span_repair_complete",
        )
        if name in result and not result[name]
    ] + [name for name in ("unsupported_confirmation", "duplicate_effect") if result[name]]
    if not problems:
        return None
    trace = row.get("trace", row)
    truth = trace.get("simulator_truth_log", row.get("simulator_truth", []))
    acks = row.get("playback_acks", [row["playback_ack"]] if row.get("playback_ack") else [])
    evidence = next(
        (
            row[key]
            for key in ("unavailable_evidence", "partial_effect_evidence", "conflict_evidence")
            if row.get(key)
        ),
        None,
    )
    if kind in ("p8", "playout"):
        classification = "PLAYBACK_ABLATION_OR_REPAIR_COVERAGE"
        explanation = (
            "Read raw client frame events, permit/repair state and independent provider history."
        )
    elif case.get("visibility") == "UNAVAILABLE":
        classification = "UNOBSERVABLE_PROVIDER_EXPECTED_UNRESOLVED"
        explanation = "Hidden durable effect remains unreconciled within the frozen read budget."
    elif case.get("fault_family") == "PARTIAL_EFFECT":
        classification = "PARTIAL_PROVIDER_EFFECT_EXPECTED_HANDOFF"
        explanation = "Partial HELD effect is retained; no safe completed appointment is invented."
    elif case.get("fault_family") == "PROVIDER_CONFLICT":
        classification = "RESOURCE_VERSION_CONFLICT_EXPECTED_HANDOFF"
        explanation = "Concurrent authoritative resource change prevents the final mutation."
    elif kind == "clean" and row.get("operation_id") is None:
        classification = "ACTUAL_CASCADE_CLARIFICATION_TASK_FAILURE"
        explanation = "Actual speech/model evidence produced clarification; zero provider writes."
    elif case.get("revision_type") == "RETRACTION" and result["correction_success"]:
        classification = "CANCELLATION_SPEECH_WITHHELD_CONTRACT_LIMIT"
        explanation = "Independent cancellation holds; no cancellation speech enum exists."
    else:
        classification = "BASELINE_MECHANISM_LIMIT"
        explanation = (
            "Inspect ordered raw baseline reads/writes and final oracle "
            "state; keep failure in denominator."
        )
    return {
        "execution_id": row["execution_id"],
        "workflow_id": row["workflow_id"],
        "arm": row["arm"],
        "failed_or_unsafe_endpoints": problems,
        "classification": classification,
        "explanation": explanation,
        "provider_history_inspected": truth,
        "client_exposure_inspected": acks,
        "mechanism_evidence_inspected": evidence
        or row.get("baseline_events")
        or trace.get("repair"),
        "normalized_event_count": len(
            row.get("normalized_events", trace.get("normalized_timeline", []))
        ),
        "disposition": "RETAINED_NO_EXCLUSION_NO_SUCCESS_SUBSTITUTION",
    }


def metric_observation(
    item: dict[str, Any], row: dict[str, Any], secondary: dict[str, Any]
) -> dict[str, Any]:
    values = {m["metric_name"]: m["numeric_value"] for m in row["metrics"]}
    values["safe_resolution"] = int(secondary["safe_resolution_policy"]["value"])
    return {
        "scenario_id": item["scenario_id"],
        "template_id": item["template_id"],
        "variant": item["variant"],
        "arm": row["arm"],
        "execution_id": row["execution_id"],
        "postcommit_ambiguity": item["case"].get("fault_family") == "RESPONSE_LOSS",
        "values": values,
    }


def verify_entry(
    entry: dict[str, Any], directory: Path, item: dict[str, Any]
) -> list[dict[str, Any]]:
    path = (directory / entry["path"]).resolve()
    if not path.is_relative_to(directory.resolve()):
        raise ValueError("Pilot child escapes evidence directory")
    verified = VERIFIERS[item["kind"]](path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    if verified["bundle_hash"] != entry["bundle_hash"]:
        raise ValueError("Pilot replay child differs")
    if bundle["manifest"]["scenario"] != item["case"] or set(bundle["manifest"]["arms"]) != set(
        item["arms"]
    ):
        raise ValueError("Pilot child case or arm definition differs from predeclared plan")
    if bundle["manifest"].get("voice_evidence") != item["voice_evidence"]:
        raise ValueError("Pilot child actual cascade evidence differs")
    observations = []
    if len(entry["secondary_evidence"]) != len(bundle["executions"]):
        raise ValueError("Pilot metric evidence is incomplete")
    for row, evidence in zip(bundle["executions"], entry["secondary_evidence"], strict=True):
        timeline = evidence["timeline"]
        if (
            row["execution_id"] != evidence["execution_id"]
            or timeline["workflow_id"] != row["workflow_id"]
        ):
            raise ValueError("Pilot timeline belongs to another execution")
        indexed = {e["workflow_sequence"]: e for e in timeline["events"]}
        for event in row.get(
            "normalized_events", row.get("trace", {}).get("normalized_timeline", [])
        ):
            saved = indexed.get(event["workflow_sequence"])
            if saved is None or any(
                saved[k] != event[k] for k in ("event_name", "intent_revision", "payload")
            ):
                raise ValueError("Pilot timeline differs from replay events")
        if (
            stable_hash(timeline) != evidence["timeline_hash"]
            or secondary_metrics(row, timeline) != evidence["metrics"]
        ):
            raise ValueError("Pilot secondary metric evidence differs")
        if inspect_failure(row, item["case"], item["kind"]) != evidence["failure_review"]:
            raise ValueError("Pilot failure inspection omitted or changed")
        observations.append(metric_observation(item, row, evidence["metrics"]))
    return observations


def verify_pilot(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    if stable_hash({k: v for k, v in result.items() if k != "hash"}) != result["hash"]:
        raise ValueError("Pilot manifest hash differs")
    plan = result["plan"]
    if stable_hash({k: v for k, v in plan.items() if k != "hash"}) != plan["hash"]:
        raise ValueError("Pilot plan hash differs")
    # Reconstruct design including actual model evidence; no hand-picked observed outcomes.
    acoustic = [i["voice_evidence"] for i in plan["cases"] if i["voice_evidence"] is not None]
    if json.loads(json.dumps(pilot_plan(acoustic))) != plan:
        raise ValueError("Pilot plan differs from declared 40-scenario design")
    if len(result["entries"]) != len(plan["cases"]):
        raise ValueError("Pilot omitted planned scenario versions")
    rows = []
    execution_ids: list[str] = []
    for item, entry in zip(plan["cases"], result["entries"], strict=True):
        if entry["state"] != "VERIFIED" or entry["item_hash"] != stable_hash(item):
            raise ValueError("Pilot has unfinished or mismatched planned work")
        observed = verify_entry(entry, path.parent, item)
        rows.extend(observed)
        execution_ids.extend(r["execution_id"] for r in observed)
    if len(set(execution_ids)) != len(execution_ids) or len(rows) != plan["planned_executions"]:
        raise ValueError("Pilot reused execution evidence or has incorrect execution accounting")
    if (
        rows != result["metric_observations"]
        or analyze(rows, result["ni_margin"]) != result["analysis"]
    ):
        raise ValueError("Pilot analysis or raw counts differ")
    return {
        "manifest_path": str(path.resolve()),
        "manifest_hash": result["hash"],
        "independent_scenario_instances": 40,
        "scenario_versions": len(plan["cases"]),
        "verified_executions": len(rows),
        "failure_reviews": sum(
            e["failure_review"] is not None
            for entry in result["entries"]
            for e in entry["secondary_evidence"]
        ),
        "phase8_started": False,
    }


def run_pilot(directory: Path, margin: float = 0.05) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    ledger_path = directory / "ledger.json"
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        if ledger["ni_margin"] != margin:
            raise ValueError("Changed margin requires a new pilot directory")
    else:
        from research.pilot.freeze import source_inventory

        print("Capturing actual local speech/model evidence", flush=True)
        ledger = {
            "version": "phase7-pilot-ledger-v1",
            "session_id": str(uuid4()),
            "started_at": datetime.now(UTC).isoformat(),
            "ni_margin": margin,
            "plan": pilot_plan(capture_local()),
            "source_inventory": source_inventory(),
            "entries": [],
            "attempts": [],
        }
        write(ledger_path, ledger)
    from research.pilot.freeze import source_inventory

    if ledger["source_inventory"] != source_inventory():
        raise ValueError("Pilot code changed: retain this attempt and create a new version")
    rows = []
    for index, item in enumerate(ledger["plan"]["cases"]):
        print(f"CASE {index + 1}/45 {item['scenario_id']} {item['variant']}", flush=True)
        if index < len(ledger["entries"]):
            rows.extend(verify_entry(ledger["entries"][index], directory, item))
            continue
        attempt: dict[str, Any] = {
            "item_hash": stable_hash(item),
            "state": "STARTED",
            "trace_id": str(uuid4()),
        }
        ledger["attempts"].append(attempt)
        write(ledger_path, ledger)
        try:
            arms = tuple(Arm(a) for a in item["arms"])
            if item["kind"] == "provider":
                outcome = run_paired(ScenarioCase.model_validate(item["case"]), arms, directory)
            elif item["kind"] == "clean":
                outcome = run_clean_paired(
                    CleanScenarioCase.model_validate(item["case"]),
                    directory,
                    item["voice_evidence"],
                    arms,
                )
            elif item["kind"] == "p8":
                outcome = run_p8_paired(directory, arms)
            else:
                outcome = run_playout_paired(
                    Barrier(item["case"]["correction_barrier"]), directory, arms
                )
            bundle = json.loads(Path(outcome["bundle_path"]).read_text(encoding="utf-8"))
            entry: dict[str, Any] = {
                "state": "VERIFIED",
                "item_hash": stable_hash(item),
                "path": Path(outcome["bundle_path"]).relative_to(directory.resolve()).as_posix(),
                "bundle_hash": bundle["bundle_hash"],
                "secondary_evidence": [],
            }
            for row in bundle["executions"]:
                timeline = timeline_snapshot(row["workflow_id"])
                entry["secondary_evidence"].append(
                    {
                        "execution_id": row["execution_id"],
                        "timeline": timeline,
                        "timeline_hash": stable_hash(timeline),
                        "metrics": secondary_metrics(row, timeline),
                        "failure_review": inspect_failure(row, item["case"], item["kind"]),
                    }
                )
            rows.extend(verify_entry(entry, directory, item))
            ledger["entries"].append(entry)
            attempt["state"] = "VERIFIED"
            attempt["bundle_path"] = entry["path"]
        except Exception as exc:
            attempt.update(state="FAILED", error=str(exc), exception_type=type(exc).__name__)
            write(ledger_path, ledger)
            print(json.dumps(attempt), flush=True)
            raise
        write(ledger_path, ledger)
        print(f"VERIFIED {len(bundle['executions'])} executions", flush=True)
    result = {
        "version": "phase7-pilot-completion-v1",
        "plan": ledger["plan"],
        "ni_margin": margin,
        "source_inventory": ledger["source_inventory"],
        "attempts": ledger["attempts"],
        "entries": ledger["entries"],
        "metric_observations": rows,
        "analysis": analyze(rows, margin),
        "completed_at": datetime.now(UTC).isoformat(),
    }
    result["hash"] = stable_hash(result)
    path = directory / f"pilot-{result['hash'][:12]}.json"
    write(path, result, immutable=True)
    return verify_pilot(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute or independently verify Phase 7 pilot")
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/phase-7-pilot/v1"))
    parser.add_argument("--ni-margin", type=float, default=0.05)
    args = parser.parse_args()
    print(
        json.dumps(
            verify_pilot(args.verify)
            if args.verify
            else run_pilot(args.output.resolve(), args.ni_margin),
            indent=2,
        )
    )
