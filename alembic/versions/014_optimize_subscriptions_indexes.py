"""Optimize subscriptions indexing

Revision ID: 014_optimize_subs_indexes
Revises: 013_add_subscriptions
Create Date: 2025-11-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '014_optimize_subs_indexes'
down_revision = '013_add_subscriptions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add helpful indexes for common subscription lookups."""
    # Composite index to speed up tenant-scoped active lookups
    op.create_index(
        'ix_subscriptions_tenant_status',
        'subscriptions',
        ['tenant_id', 'status'],
        unique=False,
    )

    # Prefix searches on criteria (e.g., 'Patient%', 'Appointment%') benefit from text_pattern_ops
    # Note: This uses PostgreSQL operator class; safe no-op on other engines not used in prod
    op.execute(
        'CREATE INDEX IF NOT EXISTS ix_subscriptions_criteria_prefix ON subscriptions (criteria text_pattern_ops)'
    )


def downgrade() -> None:
    """Drop added indexes."""
    op.drop_index('ix_subscriptions_tenant_status', table_name='subscriptions')
    op.execute('DROP INDEX IF EXISTS ix_subscriptions_criteria_prefix')
