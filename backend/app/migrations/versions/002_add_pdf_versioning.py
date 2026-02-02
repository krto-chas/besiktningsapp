"""
=============================================================================
MIGRATION: 002 - Add PDF Versioning Enhancements
=============================================================================
Add additional indexes and constraints for PDF versioning.

Revision ID: 002_add_pdf_versioning
Revises: 001_initial_schema
Create Date: 2026-01-29
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002_add_pdf_versioning'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Add PDF versioning enhancements."""
    
    # Add composite index for faster version queries
    op.create_index(
        'ix_pdf_versions_inspection_version',
        'pdf_versions',
        ['inspection_id', 'version_number'],
        unique=False
    )
    
    # Add index for status filtering
    op.create_index(
        'ix_pdf_versions_status',
        'pdf_versions',
        ['status'],
        unique=False
    )


def downgrade():
    """Remove PDF versioning enhancements."""
    op.drop_index('ix_pdf_versions_status', table_name='pdf_versions')
    op.drop_index('ix_pdf_versions_inspection_version', table_name='pdf_versions')
