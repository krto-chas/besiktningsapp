"""
=============================================================================
MIGRATION: 001 - Initial Schema
=============================================================================
Create all initial tables for besiktningsapp.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-01-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create initial tables."""
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='inspector'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('certification_org', sa.String(100), nullable=True),
        sa.Column('certification_number', sa.String(100), nullable=True),
        sa.Column('certification_valid_until', sa.String(50), nullable=True),
        sa.Column('competence', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('signature_image_id', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('client_id')
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_client_id', 'users', ['client_id'])
    
    # Properties table
    op.create_table(
        'properties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('property_type', sa.String(100), nullable=False),
        sa.Column('designation', sa.String(255), nullable=False),
        sa.Column('owner', sa.String(255), nullable=True),
        sa.Column('address', sa.String(500), nullable=False),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('num_apartments', sa.Integer(), nullable=True),
        sa.Column('num_premises', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id')
    )
    op.create_index('ix_properties_designation', 'properties', ['designation'])
    op.create_index('ix_properties_client_id', 'properties', ['client_id'])
    
    # Inspections table
    op.create_table(
        'inspections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('inspector_id', sa.Integer(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('active_time_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('notes', sa.String(2000), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inspector_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id')
    )
    op.create_index('ix_inspections_property_id', 'inspections', ['property_id'])
    op.create_index('ix_inspections_inspector_id', 'inspections', ['inspector_id'])
    op.create_index('ix_inspections_date', 'inspections', ['date'])
    op.create_index('ix_inspections_client_id', 'inspections', ['client_id'])
    
    # Apartments table
    op.create_table(
        'apartments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('inspection_id', sa.Integer(), nullable=False),
        sa.Column('apartment_number', sa.String(20), nullable=False),
        sa.Column('rooms', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('notes', sa.String(1000), nullable=True),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id')
    )
    op.create_index('ix_apartments_inspection_id', 'apartments', ['inspection_id'])
    op.create_index('ix_apartments_client_id', 'apartments', ['client_id'])
    
    # Defects table
    op.create_table(
        'defects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('apartment_id', sa.Integer(), nullable=False),
        sa.Column('room_index', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(30), nullable=True),
        sa.Column('title', sa.String(120), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('remedy', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False, server_default='medium'),
        sa.ForeignKeyConstraint(['apartment_id'], ['apartments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id')
    )
    op.create_index('ix_defects_apartment_id', 'defects', ['apartment_id'])
    op.create_index('ix_defects_client_id', 'defects', ['client_id'])
    
    # Images table
    op.create_table(
        'images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('defect_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('storage_key', sa.String(500), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('checksum', sa.String(64), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['defect_id'], ['defects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('storage_key'),
        sa.UniqueConstraint('client_id')
    )
    op.create_index('ix_images_defect_id', 'images', ['defect_id'])
    op.create_index('ix_images_storage_key', 'images', ['storage_key'])
    
    # Measurements table
    op.create_table(
        'measurements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('inspection_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(20), nullable=False),
        sa.Column('apartment_number', sa.String(20), nullable=True),
        sa.Column('sort_key', sa.String(60), nullable=True),
        sa.Column('notes', sa.String(300), nullable=True),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id')
    )
    op.create_index('ix_measurements_inspection_id', 'measurements', ['inspection_id'])
    op.create_index('ix_measurements_type', 'measurements', ['type'])
    
    # PDF Versions table
    op.create_table(
        'pdf_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('inspection_id', sa.Integer(), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('storage_key', sa.String(500), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('checksum', sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(['inspection_id'], ['inspections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('storage_key'),
        sa.UniqueConstraint('client_id')
    )
    op.create_index('ix_pdf_versions_inspection_id', 'pdf_versions', ['inspection_id'])
    op.create_index('ix_pdf_versions_storage_key', 'pdf_versions', ['storage_key'])
    
    # Sync Logs table
    op.create_table(
        'sync_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('idempotency_key', sa.String(255), nullable=False),
        sa.Column('device_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('operation_id', sa.String(255), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('client_id_ref', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('server_id', sa.Integer(), nullable=True),
        sa.Column('request_body', postgresql.JSON(), nullable=True),
        sa.Column('response_body', postgresql.JSON(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key')
    )
    op.create_index('ix_sync_logs_idempotency_key', 'sync_logs', ['idempotency_key'])
    op.create_index('ix_sync_logs_device_user', 'sync_logs', ['device_id', 'user_id'])
    op.create_index('ix_sync_logs_expires', 'sync_logs', ['expires_at'])
    
    # Standard Defects table
    op.create_table(
        'standard_defects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('code', sa.String(30), nullable=False),
        sa.Column('title', sa.String(120), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('remedy', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('category', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.UniqueConstraint('client_id')
    )
    op.create_index('ix_standard_defects_code', 'standard_defects', ['code'])
    op.create_index('ix_standard_defects_category', 'standard_defects', ['category'])


def downgrade():
    """Drop all tables."""
    op.drop_table('standard_defects')
    op.drop_table('sync_logs')
    op.drop_table('pdf_versions')
    op.drop_table('measurements')
    op.drop_table('images')
    op.drop_table('defects')
    op.drop_table('apartments')
    op.drop_table('inspections')
    op.drop_table('properties')
    op.drop_table('users')
