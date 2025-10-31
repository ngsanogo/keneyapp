"""Add created/updated timestamps to core domain tables

Revision ID: 004
Revises: 003
Create Date: 2025-11-04
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add created_at/updated_at columns to key healthcare tables."""
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    def _timestamp_column(name: str) -> sa.Column:
        return sa.Column(
            name,
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        )

    if "patients" in existing_tables:
        op.add_column("patients", _timestamp_column("created_at"))
        op.add_column("patients", _timestamp_column("updated_at"))

    if "appointments" in existing_tables:
        op.add_column("appointments", _timestamp_column("created_at"))
        op.add_column("appointments", _timestamp_column("updated_at"))

    if "prescriptions" in existing_tables:
        op.add_column("prescriptions", _timestamp_column("created_at"))
        op.add_column("prescriptions", _timestamp_column("updated_at"))


def downgrade() -> None:
    """Remove created_at/updated_at columns from domain tables."""
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "prescriptions" in existing_tables:
        op.drop_column("prescriptions", "updated_at")
        op.drop_column("prescriptions", "created_at")

    if "appointments" in existing_tables:
        op.drop_column("appointments", "updated_at")
        op.drop_column("appointments", "created_at")

    if "patients" in existing_tables:
        op.drop_column("patients", "updated_at")
        op.drop_column("patients", "created_at")
