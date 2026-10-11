"""Separate real clock/HTTP/PG boundary probes; never main input execution."""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Event, Thread
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row

from apps.durable_worker.phase2 import lease_one
from apps.durable_worker.repair import discover
from apps.voice_worker.scheduler import HttpControllerPort
from packages.provider_adapters.simulator import exchange
from research.arms import Arm
from research.remedies.runner import now
from research.study.package import write_json
from research.study_v4.calibration import CalibrationTrial
from research.study_v4.design import ROOT, materialize
from research.study_v4.runtime import DATABASE, Runtime, prepare_databases


def deadline(at: datetime) -> None:
    """Wait on a clock boundary, never position a race by an arbitrary sleep."""
    while (seconds := (at - datetime.now(UTC)).total_seconds()) > 0:
        Event().wait(min(seconds, 1))


def http_probes(directory: Path) -> list[dict[str, Any]]:
    release = Event()
    reached: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            reached.append(self.path)
            release.wait(90)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    prior = os.environ.get("SIMULATOR_BASE_URL")
    os.environ["SIMULATOR_BASE_URL"] = base
    trial = CalibrationTrial(
        Runtime(directory / "unused"), materialize(calibration=True)[0], Arm.B3, directory
    )

    def probe(name: str, seconds: int) -> dict[str, Any]:
        start, began = time.monotonic(), now()
        try:
            if name == "provider":
                result = exchange("GET", "/provider-timeout")
                outcome = "TRANSPORT_ERROR" if result.transport_error else "UNEXPECTED_RESPONSE"
            elif name == "scheduler":
                HttpControllerPort(base).get("/scheduler-timeout")
                outcome = "UNEXPECTED_RESPONSE"
            else:
                trial.request(base, "GET", "/runner-timeout")
                outcome = "UNEXPECTED_RESPONSE"
        except TimeoutError:
            outcome = "TimeoutError"
        elapsed = time.monotonic() - start
        return {
            "budget": name,
            "configured_seconds": seconds,
            "started_at": began,
            "ended_at": now(),
            "elapsed_seconds": elapsed,
            "outcome": outcome,
            "qualified": seconds <= elapsed < seconds + 5 and outcome != "UNEXPECTED_RESPONSE",
            "scope": "REAL_HTTP_SOCKET_TIMEOUT_NOT_END_TO_END_BUSINESS_RECOVERY",
        }

    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(
                pool.map(
                    lambda pair: probe(*pair), [("provider", 30), ("scheduler", 15), ("runner", 40)]
                )
            )
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        if prior is None:
            os.environ.pop("SIMULATOR_BASE_URL", None)
        else:
            os.environ["SIMULATOR_BASE_URL"] = prior
    write_json(
        directory / "http-boundaries.json", {"requests_reached": reached, "results": results}
    )
    return results


