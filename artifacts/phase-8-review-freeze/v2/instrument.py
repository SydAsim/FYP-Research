"""Same revised observable oracle, with explicit authorized main metadata adapter."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from typing import Any

from controls import Authority

from research.arms import Arm  # noqa: E402
from research.execution_setup.timing import paired_latency
from research.study.models import Acceptance, AnalysisRow, Evidence, StudyCase
from research.study.statistical_models import aft_cluster_bootstrap, lognormal_aft
from research.study_v4.analysis import outcome_report
from research.study_v4.oracle import revised_evaluate


def adapt_trace(trace: dict[str, Any]) -> tuple[StudyCase, Evidence]:
    case = StudyCase.model_validate(trace["input"])
    snapshot = trace["snapshot"]
    revisions = {r["revision"]: r for r in snapshot["history"]["revisions"]}
    anchors = []
    for target in trace["targets"]:
        actual = revisions[target["revision"]]["desired_state_json"]
        anchors.append(
            Acceptance(
                revision=target["revision"],
                scripted_at=target["scripted_at"],
                accepted_at=revisions[target["revision"]]["accepted_at"],
                actual_start=actual["requested_start"],
                actual_end=actual["requested_end"],
                actual_timezone=actual["timezone"],
            )
        )
    evidence = Evidence.model_validate(
        {
            "classification": "CAMPAIGN"
            if trace["classification"] == "CAMPAIGN"
            else "VALIDATION_ONLY",
            "case_id": case.case_id,
            "arm": trace["arm"],
            "attempt": 1,
            "execution_id": trace["execution_id"],
            "fixture_hash": case.fixture_hash,
            "started_at": trace["started_at"],
            "ended_at": trace["finished_at"],
            "status": {"FAILED": "INFRASTRUCTURE_FAILURE"}.get(trace["status"], trace["status"]),
            "resource_key": trace["targets"][0]["resource_key"],
            "acceptances": anchors,
            "truth": snapshot["truth"],
            "segments": snapshot["segments"],
            "playback": trace["client_playback"],
            "observations": snapshot["observations"],
            "truth_complete": True,
            "publication_journal_complete": True,
            "playback_journal_complete": True,
            "independent_truth_source": "SIMULATOR_APPEND_ONLY_ORACLE_EXPORT",
            "raw_trace_hash": trace["trace_hash"],
            "repair_obligations": snapshot["obligations"],
            "repair_journal_complete": True,
        }
    )
    return case, evidence


def evidence_for(trace: dict[str, Any]) -> tuple[StudyCase, Evidence]:
    case, evidence = adapt_trace(trace)
    revisions = {r["revision"]: r for r in trace["snapshot"]["history"]["revisions"]}
    anchors = []
    for issued in trace["external_requests"]:
        revision = revisions.get(issued["revision"])
        actual = revision["desired_state_json"] if revision else {}
        anchors.append(
            Acceptance(
                revision=issued["revision"],
                scripted_at=issued["issued_at"],
                accepted_at=revision["accepted_at"] if revision else None,
                actual_start=actual.get("requested_start"),
                actual_end=actual.get("requested_end"),
                actual_timezone=actual.get("timezone"),
            )
        )
    # Prefer durable server timestamps over response-receipt proxy times.
    server = {str(p["id"]): p["server_received_at"] for p in trace["snapshot"]["playback_rows"]}
    playback = [
        {
            **p,
            "server_received_at": server.get(
                str(p["request"]["event_id"]), p.get("server_received_at")
            ),
        }
        for p in evidence.playback
    ]
    known = {str(p["request"]["event_id"]) for p in playback}
    for event in trace["snapshot"]["playback_rows"]:
        if str(event["id"]) in known:
            continue
        playback.append(
            {
                "request": {
                    "event_id": str(event["id"]),
                    "segment_id": str(event["segment_id"]),
                    "event_type": event["event_type"],
                    "client_time": event["client_time"],
                    "played_ms": event["played_ms"] or 0,
                    "last_frame": event["last_frame"] or 0,
                    "last_word_index": event["last_word_index"] or 0,
                },
                "response": event["response_json"],
                "status": 202,
                "server_received_at": event["server_received_at"],
                "source": "DURABLE_SERVER_ACK_JOURNAL_NOT_SYNTHESIZED_HUMAN_EVIDENCE",
            }
        )
    gaps = bool(trace.get("collection_errors"))
    return case, evidence.model_copy(
        update={
            "attempt": trace["attempt"],
            "acceptances": anchors,
            "playback": playback,
            "truth_complete": not gaps,
            "publication_journal_complete": not gaps,
            "playback_journal_complete": not gaps,
            "repair_journal_complete": not gaps,
        }
    )


def evaluate_trace(
    trace: dict[str, Any], authority: Authority | None = None
) -> tuple[dict[str, Any], AnalysisRow]:
    if trace["classification"] == "CAMPAIGN":
        if authority is None or authority.policy.scope != "CAMPAIGN":
            raise ValueError("MAIN_ANALYSIS_AUTHORIZATION_REQUIRED")
        authority.verify(authority.policy.host_started_at)  # Read-only postflight after expiry.
        from controls import read

        bank = read(authority.source / "research/fixtures/phase8_design_v4/inputs.json")
        expected = {
            c["case_id"]: StudyCase.model_validate(c).fixture_hash for c in bank["main_inputs"]
        }
        case = StudyCase.model_validate(trace["input"])
        if expected.get(case.case_id) != case.fixture_hash or trace["attempt"] != 1:
            raise ValueError("MAIN_ORIGINAL_FIXTURE_BINDING_REQUIRED")
    elif trace["classification"] != "CALIBRATION_NOT_MAIN_CAMPAIGN" or not trace["input"][
        "case_id"
    ].startswith("cal-v4-"):
        raise ValueError("CALIBRATION_SCOPE_REQUIRED")
    case, evidence = evidence_for(trace)
    anchors = [a.accepted_at for a in evidence.acceptances if a.revision > 1 and a.accepted_at]
    return revised_evaluate(case, evidence, challenge_at=max(anchors) if anchors else None)


def analysis(
    cases: list[StudyCase],
    rows: list[AnalysisRow],
    authority: Authority,
    *,
    draws: int = 2000,
    aft_draws: int = 1000,
) -> dict[str, Any]:
    authority.verify(authority.policy.host_started_at)
    campaign = authority.policy.scope == "CAMPAIGN"
    if campaign and (len(cases) != 500 or draws != 2000 or aft_draws != 1000):
        raise ValueError("FROZEN_MAIN_ANALYSIS_SETTINGS_REQUIRED")
    if any((r.classification == "CAMPAIGN") != campaign for r in rows):
        raise ValueError("ANALYSIS_SCOPE_MIXING")
    if any(r.attempt != 1 for r in rows) or len({(r.case_id, r.arm) for r in rows}) != len(rows):
        raise ValueError("ORIGINALS_ONLY_NO_REPLACEMENT_OR_DUPLICATE")
    bound = {c.case_id: c for c in cases}
    if len(bound) != len(cases):
        raise ValueError("DUPLICATE_INDEPENDENT_INPUT")
    if any(r.case_id not in bound or r.arm not in bound[r.case_id].primary_arms for r in rows):
        raise ValueError("UNPLANNED_ANALYSIS_RECORD")
    report = outcome_report(cases, rows)
    report.update(
        status="AUTHORIZED_MAIN_ANALYSIS" if campaign else "LOCAL_CALIBRATION",
        main_started=campaign,
        classification=authority.policy.scope,
    )
    input_rows = [r.model_copy(update={"cluster_id": r.case_id}) for r in rows if r.attempt == 1]
    # Same pure functions/seeds as the qualified timing adapter; no relabelling of
    # campaign records to sneak them through its historical candidate guard.
    return {
        "classification": authority.policy.scope,
        "outcomes": report,
        "latency": [
            paired_latency(cases, rows, comparison=a, reference=b, repetitions=draws)
            for a, b in ((Arm.P2, Arm.B3), (Arm.P1, Arm.B3), (Arm.P2, Arm.P1))
        ],
        "aft": lognormal_aft(input_rows),
        "aft_input_cluster_bootstrap": aft_cluster_bootstrap(
            input_rows, draws=aft_draws, seed=8042052
        ),
    }
