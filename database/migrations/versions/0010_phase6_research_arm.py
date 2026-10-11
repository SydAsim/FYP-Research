"""Pin an explicit repair ablation arm on synthetic experiment workflows."""

from alembic import op

revision: str = "0010_phase6_research_arm"
down_revision: str | None = "0009_phase6_baselines"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE workflows ADD COLUMN research_arm text NULL "
        "CHECK (research_arm IN ('B3','P1','P2'))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE workflows DROP COLUMN research_arm")
