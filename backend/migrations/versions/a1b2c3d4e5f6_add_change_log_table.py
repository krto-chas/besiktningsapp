"""Add change_log table for offline-first sync cursors

Revision ID: a1b2c3d4e5f6
Revises: 136613429a05
Create Date: 2026-02-27 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '136613429a05'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'change_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            'entity_type', sa.String(length=50), nullable=False,
            comment='Domain entity type: property, inspection, apartment, defect, measurement',
        ),
        sa.Column(
            'server_id', sa.Integer(), nullable=False,
            comment='PK of the changed entity in its own table',
        ),
        sa.Column(
            'action', sa.String(length=20), nullable=False,
            comment='Mutation action: create | update | delete',
        ),
        sa.Column(
            'revision', sa.Integer(), nullable=False,
            comment='Entity revision at time of this change',
        ),
        sa.Column(
            'payload', sa.JSON(), nullable=True,
            comment='Full entity snapshot at time of change; null for deletes',
        ),
        sa.Column(
            'changed_by_user_id', sa.Integer(), nullable=True,
            comment='User ID who performed the mutation',
        ),
        sa.Column(
            'created_at', sa.DateTime(), nullable=False,
            comment='UTC timestamp of mutation',
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('idx_change_log_entity', 'change_log', ['entity_type', 'server_id'])
    op.create_index('idx_change_log_cursor', 'change_log', ['id'])
    op.create_index('idx_change_log_created', 'change_log', ['created_at'])


def downgrade():
    op.drop_index('idx_change_log_created', table_name='change_log')
    op.drop_index('idx_change_log_cursor', table_name='change_log')
    op.drop_index('idx_change_log_entity', table_name='change_log')
    op.drop_table('change_log')
