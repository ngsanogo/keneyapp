"""add lab test types and criteria

Revision ID: 015_add_lab
Revises: 014_optimize_subscriptions_indexes
Create Date: 2025-11-04
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '015_add_lab'
down_revision = '014_optimize_subscriptions_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'lab_test_types',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, index=True),
        sa.Column('code', sa.String(length=64), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('specimen_type', sa.String(length=128), nullable=True),
        sa.Column('gender', sa.String(length=1), nullable=True),
        sa.Column('min_age_years', sa.Float(), nullable=True),
        sa.Column('max_age_years', sa.Float(), nullable=True),
        sa.Column('category', sa.String(length=64), nullable=True),
        sa.Column('report_style', sa.String(length=64), nullable=True),
        sa.Column('tags', sa.String(length=255), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.UniqueConstraint('tenant_id', 'code', name='uq_lab_test_type_tenant_code'),
    )

    op.create_table(
        'lab_test_criteria',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False, index=True),
        sa.Column('test_type_id', sa.Integer(), nullable=False, index=True),
        sa.Column('parameter', sa.String(length=128), nullable=False),
        sa.Column('unit', sa.String(length=32), nullable=True),
        sa.Column('normal_min', sa.Float(), nullable=True),
        sa.Column('normal_max', sa.Float(), nullable=True),
        sa.Column('gender', sa.String(length=1), nullable=True),
        sa.Column('min_age_years', sa.Float(), nullable=True),
        sa.Column('max_age_years', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['test_type_id'], ['lab_test_types.id']),
    )


def downgrade() -> None:
    op.drop_table('lab_test_criteria')
    op.drop_table('lab_test_types')
