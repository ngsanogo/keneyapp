"""add_performance_indexes

Revision ID: 3b36cf47c558
Revises: 018_add_ins_to_patients
Create Date: 2025-12-01 22:38:46.247131

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b36cf47c558'
down_revision = '019_add_soft_delete'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes for frequently queried columns."""
    
    # Patient indexes for search and filtering
    op.create_index('idx_patients_email', 'patients', ['email'], unique=False)
    op.create_index('idx_patients_phone', 'patients', ['phone_number'], unique=False)
    op.create_index('idx_patients_tenant_active', 'patients', ['tenant_id', 'is_deleted'], unique=False)
    op.create_index('idx_patients_last_name', 'patients', ['last_name'], unique=False)
    op.create_index('idx_patients_date_of_birth', 'patients', ['date_of_birth'], unique=False)
    
    # Appointment indexes for date and status queries
    op.create_index('idx_appointments_date', 'appointments', ['appointment_date'], unique=False)
    op.create_index('idx_appointments_status', 'appointments', ['status'], unique=False)
    op.create_index('idx_appointments_tenant_date', 'appointments', ['tenant_id', 'appointment_date'], unique=False)
    op.create_index('idx_appointments_patient_date', 'appointments', ['patient_id', 'appointment_date'], unique=False)
    op.create_index('idx_appointments_doctor', 'appointments', ['doctor_id'], unique=False)
    
    # Message indexes for inbox/sent queries
    op.create_index('idx_messages_receiver', 'messages', ['receiver_id'], unique=False)
    op.create_index('idx_messages_sender', 'messages', ['sender_id'], unique=False)
    op.create_index('idx_messages_status', 'messages', ['status'], unique=False)
    op.create_index('idx_messages_created', 'messages', ['created_at'], unique=False)
    op.create_index('idx_messages_receiver_status', 'messages', ['receiver_id', 'status'], unique=False)
    
    # Document indexes for patient and tenant queries
    op.create_index('idx_documents_patient', 'medical_documents', ['patient_id'], unique=False)
    op.create_index('idx_documents_type', 'medical_documents', ['document_type'], unique=False)
    op.create_index('idx_documents_created', 'medical_documents', ['created_at'], unique=False)
    
    # Prescription indexes
    op.create_index('idx_prescriptions_patient', 'prescriptions', ['patient_id'], unique=False)
    op.create_index('idx_prescriptions_doctor', 'prescriptions', ['prescribed_by'], unique=False)
    op.create_index('idx_prescriptions_date', 'prescriptions', ['prescription_date'], unique=False)
    
    # Lab result indexes
    op.create_index('idx_lab_results_patient', 'lab_results', ['patient_id'], unique=False)
    op.create_index('idx_lab_results_date', 'lab_results', ['test_date'], unique=False)
    
    # User indexes for auth queries
    op.create_index('idx_users_username', 'users', ['username'], unique=True)
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_tenant_role', 'users', ['tenant_id', 'role'], unique=False)


def downgrade() -> None:
    """Remove performance indexes."""
    
    # Patient indexes
    op.drop_index('idx_patients_email', table_name='patients')
    op.drop_index('idx_patients_phone', table_name='patients')
    op.drop_index('idx_patients_tenant_active', table_name='patients')
    op.drop_index('idx_patients_last_name', table_name='patients')
    op.drop_index('idx_patients_date_of_birth', table_name='patients')
    
    # Appointment indexes
    op.drop_index('idx_appointments_date', table_name='appointments')
    op.drop_index('idx_appointments_status', table_name='appointments')
    op.drop_index('idx_appointments_tenant_date', table_name='appointments')
    op.drop_index('idx_appointments_patient_date', table_name='appointments')
    op.drop_index('idx_appointments_doctor', table_name='appointments')
    
    # Message indexes
    op.drop_index('idx_messages_receiver', table_name='messages')
    op.drop_index('idx_messages_sender', table_name='messages')
    op.drop_index('idx_messages_status', table_name='messages')
    op.drop_index('idx_messages_created', table_name='messages')
    op.drop_index('idx_messages_receiver_status', table_name='messages')
    
    # Document indexes
    op.drop_index('idx_documents_patient', table_name='medical_documents')
    op.drop_index('idx_documents_type', table_name='medical_documents')
    op.drop_index('idx_documents_created', table_name='medical_documents')
    
    # Prescription indexes
    op.drop_index('idx_prescriptions_patient', table_name='prescriptions')
    op.drop_index('idx_prescriptions_doctor', table_name='prescriptions')
    op.drop_index('idx_prescriptions_date', table_name='prescriptions')
    
    # Lab result indexes
    op.drop_index('idx_lab_results_patient', table_name='lab_results')
    op.drop_index('idx_lab_results_date', table_name='lab_results')
    
    # User indexes
    op.drop_index('idx_users_username', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_users_tenant_role', table_name='users')