def durable_probes(directory: Path) -> list[dict[str, Any]]:
    prepare_databases()
    results: list[dict[str, Any]] = []
    with Runtime(directory / "logs") as runtime:
        prior = os.environ.get("DATABASE_SYNC_URL")
        os.environ["DATABASE_SYNC_URL"] = DATABASE
        try:
            core = CalibrationTrial(runtime, materialize(calibration=True)[0], Arm.B3, directory)
            operation = core.initialize()
            lease = lease_one("budget-first", UUID(operation))
            assert lease is not None
            assert lease_one("budget-contender", UUID(operation)) is None
            with psycopg.connect(DATABASE, row_factory=dict_row) as conn:
                job = conn.execute(
                    "SELECT * FROM reconciliation_jobs WHERE id=%s", (lease.id,)
                ).fetchone()
            assert job is not None

            repair = CalibrationTrial(runtime, materialize(calibration=True)[38], Arm.P2, directory)
            op = repair.setup()
            repair.full(repair.schedule(op, 1))
            repair.revision(2, 16)
            repair.drain()
            obligation = discover("budget-repair-first", UUID(repair.item["workflow_id"]))
            assert obligation is not None
            assert discover("budget-repair-contender", UUID(repair.item["workflow_id"])) is None
            with psycopg.connect(DATABASE, row_factory=dict_row) as conn:
                held = conn.execute(
                    "SELECT * FROM repair_obligations WHERE id=%s", (obligation["id"],)
                ).fetchone()
            assert held is not None
            # Expiry probe uses another fresh verified operation, without publishing.
            ttl = CalibrationTrial(runtime, materialize(calibration=True)[0], Arm.P1, directory)
            ttl_op = ttl.setup()
            staged = ttl.stage(ttl_op, 1)
            with psycopg.connect(DATABASE, row_factory=dict_row) as conn:
                permit = conn.execute(
                    "SELECT * FROM claim_permits WHERE id=%s", (staged["claim_permit_id"],)
                ).fetchone()
            assert permit is not None
            write_json(
                directory / "durable-preconditions.json",
                json.loads(
                    json.dumps({"core_job": job, "repair": held, "permit": permit}, default=str)
                ),
            )

            def core_expiry() -> dict[str, Any]:
                deadline(job["lease_until"])
                reclaimed = lease_one("budget-after-expiry", UUID(operation))
                return {
                    "budget": "core_lease",
                    "seconds": 180,
                    "qualified": reclaimed is not None,
                    "lease_until": str(job["lease_until"]),
                    "observed_at": now(),
                    "reclaimed_job": str(reclaimed.id) if reclaimed else None,
                    "scope": "REAL_PG_CONTENTION_AND_NATURAL_EXPIRY_NO_TIMESTAMP_EDIT",
                }

            def repair_expiry() -> dict[str, Any]:
                deadline(held["delivery_lease_until"])
                recovered = discover("budget-repair-after-expiry", UUID(repair.item["workflow_id"]))
                return {
                    "budget": "repair_lease",
                    "seconds": 30,
                    "qualified": recovered is not None,
                    "lease_until": str(held["delivery_lease_until"]),
                    "observed_at": now(),
                    "scope": "REAL_PG_CONTENTION_AND_NATURAL_EXPIRY_NOT_CRASH_RECOVERY",
                }

            def permit_expiry() -> dict[str, Any]:
                from research.study_v4.runtime import API

                deadline(permit["expires_at"])
                ttl.request(
                    API,
                    "POST",
                    f"/internal/phase4/audio-segments/{staged['id']}/release",
                    {"command_id": str(uuid4()), "expected_intent_revision": 1},
                    allow_failure=True,
                )
                response = ttl.row["http"][-1]
                return {
                    "budget": "permit_ttl",
                    "seconds": 30,
                    "qualified": response["status"] == 409,
                    "expires_at": str(permit["expires_at"]),
                    "response": response,
                    "scope": "REAL_PG_EXPIRED_PERMIT_PUBLICATION_REJECTION",
                }

            with ThreadPoolExecutor(max_workers=3) as pool:
                for result in pool.map(
                    lambda fn: fn(), (core_expiry, repair_expiry, permit_expiry)
                ):
                    results.append(result)
                    write_json(directory / "durable-boundaries.json", results)
            core.row.update(snapshot=core.snapshot(), finished_at=now())
            core.save()
            repair.row.update(snapshot=repair.snapshot(), finished_at=now())
            repair.save()
        finally:
            if prior is None:
                os.environ.pop("DATABASE_SYNC_URL", None)
            else:
                os.environ["DATABASE_SYNC_URL"] = prior
    return results


def main() -> None:
    directory = ROOT / "budget-calibration" / str(uuid4())
    directory.mkdir(parents=True, exist_ok=False)
    write_json(
        directory / "plan.json",
        {
            "classification": "CALIBRATION_NOT_MAIN_CAMPAIGN",
            "planned_at": now(),
            "budgets": [
                "provider",
                "scheduler",
                "runner",
                "core_lease",
                "repair_lease",
                "permit_ttl",
            ],
            "other_budgets": "Require separate qualification; not inferred from source constants",
            "main_started": False,
        },
    )
    results = http_probes(directory) + durable_probes(directory)
    write_json(directory / "results.json", results)
    print(directory, flush=True)


if __name__ == "__main__":
    main()
