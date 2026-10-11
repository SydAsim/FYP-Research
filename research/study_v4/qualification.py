"""Conservative qualification ledger, raw exports and revised offline calibration grades."""

import json
from collections import Counter
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from research.oracle.grade import _instant
from research.scenario_dsl.models import stable_hash
from research.study.package import write_json
from research.study_v4.design import ROOT
from research.study_v4.oracle import adapt_calibration, revised_evaluate
from research.study_v4.runtime import DATABASE


def qualify(trace: dict[str, Any], raw: list[dict[str, Any]]) -> dict[str, Any]:
    case = trace["input"]
    barriers = {b["name"]: b for b in trace["barriers"]}
    targets = {t["revision"]: t for t in trace["targets"]}
    name = case["generator_family"]
    proof: list[str] = []
    gaps: list[str] = []
    snapshot = trace.get("snapshot", {})
    truth = snapshot.get("truth", [])
    accepted = targets.get(2, {}).get("accepted_at")
    if case["stratum"] == "CLEAN":
        if trace.get("grade", {}).get("correct_final_update") == "TRUE":
            proof.append("Independent final truth and supported complete update")
        else:
            gaps.append("Clean complete supported update not evidenced")
    elif case["provider"]["held_barriers"]:
        marker = next(
            (
                b
                for b in trace["barriers"]
                if b["name"] in ("COMMIT_LOG_APPENDED", "DISPATCHED_BEFORE_COMMIT")
            ),
            None,
        )
        if marker and accepted:
            response = trace.get("boundary_dispatch_result")
            pg = marker["provider_barrier"]
            if (
                pg.get("reached_at")
                and _instant(pg["reached_at"]) < _instant(accepted)
                and response
            ):
                proof.append("Durable provider barrier reached before revision acceptance")
            else:
                gaps.append("Provider barrier ordering incomplete")
            if marker["name"] == "COMMIT_LOG_APPENDED" and not any(
                _instant(t["committed_at"]) < _instant(accepted) for t in truth
            ):
                gaps.append("Hidden commit not independently established before correction")
        else:
            gaps.append("Held provider boundary not observed")
        dispatch = next((r for r in trace["http"] if r["path"] == "/internal/phase2/step"), None)
        if dispatch and accepted and _instant(dispatch["received_at"]) >= _instant(accepted):
            proof.append("Actual dispatch response receipt follows accepted correction")
        else:
            gaps.append("Response receipt ordering not established")
    else:
        # Hook names alone never certify the semantic and causal preconditions.
        hooks = case["fault_schedule"]
        established = set(barriers)
        playback = trace["client_playback"]
        if name == "verified-stale-attempt":
            verified = barriers.get("VERIFIED_BEFORE_CORRECTION")
            attempted = trace.get("unsafe_attempt", {})
            if (
                verified
                and accepted
                and attempted.get("status") == 409
                and _instant(verified["at"])
                < _instant(accepted)
                < _instant(attempted["received_at"])
            ):
                established.update(("VERIFIED", "OLD_CLAIM_ATTEMPT"))
                proof.append(
                    "Recorded verification, acceptance and normal-path 409 in causal order"
                )
        if name == "version-change-before-start":
            if (
                "VERSION_ONLY_CHANGE" in barriers
                and "START_ATTEMPT" in barriers
                and any(t["action"] == "CONCURRENT_CHANGE" for t in truth)
            ):
                proof.append("Independent version-change effect and recorded STARTED decision")
        if name == "concurrent-resource-change":
            if "VERIFIED" in barriers and any(t["action"] == "CONCURRENT_CHANGE" for t in truth):
                established.add("EXTERNAL_VERSION_CHANGE")
                proof.append("Independent concurrent version change follows recorded verification")
        if name == "late-decisive-ack" and accepted:
            delayed = [
                p
                for p in playback
                if p["request"]["event_type"] == "PROGRESS"
                and p["request"]["last_word_index"] == 8
                and _instant(p["request"]["client_time"])
                < _instant(accepted)
                < _instant(p["server_received_at"])
                and p["status"] == 202
            ]
            if len(delayed) >= 2 and "DECISIVE_ACK_WITHHELD" in barriers:
                established.update(("ACK_WITHHELD", "ACK_DELIVERED"))
                proof.append(
                    "Actual client/server clocks prove late decisive ACK and duplicate acceptance"
                )
        if name == "restart-before-repair":
            checkpoints = [
                c for c in trace["checkpoints"] if c["name"] == "persisted-before-worker-restart"
            ]
            stops = [
                p
                for p in trace["processes"]
                if p["event"] == "PROCESS_STOPPED" and p["name"] == "worker"
            ]
            starts = [
                p
                for p in trace["processes"]
                if p["event"] == "PROCESS_STARTED" and p["name"] == "worker"
            ]
            if checkpoints and stops and len({p["pid"] for p in starts}) > 1:
                established.update(("FULL_ACK", "REPAIR_PERSISTED_OR_ABLATED", "WORKER_RESTART"))
                proof.append(
                    "PG checkpoint precedes worker PID replacement; baseline response retained"
                )
        if name == "reconnect-third-revision" and targets.get(3):
            third = _instant(targets[3]["accepted_at"])
            delayed = [
                p
                for p in playback
                if p["request"]["event_type"] == "COMPLETED"
                and _instant(p["request"]["client_time"])
                < third
                < _instant(p["server_received_at"])
            ]
            if delayed and "ACK_MISSING" in barriers and "CLIENT_RECONNECT" in barriers:
                established.update(("R2_ACCEPTED", "R3_ACCEPTED"))
                proof.append(
                    "Logical reconnect and delayed completion cross recorded R3 acceptance"
                )
        if name in ("resource-only", "redis-loss"):
            unknown = barriers.get("UNKNOWN_BEFORE_CORRECTION", {})
            if any(
                o["effect_knowledge"] == "UNKNOWN"
                for o in unknown.get("history", {}).get("operations", [])
            ):
                proof.append("UNKNOWN persisted before accepted correction")
            else:
                gaps.append("P3 UNKNOWN before acceptance was not checkpointed")
        if name in ("precommit-5xx", "partial-effect", "duplicate-request-delivery"):
            if "FAULT_RESPONSE_BEFORE_CORRECTION" in barriers:
                proof.append(
                    "Actual worker response checkpoint precedes correction and further verification"
                )
            else:
                gaps.append("Correction placement after fault response was not qualified")
        if name == "duplicate-request-delivery" and '"idempotent_replay": true' in json.dumps(raw):
            established.add("DUPLICATE_IDEMPOTENT_REPLAY")
        missing = [h for h in hooks if h not in established]
        if missing:
            gaps.append("Named-hook semantic evidence requires review: " + ", ".join(missing))
        if not missing and hooks:
            proof.append("Named markers recorded; inspect trace for semantic qualification")
        if name == "duplicate-request-delivery":
            if "idempotent_replay" in json.dumps(raw) and len(truth) >= 1:
                proof.append("Provider idempotent replay export available")
            else:
                gaps.append("Duplicate replay result not evidenced")
        if name in ("precommit-5xx", "partial-effect"):
            proof.append("Raw operation attempt evidence exported for fault review")
        if not hooks and not proof:
            gaps.append("No explicit precondition checkpoint for this boundary")
    return {
        "status": "QUALIFIED_BOUNDARY" if proof and not gaps else "NEEDS_QUALIFICATION",
        "proof": proof,
        "gaps": gaps,
        "driver_status": trace["status"],
        "does_not_imply_successful_business_outcome": True,
        "scope": "Boundary evidence; restart comparison includes baseline ordinary response driver",
    }


