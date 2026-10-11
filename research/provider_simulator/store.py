"""Independent PostgreSQL truth store for the deterministic provider."""

import os
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from research.provider_simulator.models import (
    ProviderAction,
    ProviderOperation,
    ScenarioConfig,
    Visibility,
)


class SimulatorConflict(Exception):
    pass


def connection() -> psycopg.Connection[Any]:
    dsn = os.environ.get(
        "SIMULATOR_DATABASE_URL",
        "postgresql://simulator:simulator_local@127.0.0.1:5433/simulator_truth",
    )
    return psycopg.connect(dsn, row_factory=dict_row, connect_timeout=5, options="-c timezone=UTC")


def bootstrap() -> None:
    ddl = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
    with connection() as conn:
        conn.execute(ddl, prepare=False)


def create_scenario(config: ScenarioConfig) -> UUID:
    scenario_id = uuid4()
    with connection() as conn:
        conn.execute(
            "INSERT INTO simulator_scenarios (id,config_json) VALUES (%s,%s)",
            (scenario_id, Jsonb(config.model_dump(mode="json"))),
        )
        for barrier in config.held_barriers:
            conn.execute(
                "INSERT INTO simulator_barriers (scenario_id,barrier_name,state) VALUES (%s,%s,'HELD')",
                (scenario_id, barrier),
            )
    return scenario_id


def scenario_config(scenario_id: UUID) -> ScenarioConfig:
    with connection() as conn:
        row = conn.execute(
            "SELECT config_json FROM simulator_scenarios WHERE id=%s", (scenario_id,)
        ).fetchone()
    if row is None:
        raise KeyError("Unknown simulator scenario")
    return ScenarioConfig.model_validate(row["config_json"])


def next_request_index(scenario_id: UUID) -> int:
    with connection() as conn:
        row = conn.execute(
            "UPDATE simulator_scenarios SET request_count=request_count+1 "
            "WHERE id=%s RETURNING request_count",
            (scenario_id,),
        ).fetchone()
    if row is None:
        raise KeyError("Unknown simulator scenario")
    value: int = row["request_count"]
    return value


def barrier_state(scenario_id: UUID, barrier_name: str) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute(
            "SELECT state,reached_at,released_at FROM simulator_barriers "
            "WHERE scenario_id=%s AND barrier_name=%s",
            (scenario_id, barrier_name),
        ).fetchone()
    return row


def reach_barrier(scenario_id: UUID, barrier_name: str) -> bool:
    """Persist a named barrier and return whether the request must wait."""
    with connection() as conn:
        row = conn.execute(
            "INSERT INTO simulator_barriers (scenario_id,barrier_name,state,reached_at) "
            "VALUES (%s,%s,'RELEASED',now()) "
            "ON CONFLICT (scenario_id,barrier_name) DO UPDATE SET "
            "reached_at=COALESCE(simulator_barriers.reached_at,now()), "
            "state=CASE WHEN simulator_barriers.state='HELD' THEN 'REACHED' "
            "ELSE simulator_barriers.state END RETURNING state",
            (scenario_id, barrier_name),
        ).fetchone()
    assert row is not None
    held: bool = row["state"] == "REACHED"
    return held


def release_barrier(scenario_id: UUID, barrier_name: str) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO simulator_barriers (scenario_id,barrier_name,state,released_at) "
            "VALUES (%s,%s,'RELEASED',now()) "
            "ON CONFLICT (scenario_id,barrier_name) DO UPDATE SET state='RELEASED',released_at=now()",
            (scenario_id, barrier_name),
        )


def _facts(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "appointment_id": str(row["id"]),
        "resource_key": row["resource_key"],
        "starts_at": row["starts_at"].isoformat(),
        "ends_at": row["ends_at"].isoformat(),
        "timezone": row["timezone"],
        "status": row["status"],
        "version": row["version"],
    }


def inject_concurrent_change(request: ProviderOperation) -> None:
    """Create a separate append-only competing effect before the requested write."""
    if request.appointment_id is None:
        return
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM provider_appointments WHERE id=%s AND scenario_id=%s FOR UPDATE",
            (request.appointment_id, request.scenario_id),
        ).fetchone()
        if row is None:
            return
        before = _facts(row)
        changed = conn.execute(
            "UPDATE provider_appointments SET version=version+1,updated_at=now() "
            "WHERE id=%s RETURNING *",
            (request.appointment_id,),
        ).fetchone()
        conn.execute(
            "INSERT INTO provider_commits (scenario_id,action,appointment_id,resource_key,"
            "before_facts,after_facts,result_code) VALUES (%s,'CONCURRENT_CHANGE',%s,%s,%s,%s,'PRESENT')",
            (
                request.scenario_id,
                request.appointment_id,
                request.resource_key,
                Jsonb(before),
                Jsonb(_facts(changed)),
            ),
        )


