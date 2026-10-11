"""Reproducible Phase 6 harness closure, distinct from the Phase 7 pilot/freeze."""

import argparse
import json
from collections.abc import Callable
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from research.analysis.completion_metrics import secondary_metrics, timeline_snapshot
from research.replay.phase4_p8 import run as run_repair
from research.replay.phase6_p8_witness import verify_witness, witness_case
from research.replay.verify_clean_paired import verify_clean_bundle
from research.replay.verify_p8_paired import verify_p8_paired
from research.replay.verify_phase6 import verify_bundle
from research.replay.verify_playout_paired import verify_playout_paired
from research.runner.acoustic import run_acoustic
from research.runner.acoustic_source import CONDITIONS
from research.runner.clean_paired import run_clean_paired
from research.runner.p8_paired import run_p8_paired
from research.runner.paired import ALL_ARMS, _source_identity, run_paired
from research.runner.playout_paired import run_playout_paired
from research.runner.redis_loss import wipe_cache
from research.scenario_dsl.catalog import (
    CONFLICT_COVERING,
    DELAY_COVERING,
    PARTIAL_COVERING,
    READ_COVERING,
    REDIS_COVERING,
    REFUSAL_COVERING,
    case_for,
)
from research.scenario_dsl.covering import coverage_manifest
from research.scenario_dsl.models import Barrier, stable_hash

ROOT = Path(__file__).resolve().parents[2]
DESTINATION = ROOT / "artifacts" / "phase-6-completion"


def run_redis_repair(output: Path) -> dict[str, Any]:
    case = witness_case()
    trace = run_repair(
        research_arm="P2", on_repair_open=lambda workflow: wipe_cache(UUID(workflow))
    )
    from research.oracle.p8_witness import grade_p8_witness

    bundle: dict[str, Any] = {
        "manifest": {
            "witness_version": "phase6-redis-repair-v1",
            "arm": "P2",
            "scenario": case.model_dump(mode="json"),
            "fixture_hash": case.fixture_hash,
            "source": _source_identity(),
        },
        "trace": trace,
        "oracle_result": grade_p8_witness(trace, case),
    }
    bundle["bundle_hash"] = stable_hash(bundle)
    path = output / f"redis-repair-{trace['scenario_id']}.json"
    path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    verify_redis_repair(path)
    return {"bundle_path": str(path), "bundle_hash": bundle["bundle_hash"]}


