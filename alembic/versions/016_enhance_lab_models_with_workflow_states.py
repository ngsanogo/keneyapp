"""enhance_lab_models_with_workflow_states

Revision ID: 016_enhance_lab_models
Revises: 015_add_lab
Create Date: 2025-11-05

Enhancements based on GNU Health patterns:
- Add workflow state machine to lab_results
- Add enums for lab test categories and report styles
- Add audit fields for state transitions
- Add enhanced fields to lab_test_criteria

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '016_enhance_lab_models'
down_revision = '015_add_lab'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    labresultstate = postgresql.ENUM(
        'draft', 'pending_review', 'reviewed', 'validated', 'amended', 'cancelled',
        name='labresultstate'
    )
    labresultstate.create(op.get_bind())
    
    labtestcategory = postgresql.ENUM(
        'hematology', 'fluid_excreta', 'biochemical', 'immunological',
        'microbiological', 'molecular_biology', 'chromosome_genetic', 'others',
        name='labtestcategory'
    )
    labtestcategory.create(op.get_bind())
    
    labreportstyle = postgresql.ENUM(
        'tbl_h_r_u_nr', 'tbl_h_r_nr', 'tbl_h_r', 'tbl_nh_r',
        'tbl_nh_r_img', 'no_tbl', 'do_not_show',
        name='labreportstyle'
    )
    labreportstyle.create(op.get_bind())
    
    # Enhance lab_results table
    op.add_column('lab_results', sa.Column('test_type_id', sa.Integer(), nullable=True))
    op.add_column('lab_results', sa.Column('state', labresultstate, nullable=False, server_default='draft'))
    op.add_column('lab_results', sa.Column('requested_by_id', sa.Integer(), nullable=True))
    op.add_column('lab_results', sa.Column('reviewed_by_id', sa.Integer(), nullable=True))
    op.add_column('lab_results', sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('lab_results', sa.Column('validated_by_id', sa.Integer(), nullable=True))
    op.add_column('lab_results', sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add foreign keys
    op.create_foreign_key(
        'fk_lab_results_test_type_id', 'lab_results', 'lab_test_types',
        ['test_type_id'], ['id']
    )
    op.create_foreign_key(
        'fk_lab_results_requested_by_id', 'lab_results', 'users',
        ['requested_by_id'], ['id']
    )
    op.create_foreign_key(
        'fk_lab_results_reviewed_by_id', 'lab_results', 'users',
        ['reviewed_by_id'], ['id']
    )
    op.create_foreign_key(
        'fk_lab_results_validated_by_id', 'lab_results', 'users',
        ['validated_by_id'], ['id']
    )
    
    # Add indexes for workflow queries
    op.create_index('ix_lab_results_state', 'lab_results', ['state'])
    op.create_index('ix_lab_results_test_type_id', 'lab_results', ['test_type_id'])
    
    # Enhance lab_test_types table
    op.alter_column(
        'lab_test_types', 'category',
        type_=labtestcategory,
        existing_type=sa.String(64),
        postgresql_using='category::text::labtestcategory'
    )
    op.alter_column(
        'lab_test_types', 'report_style',
        type_=labreportstyle,
        existing_type=sa.String(64),
        postgresql_using='report_style::text::labreportstyle'
    )
    op.add_column('lab_test_types', sa.Column('description', sa.Text(), nullable=True))
    op.create_index('ix_lab_test_types_category', 'lab_test_types', ['category'])
    
    # Enhance lab_test_criteria table
    op.add_column('lab_test_criteria', sa.Column('code', sa.String(64), nullable=True))
    op.add_column('lab_test_criteria', sa.Column('test_method', sa.String(128), nullable=True))
    op.add_column('lab_test_criteria', sa.Column('normal_range', sa.String(128), nullable=True))
    op.add_column('lab_test_criteria', sa.Column('warning', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('lab_test_criteria', sa.Column('limits_verified', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('lab_test_criteria', sa.Column('excluded', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('lab_test_criteria', sa.Column('to_integer', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('lab_test_criteria', sa.Column('sequence', sa.Integer(), nullable=True, server_default='0'))
    op.create_index('ix_lab_test_criteria_code', 'lab_test_criteria', ['code'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_lab_test_criteria_code', table_name='lab_test_criteria')
    op.drop_index('ix_lab_test_types_category', table_name='lab_test_types')
    op.drop_index('ix_lab_results_test_type_id', table_name='lab_results')
    op.drop_index('ix_lab_results_state', table_name='lab_results')
    
    # Drop enhanced columns from lab_test_criteria
    op.drop_column('lab_test_criteria', 'sequence')
    op.drop_column('lab_test_criteria', 'to_integer')
    op.drop_column('lab_test_criteria', 'excluded')
    op.drop_column('lab_test_criteria', 'limits_verified')
    op.drop_column('lab_test_criteria', 'warning')
    op.drop_column('lab_test_criteria', 'normal_range')
    op.drop_column('lab_test_criteria', 'test_method')
    op.drop_column('lab_test_criteria', 'code')
    
    # Revert lab_test_types columns to varchar
    op.drop_column('lab_test_types', 'description')
    op.alter_column(
        'lab_test_types', 'report_style',
        type_=sa.String(64),
        existing_type=postgresql.ENUM(name='labreportstyle'),
        postgresql_using='report_style::text'
    )
    op.alter_column(
        'lab_test_types', 'category',
        type_=sa.String(64),
        existing_type=postgresql.ENUM(name='labtestcategory'),
        postgresql_using='category::text'
    )
    
    # Drop foreign keys
    op.drop_constraint('fk_lab_results_validated_by_id', 'lab_results', type_='foreignkey')
    op.drop_constraint('fk_lab_results_reviewed_by_id', 'lab_results', type_='foreignkey')
    op.drop_constraint('fk_lab_results_requested_by_id', 'lab_results', type_='foreignkey')
    op.drop_constraint('fk_lab_results_test_type_id', 'lab_results', type_='foreignkey')
    
    # Drop enhanced columns from lab_results
    op.drop_column('lab_results', 'validated_at')
    op.drop_column('lab_results', 'validated_by_id')
    op.drop_column('lab_results', 'reviewed_at')
    op.drop_column('lab_results', 'reviewed_by_id')
    op.drop_column('lab_results', 'requested_by_id')
    op.drop_column('lab_results', 'state')
    op.drop_column('lab_results', 'test_type_id')
    
    # Drop enum types
    op.execute('DROP TYPE labreportstyle')
    op.execute('DROP TYPE labtestcategory')
    op.execute('DROP TYPE labresultstate')
