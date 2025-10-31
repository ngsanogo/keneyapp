"""Add created/updated timestamps to core domain tables

Revision ID: 004
Revises: 003
Create Date: 2025-11-04
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add created_at/updated_at columns to key healthcare tables."""

    def _timestamp_column(name: str) -> sa.Column:
        return sa.Column(
            name,
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        )

    op.add_column("patients", _timestamp_column("created_at"))
    op.add_column("patients", _timestamp_column("updated_at"))

    op.add_column("appointments", _timestamp_column("created_at"))
    op.add_column("appointments", _timestamp_column("updated_at"))

    op.add_column("prescriptions", _timestamp_column("created_at"))
    op.add_column("prescriptions", _timestamp_column("updated_at"))


def downgrade() -> None:
    """Remove created_at/updated_at columns from domain tables."""

    op.drop_column("prescriptions", "updated_at")
    op.drop_column("prescriptions", "created_at")

    op.drop_column("appointments", "updated_at")
    op.drop_column("appointments", "created_at")

    op.drop_column("patients", "updated_at")
    op.drop_column("patients", "created_at")
