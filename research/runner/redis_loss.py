"""Wipe and restart the optional project cache while PostgreSQL retains facts."""

import json
import subprocess
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from research.run_store import connection
from research.scenario_dsl.models import stable_hash

ROOT = Path(__file__).resolve().parents[2]


def _redis(*arguments: str) -> str:
    # Database 15 is reserved for the research cache; the service has no host port.
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "redis", "redis-cli", "-n", "15", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return result.stdout.strip()


def durable_snapshot(workflow_id: UUID) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    with connection() as conn:
        for table in (
            "workflows",
            "intent_revisions",
            "operations",
            "verification_receipts",
            "claim_permits",
            "repair_obligations",
        ):
            column = "id" if table == "workflows" else "workflow_id"
            rows = conn.execute(
                f"SELECT to_jsonb(t) AS facts FROM {table} t WHERE {column}=%s ORDER BY id",
                (workflow_id,),
            ).fetchall()
            facts[table] = [row["facts"] for row in rows]
    return facts


def wipe_cache(workflow_id: UUID) -> dict[str, Any]:
    before = durable_snapshot(workflow_id)
    key = f"phase6:hint:{workflow_id}"
    value = stable_hash(before)
    if _redis("SET", key, value) != "OK" or _redis("GET", key) != value:
        raise AssertionError("Research Redis hint was not stored")
    flushed = _redis("FLUSHDB", "SYNC")
    after_flush = _redis("DBSIZE")
    subprocess.run(
        ["docker", "compose", "restart", "redis"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        timeout=30,
    )
    subprocess.run(
        ["docker", "compose", "--profile", "redis", "up", "-d", "--wait", "redis"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        timeout=45,
    )
    ping = _redis("PING")
    after_restart = _redis("GET", key)
    after = durable_snapshot(workflow_id)
    if flushed != "OK" or after_flush != "0" or ping != "PONG" or after_restart or before != after:
        raise AssertionError("Cache loss changed a durable correctness fact")
    # JSON data is already durable PostgreSQL row evidence; no Redis fact grades the oracle.
    return cast(
        dict[str, Any],
        json.loads(
            json.dumps(
                {
                    "database": 15,
                    "hint_key": key,
                    "hint_hash": value,
                    "flush_result": flushed,
                    "keys_after_flush": 0,
                    "restart_ping": ping,
                    "hint_after_restart": after_restart,
                    "before": before,
                    "after": after,
                    "durable_hash": stable_hash(after),
                },
                default=str,
            )
        ),
    )