def apply_operation(
    request: ProviderOperation, config: ScenarioConfig, partial: bool = False
) -> dict[str, Any]:
    """Apply one provider write and append its immutable truth entry atomically."""
    with connection() as conn:
        if config.idempotency:
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                (f"{request.scenario_id}:{request.idempotency_key}",),
            )
            prior = conn.execute(
                "SELECT request_hash,result_json FROM provider_requests "
                "WHERE scenario_id=%s AND idempotency_key=%s ORDER BY id DESC LIMIT 1",
                (request.scenario_id, request.idempotency_key),
            ).fetchone()
            if prior is not None:
                if prior["request_hash"] != request.request_hash:
                    raise SimulatorConflict("Idempotency key used with changed request hash")
                result: dict[str, Any] = prior["result_json"]
                return {**result, "idempotent_replay": True}

        before: dict[str, Any] | None = None
        if request.action is ProviderAction.CREATE:
            if (
                request.requested_start is None
                or request.requested_end is None
                or request.timezone is None
            ):
                raise SimulatorConflict("Missing requested appointment time")
            conflict = conn.execute(
                "SELECT id FROM provider_appointments WHERE scenario_id=%s AND resource_key=%s "
                "AND status IN ('CONFIRMED','HELD') AND starts_at<%s AND ends_at>%s LIMIT 1",
                (
                    request.scenario_id,
                    request.resource_key,
                    request.requested_end,
                    request.requested_start,
                ),
            ).fetchone()
            if conflict is not None:
                raise SimulatorConflict("Provider resource slot is occupied")
            appointment_id = uuid4()
            after_row = conn.execute(
                "INSERT INTO provider_appointments "
                "(id,scenario_id,resource_key,starts_at,ends_at,timezone,status) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING *",
                (
                    appointment_id,
                    request.scenario_id,
                    request.resource_key,
                    request.requested_start,
                    request.requested_end,
                    request.timezone,
                    "HELD" if partial else "CONFIRMED",
                ),
            ).fetchone()
        else:
            if request.appointment_id is None:
                raise SimulatorConflict("Target appointment is required")
            row = conn.execute(
                "SELECT * FROM provider_appointments WHERE id=%s AND scenario_id=%s FOR UPDATE",
                (request.appointment_id, request.scenario_id),
            ).fetchone()
            if row is None:
                raise SimulatorConflict("Target appointment is absent")
            if (
                request.expected_resource_version is not None
                and row["version"] != request.expected_resource_version
            ):
                raise SimulatorConflict("Provider resource version changed")
            before = _facts(row)
            appointment_id = request.appointment_id
            if request.action is ProviderAction.RESCHEDULE:
                if not config.supports_reschedule:
                    raise SimulatorConflict("Provider does not support atomic reschedule")
                if (
                    request.requested_start is None
                    or request.requested_end is None
                    or request.timezone is None
                ):
                    raise SimulatorConflict("Missing requested appointment time")
                conflict = conn.execute(
                    "SELECT id FROM provider_appointments WHERE scenario_id=%s AND resource_key=%s "
                    "AND id<>%s AND status IN ('CONFIRMED','HELD') "
                    "AND starts_at<%s AND ends_at>%s LIMIT 1",
                    (
                        request.scenario_id,
                        request.resource_key,
                        appointment_id,
                        request.requested_end,
                        request.requested_start,
                    ),
                ).fetchone()
                if conflict is not None:
                    raise SimulatorConflict("Provider resource slot is occupied")
                after_row = conn.execute(
                    "UPDATE provider_appointments SET starts_at=%s,ends_at=%s,timezone=%s,"
                    "version=version+1,status=%s,updated_at=now() WHERE id=%s RETURNING *",
                    (
                        request.requested_start,
                        request.requested_end,
                        request.timezone,
                        "HELD" if partial else "CONFIRMED",
                        appointment_id,
                    ),
                ).fetchone()
            else:
                after_row = conn.execute(
                    "UPDATE provider_appointments SET status='CANCELLED',version=version+1,"
                    "updated_at=now() WHERE id=%s RETURNING *",
                    (appointment_id,),
                ).fetchone()
        after = _facts(after_row)
        result_code = "PARTIAL" if partial else "PRESENT"
        commit = conn.execute(
            "INSERT INTO provider_commits (scenario_id,operation_id,request_hash,idempotency_key,"
            "action,appointment_id,resource_key,before_facts,after_facts,result_code) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING sequence",
            (
                request.scenario_id,
                request.operation_id,
                request.request_hash,
                request.idempotency_key,
                request.action.value,
                appointment_id,
                request.resource_key,
                Jsonb(before),
                Jsonb(after),
                result_code,
            ),
        ).fetchone()
        assert commit is not None
        result = {
            "operation_id": str(request.operation_id),
            "appointment_id": str(appointment_id),
            "outcome": result_code,
            "resource_version": after["version"] if after else None,
            "commit_sequence": commit["sequence"],
            "facts": after,
            "idempotent_replay": False,
        }
        conn.execute(
            "INSERT INTO provider_requests (scenario_id,operation_id,request_hash,idempotency_key,"
            "result_json,commit_sequence) VALUES (%s,%s,%s,%s,%s,%s)",
            (
                request.scenario_id,
                request.operation_id,
                request.request_hash,
                request.idempotency_key,
                Jsonb(result),
                commit["sequence"],
            ),
        )
        return result


