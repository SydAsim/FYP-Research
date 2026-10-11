"""Short PostgreSQL transactions for frozen research runs and client observations."""

import json
import os
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from research.analysis.metrics import metric_rows
from research.oracle.grade import ORACLE_VERSION, PlaybackAck
from research.scenario_dsl.models import CleanScenarioCase, ScenarioCase, stable_hash

MIGRATION_VERSION = "0011_phase6_b3_audio"


def connection() -> psycopg.Connection[Any]:
    dsn = os.environ.get(
        "DATABASE_SYNC_URL",
        "postgresql://voice_agent:voice_agent_local@127.0.0.1:5432/voice_agent",
    )
    return psycopg.connect(dsn, row_factory=dict_row, connect_timeout=5, options="-c timezone=UTC")


def create_run(
    manifest: dict[str, Any], source_commit: str, analysis_version: str = "phase6-primary-v1"
) -> tuple[UUID, str, dict[str, Any]]:
    run_id = uuid4()
    frozen = {**manifest, "run_id": str(run_id), "frozen_at_utc": datetime.now(UTC).isoformat()}
    digest = stable_hash(frozen)
    with connection() as conn:
        conn.execute(
            "INSERT INTO evaluation_runs (id,name,status,manifest_json,manifest_hash,"
            "source_commit,migration_version,analysis_version,frozen_at) "
            "VALUES (%s,%s,'FROZEN',%s,%s,%s,%s,%s,now())",
            (
                run_id,
                manifest["name"],
                Jsonb(frozen),
                digest,
                source_commit,
                MIGRATION_VERSION,
                analysis_version,
            ),
        )
    return run_id, digest, frozen


def create_case(
    run_id: UUID, case: ScenarioCase | CleanScenarioCase, placement: dict[str, Any]
) -> UUID:
    case_id = uuid4()
    with connection() as conn:
        conn.execute(
            "INSERT INTO scenario_cases (id,run_id,scenario_key,fixture_hash,"
            "externally_specified_final_intent,fault_schedule,seed) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (
                case_id,
                run_id,
                case.scenario_key,
                case.fixture_hash,
                Jsonb(case.final_intent),
                Jsonb(placement),
                case.seed,
            ),
        )
    return case_id


def create_execution(run_id: UUID, case_id: UUID, arm: str, repetition: int) -> UUID:
    execution_id = uuid4()
    with connection() as conn:
        conn.execute(
            "INSERT INTO executions (id,run_id,case_id,system_arm,repetition,status,started_at) "
            "VALUES (%s,%s,%s,%s,%s,'RUNNING',now())",
            (execution_id, run_id, case_id, arm, repetition),
        )
        conn.execute("UPDATE evaluation_runs SET status='RUNNING' WHERE id=%s", (run_id,))
    return execution_id


def record_barrier(
    execution_id: UUID,
    name: str,
    source_event_id: str,
    reached_at: datetime,
    *,
    held: bool = False,
) -> UUID:
    event_id = uuid4()
    with connection() as conn:
        conn.execute(
            "INSERT INTO research_barrier_events "
            "(id,execution_id,barrier_name,ordinal,state,source_event_id,reached_at,released_at) "
            "VALUES (%s,%s,%s,1,%s,%s,%s,%s)",
            (
                event_id,
                execution_id,
                name,
                "REACHED" if held else "RELEASED",
                source_event_id,
                reached_at,
                None if held else datetime.now(UTC),
            ),
        )
    return event_id


def release_barrier(event_id: UUID) -> None:
    with connection() as conn:
        row = conn.execute(
            "UPDATE research_barrier_events SET state='RELEASED',released_at=now() "
            "WHERE id=%s AND state='REACHED' RETURNING id",
            (event_id,),
        ).fetchone()
        if row is None:
            raise ValueError("Barrier was not held or does not exist")


def record_fault(
    execution_id: UUID,
    barrier: str,
    fault: str,
    target: dict[str, Any],
    event_id: UUID,
) -> UUID:
    fault_id = uuid4()
    with connection() as conn:
        conn.execute(
            "INSERT INTO fault_occurrences (id,execution_id,barrier_name,fault_type,"
            "scheduled_target,actual_event_id,injected_at,parameters) "
            "VALUES (%s,%s,%s,%s,%s,%s,now(),%s)",
            (
                fault_id,
                execution_id,
                barrier,
                fault,
                Jsonb(target),
                event_id,
                Jsonb({"placement_hash": stable_hash(target)}),
            ),
        )
    return fault_id


def timing_evidence(execution_id: UUID) -> dict[str, Any]:
    with connection() as conn:
        barriers = conn.execute(
            "SELECT id,barrier_name,ordinal,state,source_event_id,reached_at,released_at "
            "FROM research_barrier_events WHERE execution_id=%s ORDER BY reached_at,id",
            (execution_id,),
        ).fetchall()
        faults = conn.execute(
            "SELECT id,barrier_name,fault_type,scheduled_target,actual_event_id,"
            "injected_at,parameters FROM fault_occurrences WHERE execution_id=%s "
            "ORDER BY injected_at,id",
            (execution_id,),
        ).fetchall()
    return cast(
        dict[str, Any],
        json.loads(json.dumps({"barriers": barriers, "faults": faults}, default=str)),
    )


