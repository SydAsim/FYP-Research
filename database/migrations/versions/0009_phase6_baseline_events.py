"""Persist raw and normalized provider observations for research baselines."""

from alembic import op

revision: str = "0009_phase6_baselines"
down_revision: str | None = "0008_phase6_research"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        "CREATE TABLE research_baseline_events ("
        "id uuid PRIMARY KEY,"
        "execution_id uuid NOT NULL REFERENCES executions(id),"
        "ordinal integer NOT NULL CHECK (ordinal >= 1),"
        "event_kind text NOT NULL,"
        "raw_json jsonb NOT NULL,"
        "normalized_json jsonb NOT NULL,"
        "content_hash text NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),"
        "trace_id text NOT NULL,"
        "occurred_at timestamptz NOT NULL,"
        "UNIQUE (execution_id,ordinal))"
    )


def downgrade() -> None:
    op.execute("DROP TABLE research_baseline_events")
