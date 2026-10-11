"""Persist command identity and response for idempotent local transactions."""

from alembic import op

revision: str = "0002_phase1_commands"
down_revision: str | None = "0001_phase1_schema"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE command_receipts (
          command_id uuid PRIMARY KEY,
          command_type text NOT NULL,
          workflow_id uuid NULL REFERENCES workflows(id),
          request_hash text NOT NULL,
          response_json jsonb NOT NULL,
          created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE command_receipts")
