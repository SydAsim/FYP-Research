"""Durable named barriers and independent scripted client playback evidence."""

from alembic import op

revision: str = "0008_phase6_research"
down_revision: str | None = "0007_phase5_drafts"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE executions ADD COLUMN simulator_scenario_id uuid")
    op.execute("ALTER TABLE executions ADD COLUMN fault_schedule_hash text")
    op.execute("ALTER TABLE executions ADD COLUMN correction_scripted_at timestamptz")
    op.execute(
        "CREATE TABLE research_barrier_events ("
        "id uuid PRIMARY KEY,"
        "execution_id uuid NOT NULL REFERENCES executions(id),"
        "barrier_name text NOT NULL CHECK (barrier_name ~ '^P[0-9]$'),"
        "ordinal integer NOT NULL CHECK (ordinal >= 1),"
        "state text NOT NULL CHECK (state IN ('REACHED','RELEASED')) ,"
        "source_event_id text NOT NULL,"
        "reached_at timestamptz NOT NULL,"
        "released_at timestamptz NULL,"
        "UNIQUE (execution_id,barrier_name,ordinal),"
        "UNIQUE (execution_id,source_event_id))"
    )
    op.execute(
        "CREATE TABLE research_playback_acks ("
        "event_id uuid PRIMARY KEY,"
        "execution_id uuid NOT NULL REFERENCES executions(id),"
        "claim_type text NOT NULL,"
        "claim_start timestamptz NULL,"
        "intent_revision integer NOT NULL CHECK (intent_revision >= 1),"
        "released_at timestamptz NOT NULL,"
        "played_at timestamptz NOT NULL,"
        "played_ms integer NOT NULL CHECK (played_ms >= 0),"
        "permit_id uuid NULL REFERENCES claim_permits(id),"
        "audio_hash text NOT NULL CHECK (audio_hash ~ '^[0-9a-f]{64}$'),"
        "created_at timestamptz NOT NULL DEFAULT now())"
    )
    op.execute(
        "CREATE INDEX research_playback_execution_idx "
        "ON research_playback_acks (execution_id,played_at)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE research_playback_acks")
    op.execute("DROP TABLE research_barrier_events")
    op.execute("ALTER TABLE executions DROP COLUMN correction_scripted_at")
    op.execute("ALTER TABLE executions DROP COLUMN fault_schedule_hash")
    op.execute("ALTER TABLE executions DROP COLUMN simulator_scenario_id")
