"""add_appointment_reminders_table_manual

Revision ID: ad32cfbd49e1
Revises: 496bc14415db
Create Date: 2025-11-30 17:42:57.733809

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'ad32cfbd49e1'
down_revision = '496bc14415db'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create reminderchannel enum
    reminderchannel = postgresql.ENUM('email', 'sms', 'push', 'all', name='reminderchannel')
    reminderchannel.create(op.get_bind(), checkfirst=True)
    
    # Create reminderstatus enum
    reminderstatus = postgresql.ENUM('pending', 'sent', 'failed', 'cancelled', name='reminderstatus')
    reminderstatus.create(op.get_bind(), checkfirst=True)
    
    # Create appointment_reminders table
    op.create_table(
        'appointment_reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('channel', reminderchannel, nullable=False),
        sa.Column('status', reminderstatus, nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('hours_before', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_appointment_reminders_id'), 'appointment_reminders', ['id'], unique=False)
    op.create_index(op.f('ix_appointment_reminders_tenant_id'), 'appointment_reminders', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_appointment_reminders_appointment_id'), 'appointment_reminders', ['appointment_id'], unique=False)
    op.create_index(op.f('ix_appointment_reminders_scheduled_time'), 'appointment_reminders', ['scheduled_time'], unique=False)
    op.create_index('ix_appointment_reminders_status_scheduled', 'appointment_reminders', ['status', 'scheduled_time'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_appointment_reminders_status_scheduled', table_name='appointment_reminders')
    op.drop_index(op.f('ix_appointment_reminders_scheduled_time'), table_name='appointment_reminders')
    op.drop_index(op.f('ix_appointment_reminders_appointment_id'), table_name='appointment_reminders')
    op.drop_index(op.f('ix_appointment_reminders_tenant_id'), table_name='appointment_reminders')
    op.drop_index(op.f('ix_appointment_reminders_id'), table_name='appointment_reminders')
    
    # Drop table
    op.drop_table('appointment_reminders')
    
    # Drop enums
    postgresql.ENUM('pending', 'sent', 'failed', 'cancelled', name='reminderstatus').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM('email', 'sms', 'push', 'all', name='reminderchannel').drop(op.get_bind(), checkfirst=True)
