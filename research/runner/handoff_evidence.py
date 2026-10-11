"""Read controller mechanism evidence; this is never an independent oracle input."""

import json
from typing import Any, cast
from uuid import UUID

from research.run_store import connection


def handoff_snapshot(workflow_id: UUID) -> dict[str, Any]:
    with connection() as conn:
        workflow = conn.execute(
            "SELECT current_revision,resolution_status FROM workflows WHERE id=%s",
            (workflow_id,),
        ).fetchone()
        if workflow is None:
            raise ValueError("Unknown workflow for handoff evidence")
        handoffs = conn.execute(
            "SELECT id,reason_code,state,known_facts,unknown_facts,linked_operation_ids "
            "FROM handoffs "
            "WHERE workflow_id=%s ORDER BY created_at,id",
            (workflow_id,),
        ).fetchall()
        jobs = conn.execute(
            "SELECT j.id,j.operation_id,j.job_type,j.state,j.attempt_count,j.max_attempts "
            "FROM reconciliation_jobs j JOIN operations o ON o.id=j.operation_id "
            "WHERE o.workflow_id=%s ORDER BY j.id",
            (workflow_id,),
        ).fetchall()
        counts = {}
        for table in ("claims", "claim_permits", "audio_segments"):
            # Table names are a fixed internal tuple, never network input.
            row = conn.execute(
                f"SELECT count(*) AS total FROM {table} WHERE workflow_id=%s", (workflow_id,)
            ).fetchone()
            assert row is not None
            counts[table] = row["total"]
    return cast(
        dict[str, Any],
        json.loads(
            json.dumps(
                {"workflow": workflow, "handoffs": handoffs, "jobs": jobs, "counts": counts},
                default=str,
            )
        ),
    )
