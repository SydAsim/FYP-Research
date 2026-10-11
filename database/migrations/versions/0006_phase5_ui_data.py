"""Synthetic demo identity and scoped maintenance notes for the Phase 5 UI."""

# ruff: noqa: E501 -- Migration SQL remains explicit for review.

from alembic import op

revision: str = "0006_phase5_ui_data"
down_revision: str | None = "0005_phase4_playback"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        "CREATE TABLE resident_notes ("
        "id uuid PRIMARY KEY DEFAULT gen_random_uuid(),"
        "resident_id uuid NOT NULL REFERENCES residents(id),"
        "category text NOT NULL CHECK (category IN "
        "('SCHEDULING_PREFERENCE','ACCESS_INSTRUCTION','MAINTENANCE_CONTEXT',"
        "'COMMUNICATION_PREFERENCE','FOLLOW_UP')) ,"
        "note_text text NOT NULL CHECK (length(trim(note_text)) BETWEEN 1 AND 2000),"
        "source text NOT NULL CHECK (source IN ('HUMAN','CALL_EXTRACTED','SYSTEM')) ,"
        "source_call_id uuid NULL REFERENCES call_sessions(id),"
        "source_utterance_id uuid NULL REFERENCES utterances(id),"
        "validated boolean NOT NULL DEFAULT false,"
        "version integer NOT NULL DEFAULT 0 CHECK (version >= 0),"
        "created_at timestamptz NOT NULL DEFAULT now(),"
        "superseded_at timestamptz NULL,"
        "CHECK (source <> 'CALL_EXTRACTED' OR source_call_id IS NOT NULL))"
    )
    op.execute(
        "CREATE INDEX resident_notes_active_idx ON resident_notes(resident_id,created_at) WHERE superseded_at IS NULL"
    )
    op.execute(
        "INSERT INTO actors (id,subject,display_name) VALUES "
        "('11111111-1111-4111-8111-111111111111','demo:maintenance','Demo Resident') "
        "ON CONFLICT DO NOTHING"
    )
    op.execute(
        "INSERT INTO properties (id,external_ref,display_name,timezone) VALUES "
        "('22222222-2222-4222-8222-222222222222','demo:property','Indigo Demo Property','Asia/Karachi') "
        "ON CONFLICT DO NOTHING"
    )
    op.execute(
        "INSERT INTO residents (id,actor_id,property_id,unit_ref,contact_json,scheduling_preference_json) VALUES "
        "('33333333-3333-4333-8333-333333333333',"
        "'11111111-1111-4111-8111-111111111111',"
        "'22222222-2222-4222-8222-222222222222','A-1',"
        "jsonb_build_object('synthetic',true,'communication_preference','voice'),"
        "jsonb_build_object('preferred_window','afternoon')) ON CONFLICT DO NOTHING"
    )
    op.execute(
        "INSERT INTO maintenance_tickets "
        "(id,resident_id,property_id,issue_type,description,status) VALUES "
        "('44444444-4444-4444-8444-444444444444',"
        "'33333333-3333-4333-8333-333333333333',"
        "'22222222-2222-4222-8222-222222222222',"
        "'GENERAL','Synthetic maintenance scheduling demo','OPEN') ON CONFLICT DO NOTHING"
    )


def downgrade() -> None:
    op.execute("DROP TABLE resident_notes")
    op.execute("DELETE FROM maintenance_tickets WHERE id='44444444-4444-4444-8444-444444444444'")
    op.execute("DELETE FROM residents WHERE id='33333333-3333-4333-8333-333333333333'")
    op.execute("DELETE FROM properties WHERE id='22222222-2222-4222-8222-222222222222'")
    op.execute("DELETE FROM actors WHERE id='11111111-1111-4111-8111-111111111111'")