def _visible(config: ScenarioConfig, reads: int) -> bool:
    if config.visibility in (Visibility.IMMEDIATE, Visibility.STALE):
        return True
    if config.visibility is Visibility.UNAVAILABLE:
        return False
    return reads > config.visibility_reads


def operation_status(
    scenario_id: UUID, operation_id: UUID, config: ScenarioConfig
) -> dict[str, Any]:
    if not config.status_lookup:
        raise NotImplementedError("Operation status lookup is absent")
    if config.visibility is Visibility.UNAVAILABLE:
        raise ConnectionError("Provider operation status is unavailable")
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM provider_requests WHERE scenario_id=%s AND operation_id=%s "
            "ORDER BY id DESC LIMIT 1 FOR UPDATE",
            (scenario_id, operation_id),
        ).fetchone()
        if row is None:
            return {"outcome": "ABSENT", "operation_id": str(operation_id), "authoritative": True}
        read = conn.execute(
            "UPDATE provider_requests SET status_reads=status_reads+1 WHERE id=%s "
            "RETURNING status_reads",
            (row["id"],),
        ).fetchone()
        assert read is not None
        if not _visible(config, read["status_reads"]):
            return {"outcome": "UNKNOWN", "operation_id": str(operation_id), "authoritative": False}
        if config.visibility is Visibility.STALE and read["status_reads"] <= max(
            1, config.visibility_reads
        ):
            return {
                "outcome": "UNKNOWN",
                "operation_id": str(operation_id),
                "authoritative": False,
                "stale": True,
            }
        result: dict[str, Any] = row["result_json"]
        return {**result, "authoritative": True}


def resource_state(
    scenario_id: UUID, operation_id: UUID, resource_key: str, config: ScenarioConfig
) -> dict[str, Any]:
    if not config.resource_lookup:
        raise NotImplementedError("Resource lookup is absent")
    if config.visibility is Visibility.UNAVAILABLE:
        raise ConnectionError("Provider resource read is unavailable")
    with connection() as conn:
        request_row = conn.execute(
            "SELECT * FROM provider_requests WHERE scenario_id=%s AND operation_id=%s "
            "ORDER BY id DESC LIMIT 1 FOR UPDATE",
            (scenario_id, operation_id),
        ).fetchone()
        if request_row is not None:
            read = conn.execute(
                "UPDATE provider_requests SET resource_reads=resource_reads+1 WHERE id=%s "
                "RETURNING resource_reads",
                (request_row["id"],),
            ).fetchone()
            assert read is not None
            if config.visibility is Visibility.STALE and read["resource_reads"] <= max(
                1, config.visibility_reads
            ):
                return {
                    "outcome": "UNKNOWN",
                    "appointments": [],
                    "authoritative": False,
                    "stale": True,
                }
            if not _visible(config, read["resource_reads"]):
                return {"outcome": "UNKNOWN", "appointments": [], "authoritative": False}
        rows = conn.execute(
            "SELECT * FROM provider_appointments WHERE scenario_id=%s AND resource_key=%s "
            "ORDER BY created_at NULLS LAST, id",
            (scenario_id, resource_key),
        ).fetchall()
    return {
        "outcome": "PRESENT" if rows else "ABSENT",
        "appointments": [_facts(row) for row in rows],
        "authoritative": True,
    }


def truth_log(scenario_id: UUID) -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT sequence,scenario_id,operation_id,request_hash,idempotency_key,action,"
            "appointment_id,resource_key,before_facts,after_facts,result_code,committed_at "
            "FROM provider_commits WHERE scenario_id=%s ORDER BY sequence",
            (scenario_id,),
        ).fetchall()
    return rows
