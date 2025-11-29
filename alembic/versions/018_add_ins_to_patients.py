"""Add INS and SSN columns to patients table

Revision ID: 018_add_ins_to_patients
Revises: 017_french_healthcare
Create Date: 2025-11-29 14:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '018_add_ins_to_patients'
down_revision: Union[str, None] = '017_french_healthcare'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add ins_number and social_security_number columns to patients table for quick reference."""
    # Add INS number column (non-unique, for quick lookup)
    op.add_column('patients', sa.Column('ins_number', sa.String(length=15), nullable=True))
    op.create_index(op.f('ix_patients_ins_number'), 'patients', ['ins_number'], unique=False)
    
    # Add social security number (NIR) column
    op.add_column('patients', sa.Column('social_security_number', sa.String(length=15), nullable=True))
    op.create_index(op.f('ix_patients_social_security_number'), 'patients', ['social_security_number'], unique=False)


def downgrade() -> None:
    """Remove INS columns from patients table."""
    op.drop_index(op.f('ix_patients_social_security_number'), table_name='patients')
    op.drop_column('patients', 'social_security_number')
    op.drop_index(op.f('ix_patients_ins_number'), table_name='patients')
    op.drop_column('patients', 'ins_number')
