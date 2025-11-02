"""Add medical_documents table

Revision ID: 011_add_medical_documents
Revises: 010_add_messages
Create Date: 2025-11-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011_add_medical_documents'
down_revision = '010_add_messages'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create medical_documents table for document storage."""
    # Create enums
    document_type = postgresql.ENUM(
        'lab_result', 'imaging', 'prescription', 'consultation_note', 
        'vaccination_record', 'insurance', 'id_document', 'other',
        name='documenttype', create_type=True
    )
    document_type.create(op.get_bind(), checkfirst=True)
    
    document_format = postgresql.ENUM(
        'pdf', 'jpeg', 'png', 'dicom', 'docx', 'txt',
        name='documentformat', create_type=True
    )
    document_format.create(op.get_bind(), checkfirst=True)
    
    document_status = postgresql.ENUM(
        'uploading', 'processing', 'ready', 'failed', 'archived',
        name='documentstatus', create_type=True
    )
    document_status.create(op.get_bind(), checkfirst=True)
    
    # Create medical_documents table
    op.create_table(
        'medical_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('document_type', sa.Enum(
            'lab_result', 'imaging', 'prescription', 'consultation_note',
            'vaccination_record', 'insurance', 'id_document', 'other',
            name='documenttype'
        ), nullable=False),
        sa.Column('document_format', sa.Enum(
            'pdf', 'jpeg', 'png', 'dicom', 'docx', 'txt',
            name='documentformat'
        ), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('storage_path', sa.String(length=1000), nullable=False),
        sa.Column('storage_type', sa.String(length=50), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('status', sa.Enum(
            'uploading', 'processing', 'ready', 'failed', 'archived',
            name='documentstatus'
        ), nullable=False),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('ocr_text', sa.Text(), nullable=True),
        sa.Column('extracted_metadata', sa.Text(), nullable=True),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=True),
        sa.Column('prescription_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('is_sensitive', sa.Boolean(), nullable=True),
        sa.Column('encryption_key_id', sa.String(length=255), nullable=True),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['prescription_id'], ['prescriptions.id'], ondelete='SET NULL'),
    )
    
    # Create indexes
    op.create_index(op.f('ix_medical_documents_id'), 'medical_documents', ['id'], unique=False)
    op.create_index(op.f('ix_medical_documents_patient_id'), 'medical_documents', ['patient_id'], unique=False)
    op.create_index(op.f('ix_medical_documents_tenant_id'), 'medical_documents', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medical_documents_created_at'), 'medical_documents', ['created_at'], unique=False)
    op.create_index(op.f('ix_medical_documents_checksum'), 'medical_documents', ['checksum'], unique=False)
    
    # Composite indexes for common queries
    op.create_index('ix_medical_documents_patient_type', 'medical_documents', 
                   ['patient_id', 'document_type', 'tenant_id'], unique=False)
    op.create_index('ix_medical_documents_patient_deleted', 'medical_documents',
                   ['patient_id', 'deleted_at'], unique=False)


def downgrade() -> None:
    """Drop medical_documents table."""
    # Drop indexes
    op.drop_index('ix_medical_documents_patient_deleted', table_name='medical_documents')
    op.drop_index('ix_medical_documents_patient_type', table_name='medical_documents')
    op.drop_index(op.f('ix_medical_documents_checksum'), table_name='medical_documents')
    op.drop_index(op.f('ix_medical_documents_created_at'), table_name='medical_documents')
    op.drop_index(op.f('ix_medical_documents_tenant_id'), table_name='medical_documents')
    op.drop_index(op.f('ix_medical_documents_patient_id'), table_name='medical_documents')
    op.drop_index(op.f('ix_medical_documents_id'), table_name='medical_documents')
    
    # Drop table
    op.drop_table('medical_documents')
    
    # Drop enums
    document_status = postgresql.ENUM('uploading', 'processing', 'ready', 'failed', 'archived', name='documentstatus')
    document_status.drop(op.get_bind(), checkfirst=True)
    
    document_format = postgresql.ENUM('pdf', 'jpeg', 'png', 'dicom', 'docx', 'txt', name='documentformat')
    document_format.drop(op.get_bind(), checkfirst=True)
    
    document_type = postgresql.ENUM(
        'lab_result', 'imaging', 'prescription', 'consultation_note',
        'vaccination_record', 'insurance', 'id_document', 'other',
        name='documenttype'
    )
    document_type.drop(op.get_bind(), checkfirst=True)