def verify_redis_repair(path: Path) -> dict[str, Any]:
    from research.replay.recovery_evidence import verify_cache

    verified = verify_witness(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    cache = bundle["trace"]["redis_repair_evidence"]
    verify_cache(cache)
    repairs = cache["before"]["repair_obligations"]
    if (
        len(repairs) != 1
        or repairs[0]["state"] != "OPEN"
        or not verified["played_span_repair_complete"]
    ):
        raise ValueError(
            "Redis loss did not preserve an existing repair through completed playback"
        )
    return {**verified, "verified_executions": 1}


VERIFIERS: dict[str, Callable[[Path], dict[str, Any]]] = {
    "provider": verify_bundle,
    "clean": verify_clean_bundle,
    "playout": verify_playout_paired,
    "p8": verify_p8_paired,
    "redis_repair": verify_redis_repair,
}


def run_completion() -> dict[str, Any]:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    session_id = str(uuid4())
    ledger_path = DESTINATION / f"ledger-{session_id}.json"
    ledger: dict[str, Any] = {
        "session_id": session_id,
        "scope": "PHASE6_HARNESS_NOT_PHASE7_PILOT",
        "started_at": datetime.now(UTC).isoformat(),
        "entries": [],
    }
    entries: list[dict[str, Any]] = ledger["entries"]

    def save() -> None:
        ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")

    def add(label: str, kind: str, action: Callable[[], dict[str, Any]]) -> None:
        print(f"START {label}", flush=True)
        entry: dict[str, Any] = {"label": label, "kind": kind, "state": "STARTED"}
        entries.append(entry)
        save()
        try:
            checkpoint = DESTINATION / f"checkpoint-{stable_hash({'label': label})[:16]}.json"
            result = (
                json.loads(checkpoint.read_text(encoding="utf-8"))
                if checkpoint.exists()
                else action()
            )
            path = Path(result["bundle_path"])
            verified = VERIFIERS[kind](path)
            bundle = json.loads(path.read_text(encoding="utf-8"))
            rows = bundle.get("executions", [])
            entry.update(
                state="VERIFIED",
                path=path.relative_to(ROOT).as_posix(),
                bundle_hash=bundle["bundle_hash"],
                verified=verified,
                source_identity=bundle["manifest"].get("source_tree_hash"),
                secondary_evidence=[
                    {
                        "execution_id": row["execution_id"],
                        "timeline": timeline_snapshot(row["workflow_id"]),
                    }
                    for row in rows
                ],
            )
            for row, evidence in zip(rows, entry["secondary_evidence"], strict=True):
                evidence["timeline_hash"] = stable_hash(evidence["timeline"])
                evidence["metrics"] = secondary_metrics(row, evidence["timeline"])
            print(f"VERIFIED {label}: {verified['verified_executions']} executions", flush=True)
            if not checkpoint.exists():
                checkpoint.write_text(json.dumps(result, indent=2), encoding="utf-8")
        except Exception as exc:
            entry.update(
                state="FAILED",
                trace_id=str(uuid4()),
                exception_type=type(exc).__name__,
                error=str(exc),
            )
            save()
            raise
        save()

    plan = coverage_manifest()
    for row in plan["scenarios"]:
        key = row["scenario_key"]
        checkpoint = ROOT / "artifacts" / "phase-6-secondary-v3" / f"{key}.json"
        if checkpoint.exists():
            add(key, "provider", partial(json.loads, checkpoint.read_text(encoding="utf-8")))
        else:
            from research.scenario_dsl.models import ScenarioCase

            case = ScenarioCase.model_validate(row)
            add(key, "provider", partial(run_paired, case, ALL_ARMS, DESTINATION))
    for stage in (Barrier.P0, Barrier.P1, Barrier.P2, Barrier.P3, Barrier.P4, Barrier.P5):
        case = case_for(stage)
        add(stage.value, "provider", partial(run_paired, case, ALL_ARMS, DESTINATION))
    for case in (
        *DELAY_COVERING,
        *REFUSAL_COVERING,
        *PARTIAL_COVERING,
        *REDIS_COVERING,
        *READ_COVERING,
    ):
        add(case.scenario_key, "provider", partial(run_paired, case, ALL_ARMS, DESTINATION))
    add(
        "post-verification-version-conflict",
        "provider",
        lambda: run_paired(CONFLICT_COVERING[0], output_dir=DESTINATION),
    )
    add("clean-control", "clean", lambda: run_clean_paired(output_dir=DESTINATION, arms=ALL_ARMS))
    for stage in (Barrier.P6, Barrier.P7, Barrier.P9):
        add(
            stage.value,
            "playout",
            partial(run_playout_paired, stage, DESTINATION, ALL_ARMS),
        )
    add("P8", "p8", lambda: run_p8_paired(DESTINATION, ALL_ARMS))
    add("redis-existing-repair", "redis_repair", lambda: run_redis_repair(DESTINATION))
    acoustic = run_acoustic(DESTINATION)
    for item in acoustic["outcomes"]:
        add(item["condition"], "clean", partial(dict, item["replay"]))
    ledger["completed_at"] = datetime.now(UTC).isoformat()
    save()
    result: dict[str, Any] = {
        "version": "phase6-completion-v1",
        "scope": ledger["scope"],
        "source": _source_identity(),
        "covering_array": plan,
        "entries": entries,
        "accounting": {
            "paired_fixture_count": sum(e["kind"] != "redis_repair" for e in entries),
            "auxiliary_witness_count": 1,
            "verified_executions": sum(e["verified"]["verified_executions"] for e in entries),
            "phase7_started": False,
        },
        "limits": [
            "Physical hearing is not inferred from client acknowledgements",
            "No cancellation speech contract; zero exposure has a zero conditional denominator",
            "Secondary covering rows fixed P3; other levels covered in mandatory rows",
            "Model proposal shared across paired arms isolates protocol effects",
            "Historical child sources remain separately recorded; no single-source campaign claim",
            "No non-inferiority conclusion or population effect estimate from harness smoke runs",
        ],
    }
    result["hash"] = stable_hash(result)
    path = DESTINATION / f"completion-{result['hash'][:12]}.json"
    if path.exists():
        raise FileExistsError("A completed manifest cannot be overwritten")
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return verify_completion(path)


def verify_completion(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    if stable_hash({k: v for k, v in result.items() if k != "hash"}) != result["hash"]:
        raise ValueError("Completion manifest hash differs")
    if result["covering_array"] != json.loads(json.dumps(coverage_manifest())):
        raise ValueError("Completion covering array differs from the declared feasible domain")
    verified_total = 0
    covered_keys: set[str] = set()
    mandatory_labels = {
        *(stage.value for stage in Barrier),
        *CONDITIONS,
        "post-verification-version-conflict",
        "clean-control",
        "redis-existing-repair",
        *(
            case.scenario_key
            for case in (
                *DELAY_COVERING,
                *REFUSAL_COVERING,
                *PARTIAL_COVERING,
                *REDIS_COVERING,
                *READ_COVERING,
            )
        ),
    }
    expected_labels = mandatory_labels | {
        row["scenario_key"] for row in result["covering_array"]["scenarios"]
    }
    labels = [entry["label"] for entry in result["entries"]]
    if len(labels) != len(set(labels)) or set(labels) != expected_labels:
        raise ValueError("Completion omitted or repeated a mandatory planned fixture")
    for entry in result["entries"]:
        if entry["state"] != "VERIFIED":
            raise ValueError("Completion contains an unverified or failed planned execution")
        child = (ROOT / entry["path"]).resolve()
        if not child.is_relative_to(ROOT):
            raise ValueError("Completion child lies outside the replay workspace")
        verified = VERIFIERS[entry["kind"]](child)
        if verified != entry["verified"] or verified["bundle_hash"] != entry["bundle_hash"]:
            raise ValueError("Completion child evidence differs")
        bundle = json.loads(child.read_text(encoding="utf-8"))
        rows = bundle.get("executions", [])
        if len(rows) != len(entry["secondary_evidence"]):
            raise ValueError("Completion lacks secondary metric evidence")
        for row, evidence in zip(rows, entry["secondary_evidence"], strict=True):
            if evidence["timeline"]["workflow_id"] != row["workflow_id"]:
                raise ValueError("Completion causal timeline belongs to another workflow")
            recorded = {e["workflow_sequence"]: e for e in evidence["timeline"]["events"]}
            for event in row.get(
                "normalized_events", row.get("trace", {}).get("normalized_timeline", [])
            ):
                saved = recorded.get(event["workflow_sequence"])
                if saved is None or any(
                    saved[key] != event[key] for key in ("event_name", "intent_revision", "payload")
                ):
                    raise ValueError("Completion causal timeline differs from normalized events")
            if (
                evidence["execution_id"] != row["execution_id"]
                or stable_hash(evidence["timeline"]) != evidence["timeline_hash"]
            ):
                raise ValueError("Completion causal timeline differs")
            if (
                secondary_metrics(row, evidence["timeline"], evidence["metrics"]["version"])
                != evidence["metrics"]
            ):
                raise ValueError("Completion secondary metric differs")
        if entry["label"].startswith("secondary-"):
            scenario = bundle["manifest"]["scenario"]
            expected = next(
                r
                for r in result["covering_array"]["scenarios"]
                if r["scenario_key"] == entry["label"]
            )
            if scenario != expected or set(bundle["manifest"]["arms"]) != {
                arm.value for arm in ALL_ARMS
            }:
                raise ValueError("Completion secondary fixture or paired arms differ")
            covered_keys.add(entry["label"])
        verified_total += verified["verified_executions"]
    if len(covered_keys) != result["covering_array"]["selected_count"]:
        raise ValueError("Completion omitted a planned covering row")
    if verified_total != result["accounting"]["verified_executions"]:
        raise ValueError("Completion execution accounting differs")
    return {
        "manifest_path": str(path.resolve()),
        "manifest_hash": result["hash"],
        **result["accounting"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run or independently verify Phase 6 harness closure"
    )
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify_completion(args.verify) if args.verify else run_completion(), indent=2))
