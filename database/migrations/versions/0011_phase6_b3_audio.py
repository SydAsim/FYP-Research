"""Confine permitless decisive audio to explicitly tagged B3 experiments."""

from alembic import op

revision: str = "0011_phase6_b3_audio"
down_revision: str | None = "0010_phase6_research_arm"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE audio_segments ADD COLUMN research_unpermitted boolean NOT NULL DEFAULT false"
    )
    op.execute("ALTER TABLE audio_segments DROP CONSTRAINT outcome_segment_needs_permit")
    op.execute(
        "ALTER TABLE audio_segments ADD CONSTRAINT outcome_segment_needs_permit "
        "CHECK ((segment_class NOT IN ('OUTCOME','REPAIR') OR claim_permit_id IS NOT NULL "
        "OR (segment_class='OUTCOME' AND research_unpermitted)) "
        "AND (NOT research_unpermitted OR "
        "(segment_class='OUTCOME' AND claim_permit_id IS NULL AND claim_id IS NULL "
        "AND repair_obligation_id IS NULL)))"
    )
    op.execute(
        "CREATE FUNCTION check_b3_unpermitted_audio() RETURNS trigger LANGUAGE plpgsql AS $$ "
        "BEGIN IF NEW.research_unpermitted AND NOT EXISTS "
        "(SELECT 1 FROM workflows w WHERE w.id=NEW.workflow_id AND w.call_id=NEW.call_id "
        "AND w.research_arm='B3') THEN "
        "RAISE EXCEPTION 'unpermitted outcome audio requires B3 research workflow'; "
        "END IF; RETURN NEW; END $$"
    )
    op.execute(
        "CREATE TRIGGER b3_unpermitted_audio_guard BEFORE INSERT OR UPDATE ON audio_segments "
        "FOR EACH ROW EXECUTE FUNCTION check_b3_unpermitted_audio()"
    )
    op.execute(
        "CREATE UNIQUE INDEX b3_audio_one_revision_idx "
        "ON audio_segments(workflow_id,intent_revision) "
        "WHERE research_unpermitted"
    )


def downgrade() -> None:
    op.execute("DROP INDEX b3_audio_one_revision_idx")
    op.execute("DROP TRIGGER b3_unpermitted_audio_guard ON audio_segments")
    op.execute("DROP FUNCTION check_b3_unpermitted_audio()")
    op.execute("ALTER TABLE audio_segments DROP CONSTRAINT outcome_segment_needs_permit")
    op.execute(
        "ALTER TABLE audio_segments ADD CONSTRAINT outcome_segment_needs_permit "
        "CHECK (segment_class NOT IN ('OUTCOME','REPAIR') OR claim_permit_id IS NOT NULL)"
    )
    op.execute("ALTER TABLE audio_segments DROP COLUMN research_unpermitted")
