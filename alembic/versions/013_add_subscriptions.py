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
    """Create subscriptions table and related enum types."""
    # Create PostgreSQL ENUM types for status and channel_type
    subscription_status = postgresql.ENUM(
        'requested', 'active', 'off', 'error', name='subscriptionstatus'
    )
    subscription_status.create(op.get_bind(), checkfirst=True)

    subscription_channel = postgresql.ENUM(
        'rest-hook', name='subscriptionchanneltype'
    )
    subscription_channel.create(op.get_bind(), checkfirst=True)

    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('status', subscription_status, nullable=False, server_default='requested'),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('criteria', sa.String(length=255), nullable=False),
        sa.Column('channel_type', subscription_channel, nullable=False, server_default='rest-hook'),
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
    """Drop subscriptions table and enum types."""
    op.drop_index(op.f('ix_subscriptions_tenant_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_id'), table_name='subscriptions')
    op.drop_table('subscriptions')

    # Drop ENUM types
    subscription_channel = postgresql.ENUM('rest-hook', name='subscriptionchanneltype')
    subscription_channel.drop(op.get_bind(), checkfirst=True)

    subscription_status = postgresql.ENUM('requested', 'active', 'off', 'error', name='subscriptionstatus')
    subscription_status.drop(op.get_bind(), checkfirst=True)
