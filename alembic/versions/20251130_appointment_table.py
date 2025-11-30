"""add appointments table

Revision ID: 20251130_appointment
Revises: 
Create Date: 2025-11-30 00:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251130_appointment"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_appointments_tenant_patient_scheduled",
        "appointments",
        ["tenant_id", "patient_id", "scheduled_at"],
    )
    op.create_index("ix_appointments_id", "appointments", ["id"])  # parity
    op.create_index("ix_appointments_tenant_id", "appointments", ["tenant_id"])  # parity


def downgrade() -> None:
    op.drop_index("ix_appointments_tenant_patient_scheduled", table_name="appointments")
    op.drop_index("ix_appointments_id", table_name="appointments")
    op.drop_index("ix_appointments_tenant_id", table_name="appointments")
    op.drop_table("appointments")
