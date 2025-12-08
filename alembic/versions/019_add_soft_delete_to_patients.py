"""Add soft delete support to patients table

Revision ID: 019_add_soft_delete
Revises: 018_add_ins_to_patients
Create Date: 2025-12-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '019_add_soft_delete'
down_revision: Union[str, None] = '018_add_ins_to_patients'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_deleted column to patients table for soft delete support."""
    op.add_column('patients', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index(op.f('ix_patients_is_deleted'), 'patients', ['is_deleted'], unique=False)


def downgrade() -> None:
    """Remove is_deleted column from patients table."""
    op.drop_index(op.f('ix_patients_is_deleted'), table_name='patients')
    op.drop_column('patients', 'is_deleted')
