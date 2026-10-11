"""Persist voice events, audio state, acknowledged exposure, and repair identity."""

from alembic import op

revision: str = "0005_phase4_playback"
down_revision: str | None = "0004_phase3_evidence"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        "CREATE TABLE voice_events ("
        "id uuid PRIMARY KEY,call_id uuid NOT NULL REFERENCES call_sessions(id),"
        "source_event_id text NOT NULL,event_type text NOT NULL,"
        "raw_json jsonb NOT NULL,normalized_json jsonb NOT NULL,"
        "content_hash text NOT NULL,occurred_at timestamptz NOT NULL,"
        "trace_id text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),"
        "UNIQUE(call_id,source_event_id))"
    )
    op.execute("CREATE INDEX voice_events_call_order_idx ON voice_events(call_id,occurred_at,id)")
    op.execute(
        "ALTER TABLE audio_segments ADD COLUMN workflow_id uuid REFERENCES workflows(id),"
        "ADD COLUMN intent_revision integer CHECK (intent_revision >= 1),"
        "ADD COLUMN claim_id uuid REFERENCES claims(id),"
        "ADD COLUMN repair_obligation_id uuid REFERENCES repair_obligations(id),"
        "ADD COLUMN segment_text text,ADD COLUMN audio_data bytea,"
        "ADD COLUMN audio_hash text,ADD COLUMN duration_ms integer CHECK (duration_ms > 0),"
        "ADD COLUMN frame_count bigint CHECK (frame_count > 0),"
        "ADD COLUMN word_timeline_json jsonb,"
        "ADD COLUMN state text NOT NULL DEFAULT 'GENERATED' CHECK (state IN "
        "('GENERATED','QUEUED','PUBLISHED','STARTED','STOPPED','COMPLETED','CANCELLED')) ,"
        "ADD COLUMN started_at timestamptz,ADD COLUMN stopped_at timestamptz,"
        "ADD COLUMN completed_at timestamptz,"
        "ADD COLUMN last_played_ms integer NOT NULL DEFAULT 0 CHECK (last_played_ms >= 0),"
        "ADD COLUMN last_frame bigint NOT NULL DEFAULT 0 CHECK (last_frame >= 0),"
        "ADD COLUMN last_word_index integer NOT NULL DEFAULT 0 CHECK (last_word_index >= 0)"
    )
    op.execute(
        "CREATE UNIQUE INDEX audio_segments_one_permit_idx ON audio_segments(claim_permit_id) "
        "WHERE claim_permit_id IS NOT NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX repair_obligations_one_stale_span_idx "
        "ON repair_obligations(stale_segment_id,triggering_revision)"
    )
    op.execute("ALTER TABLE playback_events ADD COLUMN response_json jsonb")
    op.execute(
        "CREATE INDEX playback_events_segment_order_idx ON playback_events"
        "(segment_id,server_received_at,id)"
    )
    op.execute(
        "ALTER TABLE repair_obligations ADD CONSTRAINT repair_played_has_claim "
        "CHECK (state NOT IN ('REPAIR_AUTHORIZED','REPAIR_PLAYED') "
        "OR repair_claim_id IS NOT NULL)"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE repair_obligations DROP CONSTRAINT repair_played_has_claim")
    op.execute("DROP INDEX playback_events_segment_order_idx")
    op.execute("ALTER TABLE playback_events DROP COLUMN response_json")
    op.execute("DROP INDEX repair_obligations_one_stale_span_idx")
    op.execute("DROP INDEX audio_segments_one_permit_idx")
    op.execute(
        "ALTER TABLE audio_segments DROP COLUMN last_word_index,DROP COLUMN last_frame,"
        "DROP COLUMN last_played_ms,DROP COLUMN completed_at,DROP COLUMN stopped_at,"
        "DROP COLUMN started_at,DROP COLUMN state,DROP COLUMN word_timeline_json,"
        "DROP COLUMN frame_count,DROP COLUMN duration_ms,DROP COLUMN audio_hash,"
        "DROP COLUMN audio_data,DROP COLUMN segment_text,DROP COLUMN repair_obligation_id,"
        "DROP COLUMN claim_id,DROP COLUMN intent_revision,DROP COLUMN workflow_id"
    )
    op.execute("DROP TABLE voice_events")
