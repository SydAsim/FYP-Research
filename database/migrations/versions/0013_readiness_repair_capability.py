"""Enforce ablated repair capability at the durable database boundary."""

from alembic import op

revision: str = "0013_readiness_capability"
down_revision: str | None = "0012_readiness_repair"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        "CREATE FUNCTION check_repair_capability() RETURNS trigger LANGUAGE plpgsql AS $$ "
        "BEGIN IF NOT EXISTS (SELECT 1 FROM workflows w WHERE w.id=NEW.workflow_id "
        "AND (w.research_arm IS NULL OR w.research_arm='P2')) THEN "
        "RAISE EXCEPTION 'durable repair capability disabled for research arm'; "
        "END IF; RETURN NEW; END $$"
    )
    op.execute(
        "CREATE TRIGGER repair_capability_guard BEFORE INSERT OR UPDATE ON repair_obligations "
        "FOR EACH ROW EXECUTE FUNCTION check_repair_capability()"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER repair_capability_guard ON repair_obligations")
    op.execute("DROP FUNCTION check_repair_capability()")
