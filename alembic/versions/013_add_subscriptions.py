"""Add subscriptions table

Revision ID: 013_add_subscriptions
Revises: 012_add_medical_record_shares
Create Date: 2025-11-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '013_add_subscriptions'
down_revision = '012_add_medical_record_shares'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create subscriptions table using VARCHAR for enum fields."""
    # Create subscriptions table with VARCHAR instead of ENUM for compatibility
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='requested'),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('criteria', sa.String(length=255), nullable=False),
        sa.Column('channel_type', sa.String(length=30), nullable=False, server_default='rest-hook'),
        sa.Column('endpoint', sa.String(length=512), nullable=False),
        sa.Column('payload', sa.String(length=128), nullable=True, server_default='application/fhir+json'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_subscriptions_tenant_id'), 'subscriptions', ['tenant_id'], unique=False)


def downgrade() -> None:
    """Drop subscriptions table."""
    op.drop_index(op.f('ix_subscriptions_tenant_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
