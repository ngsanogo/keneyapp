"""Add messages table for secure messaging

Revision ID: 010_add_messages
Revises: b9b286850b0d
Create Date: 2025-11-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_add_messages'
down_revision = 'b9b286850b0d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create messages table for secure patient-doctor communication."""
    # Create enum for message status
    message_status = postgresql.ENUM('sent', 'delivered', 'read', 'failed', name='messagestatus', create_type=True)
    message_status.create(op.get_bind(), checkfirst=True)

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('receiver_id', sa.Integer(), nullable=False),
        sa.Column('encrypted_content', sa.Text(), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=True),
        # Use existing ENUM type if already created (avoid duplicate creation errors)
        sa.Column(
            'status',
            postgresql.ENUM(
                'sent', 'delivered', 'read', 'failed',
                name='messagestatus',
                create_type=False
            ),
            nullable=False
        ),
        sa.Column('is_urgent', sa.Boolean(), nullable=True),
        sa.Column('attachment_ids', sa.Text(), nullable=True),
        sa.Column('thread_id', sa.String(length=255), nullable=True),
        sa.Column('reply_to_id', sa.Integer(), nullable=True),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by_sender', sa.Boolean(), nullable=True),
        sa.Column('deleted_by_receiver', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reply_to_id'], ['messages.id'], ondelete='SET NULL'),
    )

    # Create indexes
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)
    op.create_index(op.f('ix_messages_sender_id'), 'messages', ['sender_id'], unique=False)
    op.create_index(op.f('ix_messages_receiver_id'), 'messages', ['receiver_id'], unique=False)
    op.create_index(op.f('ix_messages_thread_id'), 'messages', ['thread_id'], unique=False)
    op.create_index(op.f('ix_messages_tenant_id'), 'messages', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_messages_created_at'), 'messages', ['created_at'], unique=False)

    # Composite index for common query patterns
    op.create_index('ix_messages_receiver_unread', 'messages', ['receiver_id', 'read_at', 'tenant_id'], unique=False)
    op.create_index('ix_messages_conversation', 'messages', ['sender_id', 'receiver_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Drop messages table."""
    # Drop indexes
    op.drop_index('ix_messages_conversation', table_name='messages')
    op.drop_index('ix_messages_receiver_unread', table_name='messages')
    op.drop_index(op.f('ix_messages_created_at'), table_name='messages')
    op.drop_index(op.f('ix_messages_tenant_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_thread_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_receiver_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_sender_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_id'), table_name='messages')

    # Drop table
    op.drop_table('messages')

    # Drop enum type
    message_status = postgresql.ENUM('sent', 'delivered', 'read', 'failed', name='messagestatus')
    message_status.drop(op.get_bind(), checkfirst=True)
