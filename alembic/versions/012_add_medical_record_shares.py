"""Add medical_record_shares table

Revision ID: 012_add_medical_record_shares
Revises: 011_add_medical_documents
Create Date: 2025-11-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '012_add_medical_record_shares'
down_revision = '011_add_medical_documents'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create medical_record_shares table for controlled sharing."""
    # Use VARCHAR instead of ENUM to avoid conflicts with SQLAlchemy metadata
    # The model uses native_enum=False for compatibility
    op.create_table(
        'medical_record_shares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('shared_by_user_id', sa.Integer(), nullable=False),
        sa.Column('share_token', sa.String(length=255), nullable=False),
        sa.Column('scope', sa.String(length=50), nullable=False),  # Changed to VARCHAR
        sa.Column('custom_resources', sa.Text(), nullable=True),
        sa.Column('recipient_email', sa.String(length=255), nullable=True),
        sa.Column('recipient_name', sa.String(length=255), nullable=True),
        sa.Column('access_pin', sa.String(length=10), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),  # Changed to VARCHAR
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('access_count', sa.Integer(), nullable=False),
        sa.Column('max_access_count', sa.Integer(), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_accessed_ip', sa.String(length=50), nullable=True),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('consent_given', sa.Boolean(), nullable=False),
        sa.Column('consent_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by_user_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shared_by_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['revoked_by_user_id'], ['users.id'], ondelete='SET NULL'),
    )

    # Create indexes
    op.create_index(op.f('ix_medical_record_shares_id'), 'medical_record_shares', ['id'], unique=False)
    op.create_index(op.f('ix_medical_record_shares_patient_id'), 'medical_record_shares', ['patient_id'], unique=False)
    op.create_index(op.f('ix_medical_record_shares_share_token'), 'medical_record_shares', ['share_token'], unique=True)
    op.create_index(op.f('ix_medical_record_shares_tenant_id'), 'medical_record_shares', ['tenant_id'], unique=False)

    # Composite indexes for common queries
    op.create_index('ix_medical_record_shares_active', 'medical_record_shares',
                   ['status', 'expires_at'], unique=False)


def downgrade() -> None:
    """Drop medical_record_shares table."""
    # Drop indexes
    op.drop_index('ix_medical_record_shares_active', table_name='medical_record_shares')
    op.drop_index(op.f('ix_medical_record_shares_tenant_id'), table_name='medical_record_shares')
    op.drop_index(op.f('ix_medical_record_shares_share_token'), table_name='medical_record_shares')
    op.drop_index(op.f('ix_medical_record_shares_patient_id'), table_name='medical_record_shares')
    op.drop_index(op.f('ix_medical_record_shares_id'), table_name='medical_record_shares')

    # Drop table (no ENUMs to drop since we use VARCHAR)
    op.drop_table('medical_record_shares')
