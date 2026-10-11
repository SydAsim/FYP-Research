"""Durable repair delivery leases; previous migrations stay unchanged."""

from alembic import op

revision: str = "0012_readiness_repair"
down_revision: str | None = "0011_phase6_b3_audio"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE repair_obligations "
        "ADD COLUMN delivery_lease_owner text,ADD COLUMN delivery_lease_until timestamptz,"
        "ADD COLUMN delivery_attempt_count integer NOT NULL DEFAULT 0 "
        "CHECK (delivery_attempt_count>=0),ADD COLUMN delivery_error_json jsonb"
    )
    op.execute(
        "CREATE INDEX repair_delivery_pending_idx ON repair_obligations(created_at) "
        "WHERE state IN ('OPEN','REPAIR_AUTHORIZED')"
    )


def downgrade() -> None:
    op.execute("DROP INDEX repair_delivery_pending_idx")
    op.execute(
        "ALTER TABLE repair_obligations DROP COLUMN delivery_error_json,"
        "DROP COLUMN delivery_attempt_count,DROP COLUMN delivery_lease_until,"
        "DROP COLUMN delivery_lease_owner"
    )
