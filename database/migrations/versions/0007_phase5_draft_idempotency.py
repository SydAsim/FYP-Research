"""Bind research draft creation to a durable command ID."""

from alembic import op

revision: str = "0007_phase5_drafts"
down_revision: str | None = "0006_phase5_ui_data"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE evaluation_runs ADD COLUMN creation_command_id uuid UNIQUE")


def downgrade() -> None:
    op.execute("ALTER TABLE evaluation_runs DROP COLUMN creation_command_id")
