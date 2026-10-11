"""Phase 0 baseline; business schema is explicitly Phase 1."""

revision: str = "0000_phase0"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
