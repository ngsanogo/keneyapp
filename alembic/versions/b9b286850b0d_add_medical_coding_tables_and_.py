"""Add medical coding tables and terminology support

Revision ID: b9b286850b0d
Revises: 004
Create Date: 2025-10-31 20:55:07.187976

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9b286850b0d'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create medical_codes table
    op.create_table(
        'medical_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code_system', sa.Enum('icd11', 'snomed_ct', 'loinc', 'atc', 'cpt', 'ccam', 'dicom', name='codesystem', create_type=False), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('display', sa.String(length=500), nullable=False),
        sa.Column('definition', sa.Text(), nullable=True),
        sa.Column('parent_code', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medical_codes_id'), 'medical_codes', ['id'], unique=False)
    op.create_index(op.f('ix_medical_codes_code_system'), 'medical_codes', ['code_system'], unique=False)
    op.create_index(op.f('ix_medical_codes_code'), 'medical_codes', ['code'], unique=False)

    # Create conditions table
    op.create_table(
        'conditions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('clinical_status', sa.String(length=20), nullable=True, server_default='active'),
        sa.Column('verification_status', sa.String(length=20), nullable=True, server_default='confirmed'),
        sa.Column('severity', sa.String(length=20), nullable=True),
        sa.Column('icd11_code', sa.String(length=50), nullable=True),
        sa.Column('icd11_display', sa.String(length=500), nullable=True),
        sa.Column('snomed_code', sa.String(length=50), nullable=True),
        sa.Column('snomed_display', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('onset_date', sa.DateTime(), nullable=True),
        sa.Column('abatement_date', sa.DateTime(), nullable=True),
        sa.Column('recorded_by_id', sa.Integer(), nullable=True),
        sa.Column('recorded_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.ForeignKeyConstraint(['recorded_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conditions_id'), 'conditions', ['id'], unique=False)
    op.create_index(op.f('ix_conditions_tenant_id'), 'conditions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_conditions_patient_id'), 'conditions', ['patient_id'], unique=False)
    op.create_index(op.f('ix_conditions_icd11_code'), 'conditions', ['icd11_code'], unique=False)
    op.create_index(op.f('ix_conditions_snomed_code'), 'conditions', ['snomed_code'], unique=False)

    # Create observations table
    op.create_table(
        'observations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='final'),
        sa.Column('loinc_code', sa.String(length=50), nullable=False),
        sa.Column('loinc_display', sa.String(length=500), nullable=False),
        sa.Column('value_quantity', sa.String(length=50), nullable=True),
        sa.Column('value_unit', sa.String(length=50), nullable=True),
        sa.Column('value_string', sa.Text(), nullable=True),
        sa.Column('reference_range_low', sa.String(length=50), nullable=True),
        sa.Column('reference_range_high', sa.String(length=50), nullable=True),
        sa.Column('interpretation', sa.String(length=50), nullable=True),
        sa.Column('effective_datetime', sa.DateTime(), nullable=False),
        sa.Column('issued_datetime', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('performer_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.ForeignKeyConstraint(['performer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_observations_id'), 'observations', ['id'], unique=False)
    op.create_index(op.f('ix_observations_tenant_id'), 'observations', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_observations_patient_id'), 'observations', ['patient_id'], unique=False)
    op.create_index(op.f('ix_observations_loinc_code'), 'observations', ['loinc_code'], unique=False)

    # Create procedures table
    op.create_table(
        'procedures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='completed'),
        sa.Column('cpt_code', sa.String(length=50), nullable=True),
        sa.Column('cpt_display', sa.String(length=500), nullable=True),
        sa.Column('ccam_code', sa.String(length=50), nullable=True),
        sa.Column('ccam_display', sa.String(length=500), nullable=True),
        sa.Column('snomed_code', sa.String(length=50), nullable=True),
        sa.Column('snomed_display', sa.String(length=500), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('outcome', sa.String(length=500), nullable=True),
        sa.Column('performed_datetime', sa.DateTime(), nullable=False),
        sa.Column('performed_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.ForeignKeyConstraint(['performed_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_procedures_id'), 'procedures', ['id'], unique=False)
    op.create_index(op.f('ix_procedures_tenant_id'), 'procedures', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_procedures_patient_id'), 'procedures', ['patient_id'], unique=False)
    op.create_index(op.f('ix_procedures_cpt_code'), 'procedures', ['cpt_code'], unique=False)
    op.create_index(op.f('ix_procedures_ccam_code'), 'procedures', ['ccam_code'], unique=False)
    op.create_index(op.f('ix_procedures_snomed_code'), 'procedures', ['snomed_code'], unique=False)

    # Add ATC code columns to prescriptions table
    op.add_column('prescriptions', sa.Column('atc_code', sa.String(length=50), nullable=True))
    op.add_column('prescriptions', sa.Column('atc_display', sa.String(length=500), nullable=True))
    op.create_index(op.f('ix_prescriptions_atc_code'), 'prescriptions', ['atc_code'], unique=False)


def downgrade() -> None:
    # Drop ATC columns from prescriptions
    op.drop_index(op.f('ix_prescriptions_atc_code'), table_name='prescriptions')
    op.drop_column('prescriptions', 'atc_display')
    op.drop_column('prescriptions', 'atc_code')

    # Drop procedures table
    op.drop_index(op.f('ix_procedures_snomed_code'), table_name='procedures')
    op.drop_index(op.f('ix_procedures_ccam_code'), table_name='procedures')
    op.drop_index(op.f('ix_procedures_cpt_code'), table_name='procedures')
    op.drop_index(op.f('ix_procedures_patient_id'), table_name='procedures')
    op.drop_index(op.f('ix_procedures_tenant_id'), table_name='procedures')
    op.drop_index(op.f('ix_procedures_id'), table_name='procedures')
    op.drop_table('procedures')

    # Drop observations table
    op.drop_index(op.f('ix_observations_loinc_code'), table_name='observations')
    op.drop_index(op.f('ix_observations_patient_id'), table_name='observations')
    op.drop_index(op.f('ix_observations_tenant_id'), table_name='observations')
    op.drop_index(op.f('ix_observations_id'), table_name='observations')
    op.drop_table('observations')

    # Drop conditions table
    op.drop_index(op.f('ix_conditions_snomed_code'), table_name='conditions')
    op.drop_index(op.f('ix_conditions_icd11_code'), table_name='conditions')
    op.drop_index(op.f('ix_conditions_patient_id'), table_name='conditions')
    op.drop_index(op.f('ix_conditions_tenant_id'), table_name='conditions')
    op.drop_index(op.f('ix_conditions_id'), table_name='conditions')
    op.drop_table('conditions')

    # Drop medical_codes table
    op.drop_index(op.f('ix_medical_codes_code'), table_name='medical_codes')
    op.drop_index(op.f('ix_medical_codes_code_system'), table_name='medical_codes')
    op.drop_index(op.f('ix_medical_codes_id'), table_name='medical_codes')
    op.drop_table('medical_codes')

    # Drop enum type
    op.execute('DROP TYPE codesystem')
