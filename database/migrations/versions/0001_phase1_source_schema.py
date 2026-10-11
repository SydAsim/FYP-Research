"""Install the authoritative PostgreSQL schema, pinned to its source hash.

The source SQL is intentionally executed statement by statement so Alembic owns
the transaction. A changed source file cannot silently change this migration.
"""

from hashlib import sha256
from pathlib import Path

from alembic import op

revision: str = "0001_phase1_schema"
down_revision: str | None = "0000_phase0"
branch_labels: str | None = None
depends_on: str | None = None

SOURCE_HASH = "4884f8e22e26a8f2c20b47e856da337bbaadacaf956a7a230fcbefe3126b35ed"
SOURCE = Path(__file__).resolve().parents[2] / "001_initial_schema.sql"


def upgrade() -> None:
    raw = SOURCE.read_bytes()
    if sha256(raw).hexdigest() != SOURCE_HASH:
        raise RuntimeError("Authoritative schema SQL changed after migration review")
    statements = raw.decode("utf-8-sig").strip().split(";")
    for statement in statements:
        sql = statement.strip()
        if sql and sql not in {"BEGIN", "COMMIT"}:
            op.execute(sql)


def downgrade() -> None:
    # The source SQL adds this forward reference after evaluation_runs exists.
    op.execute("ALTER TABLE call_sessions DROP CONSTRAINT call_sessions_evaluation_run_fk")
    tables = (
        "metrics",
        "oracle_results",
        "fault_occurrences",
        "executions",
        "scenario_cases",
        "evaluation_runs",
        "inbox_deliveries",
        "outbox",
        "workflow_events",
        "handoffs",
        "repair_obligations",
        "playback_events",
        "audio_segments",
        "claim_permits",
        "claims",
        "evidence_items",
        "verification_receipts",
        "reconciliation_jobs",
        "effect_ledger",
        "operation_attempts",
        "operations",
        "appointments",
        "maintenance_tickets",
        "intent_revisions",
        "utterances",
        "workflows",
        "call_sessions",
        "residents",
        "properties",
        "actors",
    )
    for table in tables:
        op.execute(f"DROP TABLE {table}")
    for enum in (
        "appointment_status",
        "verification_result",
        "speech_eligibility",
        "applicability",
        "effect_knowledge",
        "processing_phase",
        "conversation_phase",
    ):
        op.execute(f"DROP TYPE {enum}")
