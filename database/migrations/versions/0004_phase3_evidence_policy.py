"""Tighten receipt and permit storage for evidence-gated text publication."""

from alembic import op

revision: str = "0004_phase3_evidence"
down_revision: str | None = "0003_phase2_recovery"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE verification_receipts ADD CONSTRAINT receipt_valid_window "
        "CHECK (valid_until IS NULL OR valid_until > valid_from)"
    )
    op.execute(
        "ALTER TABLE verification_receipts ADD CONSTRAINT receipt_operation_scope "
        "FOREIGN KEY (workflow_id,operation_id) REFERENCES operations(workflow_id,id)"
    )
    op.execute(
        "ALTER TABLE claim_permits ADD CONSTRAINT permit_valid_window "
        "CHECK (expires_at > authorized_at)"
    )
    op.execute(
        "CREATE UNIQUE INDEX claim_permits_one_active_claim_idx ON claim_permits (claim_id) "
        "WHERE state IN ('AUTHORIZED','QUEUED','PUBLISHED')"
    )
    op.execute(
        "ALTER TABLE audio_segments ADD CONSTRAINT outcome_segment_needs_permit "
        "CHECK (segment_class NOT IN ('OUTCOME','REPAIR') OR claim_permit_id IS NOT NULL)"
    )
    op.execute(
        "CREATE INDEX verification_receipts_applicability_idx ON verification_receipts "
        "(workflow_id,intent_revision,claim_type,valid_until)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX verification_receipts_applicability_idx")
    op.execute("ALTER TABLE audio_segments DROP CONSTRAINT outcome_segment_needs_permit")
    op.execute("DROP INDEX claim_permits_one_active_claim_idx")
    op.execute("ALTER TABLE claim_permits DROP CONSTRAINT permit_valid_window")
    op.execute("ALTER TABLE verification_receipts DROP CONSTRAINT receipt_operation_scope")
    op.execute("ALTER TABLE verification_receipts DROP CONSTRAINT receipt_valid_window")
