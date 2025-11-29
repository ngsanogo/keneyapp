"""Add French healthcare integration: INS, CPS, DMP, MSSante

Revision ID: 017_french_healthcare
Revises: 016_enhance_lab_models
Create Date: 2025-11-29 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '017_french_healthcare'
down_revision: Union[str, None] = '016_enhance_lab_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums (check existence first)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE insstatus AS ENUM ('pending', 'verified', 'failed', 'expired');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE cpstype AS ENUM ('cps', 'e_cps', 'cpf');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # ### PatientINS table ###
    op.create_table(
        'patient_ins',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('ins_number', sa.String(length=15), nullable=False),
        sa.Column('nir_key', sa.String(length=2), nullable=True),
        sa.Column('oid', sa.String(length=50), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'verified', 'failed', 'expired', name='insstatus', create_type=False), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_method', sa.String(length=50), nullable=True),
        sa.Column('verification_operator_id', sa.Integer(), nullable=True),
        sa.Column('birth_name', sa.String(length=100), nullable=True),
        sa.Column('first_names', sa.String(length=200), nullable=True),
        sa.Column('birth_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('birth_location', sa.String(length=200), nullable=True),
        sa.Column('birth_location_code', sa.String(length=10), nullable=True),
        sa.Column('gender_code', sa.String(length=1), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_check_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['verification_operator_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ins_number'),
        sa.UniqueConstraint('patient_id')
    )
    op.create_index(op.f('ix_patient_ins_ins_number'), 'patient_ins', ['ins_number'], unique=False)
    op.create_index(op.f('ix_patient_ins_patient_id'), 'patient_ins', ['patient_id'], unique=False)
    op.create_index(op.f('ix_patient_ins_tenant_id'), 'patient_ins', ['tenant_id'], unique=False)
    
    # ### HealthcareProfessionalCPS table ###
    op.create_table(
        'healthcare_professional_cps',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('cps_type', postgresql.ENUM('cps', 'e_cps', 'cpf', name='cpstype', create_type=False), nullable=False),
        sa.Column('cps_number', sa.String(length=20), nullable=False),
        sa.Column('rpps_number', sa.String(length=11), nullable=True),
        sa.Column('adeli_number', sa.String(length=9), nullable=True),
        sa.Column('profession_code', sa.String(length=10), nullable=True),
        sa.Column('profession_category', sa.String(length=50), nullable=True),
        sa.Column('specialty_code', sa.String(length=10), nullable=True),
        sa.Column('specialty_label', sa.String(length=200), nullable=True),
        sa.Column('practice_structure_id', sa.String(length=50), nullable=True),
        sa.Column('practice_structure_name', sa.String(length=200), nullable=True),
        sa.Column('psc_sub', sa.String(length=100), nullable=True),
        sa.Column('psc_token_endpoint', sa.String(length=500), nullable=True),
        sa.Column('psc_last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('issue_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cps_number'),
        sa.UniqueConstraint('psc_sub'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_healthcare_professional_cps_adeli_number'), 'healthcare_professional_cps', ['adeli_number'], unique=False)
    op.create_index(op.f('ix_healthcare_professional_cps_cps_number'), 'healthcare_professional_cps', ['cps_number'], unique=False)
    op.create_index(op.f('ix_healthcare_professional_cps_rpps_number'), 'healthcare_professional_cps', ['rpps_number'], unique=False)
    op.create_index(op.f('ix_healthcare_professional_cps_tenant_id'), 'healthcare_professional_cps', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_professional_cps_user_id'), 'healthcare_professional_cps', ['user_id'], unique=False)
    
    # ### DMPIntegration table ###
    op.create_table(
        'dmp_integration',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('dmp_id', sa.String(length=50), nullable=True),
        sa.Column('dmp_consent', sa.Boolean(), nullable=False),
        sa.Column('dmp_consent_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dmp_access_mode', sa.String(length=20), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('documents_sent_count', sa.Integer(), nullable=False),
        sa.Column('documents_received_count', sa.Integer(), nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dmp_id')
    )
    op.create_index(op.f('ix_dmp_integration_dmp_id'), 'dmp_integration', ['dmp_id'], unique=False)
    op.create_index(op.f('ix_dmp_integration_patient_id'), 'dmp_integration', ['patient_id'], unique=False)
    op.create_index(op.f('ix_dmp_integration_tenant_id'), 'dmp_integration', ['tenant_id'], unique=False)
    
    # ### MSSanteMessage table ###
    op.create_table(
        'mssante_messages',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('internal_message_id', sa.Integer(), nullable=True),
        sa.Column('mssante_message_id', sa.String(length=100), nullable=True),
        sa.Column('sender_mssante_address', sa.String(length=200), nullable=False),
        sa.Column('receiver_mssante_address', sa.String(length=200), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('has_attachments', sa.Boolean(), nullable=False),
        sa.Column('attachment_count', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['internal_message_id'], ['messages.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('mssante_message_id')
    )
    op.create_index(op.f('ix_mssante_messages_internal_message_id'), 'mssante_messages', ['internal_message_id'], unique=False)
    op.create_index(op.f('ix_mssante_messages_mssante_message_id'), 'mssante_messages', ['mssante_message_id'], unique=False)
    op.create_index(op.f('ix_mssante_messages_tenant_id'), 'mssante_messages', ['tenant_id'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_mssante_messages_tenant_id'), table_name='mssante_messages')
    op.drop_index(op.f('ix_mssante_messages_mssante_message_id'), table_name='mssante_messages')
    op.drop_index(op.f('ix_mssante_messages_internal_message_id'), table_name='mssante_messages')
    op.drop_table('mssante_messages')
    
    op.drop_index(op.f('ix_dmp_integration_tenant_id'), table_name='dmp_integration')
    op.drop_index(op.f('ix_dmp_integration_patient_id'), table_name='dmp_integration')
    op.drop_index(op.f('ix_dmp_integration_dmp_id'), table_name='dmp_integration')
    op.drop_table('dmp_integration')
    
    op.drop_index(op.f('ix_healthcare_professional_cps_user_id'), table_name='healthcare_professional_cps')
    op.drop_index(op.f('ix_healthcare_professional_cps_tenant_id'), table_name='healthcare_professional_cps')
    op.drop_index(op.f('ix_healthcare_professional_cps_rpps_number'), table_name='healthcare_professional_cps')
    op.drop_index(op.f('ix_healthcare_professional_cps_cps_number'), table_name='healthcare_professional_cps')
    op.drop_index(op.f('ix_healthcare_professional_cps_adeli_number'), table_name='healthcare_professional_cps')
    op.drop_table('healthcare_professional_cps')
    
    op.drop_index(op.f('ix_patient_ins_tenant_id'), table_name='patient_ins')
    op.drop_index(op.f('ix_patient_ins_patient_id'), table_name='patient_ins')
    op.drop_index(op.f('ix_patient_ins_ins_number'), table_name='patient_ins')
    op.drop_table('patient_ins')
    
    # Drop enums
    op.execute('DROP TYPE cpstype')
    op.execute('DROP TYPE insstatus')