def run() -> dict[str, Any]:
    executions = []
    grades = []
    for manifest_path in sorted((ROOT / "calibration").glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest["executions"]:
            path = Path(entry["path"])
            trace = json.loads(path.read_text(encoding="utf-8"))
            raw: list[dict[str, Any]] = []
            if trace.get("workflow_id"):
                with psycopg.connect(DATABASE, row_factory=dict_row) as conn:
                    raw = conn.execute(
                        "SELECT p.* FROM provider_events p JOIN operations o "
                        "ON o.id=p.operation_id WHERE o.workflow_id=%s ORDER BY p.occurred_at,p.id",
                        (trace["workflow_id"],),
                    ).fetchall()
            raw = json.loads(json.dumps(raw, default=str))
            write_json(ROOT / "raw-provider-exports" / (trace["execution_id"] + ".json"), raw)
            qualified = qualify(trace, raw)
            result: dict[str, Any] = {
                **entry,
                "purpose": manifest.get("purpose", "DEBUG_SMOKE"),
                "qualification": qualified,
                "raw_export_hash": stable_hash(raw),
            }
            try:
                case, evidence = adapt_calibration(trace)
                anchor = next(
                    (a.accepted_at for a in reversed(evidence.acceptances) if a.revision > 1), None
                )
                grade, row = revised_evaluate(case, evidence, challenge_at=anchor)
                result["revised_values"] = grade["values"]
                grades.append(
                    {
                        "classification": "CALIBRATION_NOT_MAIN_CAMPAIGN",
                        "path": entry["path"],
                        "grade": grade,
                        "analysis_row": row.model_dump(mode="json"),
                    }
                )
            except (KeyError, ValueError, TypeError) as error:
                result["evidence_invalid"] = {"type": type(error).__name__, "detail": str(error)}
            executions.append(result)
    output = {
        "classification": "CALIBRATION_NOT_MAIN_CAMPAIGN",
        "main_started": False,
        "all_attempts": executions,
        "driver_status_counts": dict(Counter(e["status"] for e in executions)),
        "qualification_counts": dict(Counter(e["qualification"]["status"] for e in executions)),
        "oracle_valid": len(grades),
        "oracle_invalid": len(executions) - len(grades),
        "budget_verdict": "Every budget needs boundary evidence; source constants are insufficient",
        "readiness": "NOT_READY_TO_FREEZE",
    }
    write_json(ROOT / "calibration-qualification.json", output)
    write_json(ROOT / "calibration-grades.json", grades)
    return {k: v for k, v in output.items() if k != "all_attempts"}


if __name__ == "__main__":
    print(run())