def record_baseline_event(
    execution_id: UUID,
    ordinal: int,
    event_kind: str,
    raw: dict[str, Any],
    normalized: dict[str, Any],
    trace_id: str,
) -> None:
    content_hash = stable_hash({"event_kind": event_kind, "raw": raw, "normalized": normalized})
    with connection() as conn:
        conn.execute(
            "INSERT INTO research_baseline_events (id,execution_id,ordinal,event_kind,"
            "raw_json,normalized_json,content_hash,trace_id,occurred_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                uuid4(),
                execution_id,
                ordinal,
                event_kind,
                Jsonb(raw),
                Jsonb(normalized),
                content_hash,
                trace_id,
                datetime.now(UTC),
            ),
        )


def baseline_events_for(execution_id: UUID) -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT ordinal,event_kind,raw_json,normalized_json,content_hash,trace_id,occurred_at "
            "FROM research_baseline_events WHERE execution_id=%s ORDER BY ordinal",
            (execution_id,),
        ).fetchall()
    return cast(list[dict[str, Any]], json.loads(json.dumps(rows, default=str)))


def bind_execution(
    execution_id: UUID,
    scenario_id: UUID,
    workflow_id: UUID,
    schedule_hash: str,
    corrected_at: datetime,
) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE executions SET simulator_scenario_id=%s,workflow_id=%s,"
            "fault_schedule_hash=%s,correction_scripted_at=%s WHERE id=%s",
            (scenario_id, workflow_id, schedule_hash, corrected_at, execution_id),
        )


def bind_clean_execution(
    execution_id: UUID, scenario_id: UUID, workflow_id: UUID, schedule_hash: str
) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE executions SET simulator_scenario_id=%s,workflow_id=%s,"
            "fault_schedule_hash=%s WHERE id=%s",
            (scenario_id, workflow_id, schedule_hash, execution_id),
        )


def record_playback(execution_id: UUID, ack: PlaybackAck, audio_hash: str) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO research_playback_acks (event_id,execution_id,claim_type,"
            "claim_start,intent_revision,released_at,played_at,played_ms,permit_id,audio_hash) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                UUID(ack.event_id),
                execution_id,
                ack.claim_type,
                ack.claim_start,
                ack.intent_revision,
                ack.released_at,
                ack.played_at,
                ack.played_ms,
                UUID(ack.permit_id) if ack.permit_id else None,
                audio_hash,
            ),
        )


def playback_for(execution_id: UUID) -> list[PlaybackAck]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT event_id,claim_type,claim_start,intent_revision,released_at,"
            "played_at,played_ms,permit_id FROM research_playback_acks "
            "WHERE execution_id=%s ORDER BY played_at,event_id",
            (execution_id,),
        ).fetchall()
    return [
        PlaybackAck.model_validate(
            {
                key: str(value) if key in ("event_id", "permit_id") and value else value
                for key, value in row.items()
            }
        )
        for row in rows
    ]


def record_result(
    execution_id: UUID,
    case: ScenarioCase | CleanScenarioCase,
    truth: list[dict[str, Any]],
    result: dict[str, Any],
) -> None:
    rows = metric_rows(result)
    with connection() as conn:
        conn.execute(
            "INSERT INTO oracle_results (execution_id,oracle_version,actual_provider_truth,"
            "final_intent,valid_outcomes,forbidden_effects,result_json,result_hash,evaluated_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,now())",
            (
                execution_id,
                result.get("oracle_version", ORACLE_VERSION),
                Jsonb(json.loads(json.dumps(truth, default=str))),
                Jsonb(case.final_intent),
                Jsonb({"one_confirmed_at": case.final_start.isoformat()}),
                Jsonb({"extra_active": True, "duplicate_logical_effect": True}),
                Jsonb(result),
                result["result_hash"],
            ),
        )
        for row in rows:
            conn.execute(
                "INSERT INTO metrics (execution_id,metric_name,metric_version,numeric_value,"
                "categorical_value,numerator,denominator,details) "
                "VALUES (%s,%s,%s,%s,NULL,%s,%s,%s)",
                (
                    execution_id,
                    row["metric_name"],
                    row["metric_version"],
                    row["numeric_value"],
                    row["numerator"],
                    row["denominator"],
                    Jsonb(row["details"]),
                ),
            )
        conn.execute(
            "UPDATE executions SET status='COMPLETED',completed_at=now() WHERE id=%s",
            (execution_id,),
        )


def finish_run(run_id: UUID) -> None:
    with connection() as conn:
        pending = conn.execute(
            "SELECT count(*) AS n FROM executions WHERE run_id=%s AND status!='COMPLETED'",
            (run_id,),
        ).fetchone()
        assert pending is not None
        if pending["n"] != 0:
            raise ValueError("Run has unfinished executions")
        conn.execute(
            "UPDATE evaluation_runs SET status='COMPLETED',completed_at=now() WHERE id=%s",
            (run_id,),
        )


def fail_execution(run_id: UUID, execution_id: UUID, trace_id: str, reason: str) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE executions SET status='FAILED',completed_at=now(),exclusion_reason=%s "
            "WHERE id=%s AND status='RUNNING'",
            (f"trace_id={trace_id}; reason={reason[:300]}", execution_id),
        )
        conn.execute(
            "UPDATE evaluation_runs SET status='FAILED',completed_at=now() WHERE id=%s",
            (run_id,),
        )
