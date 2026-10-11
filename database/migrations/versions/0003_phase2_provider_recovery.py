"""Add durable raw provider events and active-job deduplication."""

from alembic import op

revision: str = "0003_phase2_recovery"
down_revision: str | None = "0002_phase1_commands"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE provider_events (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          operation_id uuid NOT NULL REFERENCES operations(id),
          attempt_id uuid NULL REFERENCES operation_attempts(id),
          event_kind text NOT NULL,
          raw_json jsonb NOT NULL,
          normalized_json jsonb NOT NULL,
          content_hash text NOT NULL,
          trace_id text NOT NULL,
          occurred_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX provider_events_operation_idx ON provider_events (operation_id, occurred_at)"
    )
    op.execute(
        "CREATE UNIQUE INDEX reconciliation_jobs_one_active_idx "
        "ON reconciliation_jobs (operation_id, job_type) WHERE state IN ('READY','LEASED')"
    )


def downgrade() -> None:
    op.execute("DROP INDEX reconciliation_jobs_one_active_idx")
    op.execute("DROP TABLE provider_events")
