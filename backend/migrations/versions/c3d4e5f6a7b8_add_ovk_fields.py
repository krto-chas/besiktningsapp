"""add_ovk_fields

Adds OVK-specific fields to inspections and measurements tables.

inspections:
  - ovk_result      ENUM(G, C, EG, EJ)
  - next_inspection_date DATE
  - reinspection_date    DATE
  - system_number        VARCHAR(20)
  - system_type          ENUM(S, F, FT, FTX, FX, T)
  - inspection_category  INTEGER
  - energy_saving_measures VARCHAR(200)
  - notes changed from VARCHAR(2000) → TEXT

measurements:
  - direction            ENUM(T, F)
  - projected_value      FLOAT
  - measurement_method   VARCHAR(20)
  - room_name            VARCHAR(100)

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-02-27
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # ── inspections ──────────────────────────────────────────────────────────

    # Change notes from VARCHAR(2000) to TEXT
    op.alter_column(
        'inspections', 'notes',
        existing_type=sa.String(2000),
        type_=sa.Text(),
        existing_nullable=True,
    )

    # OVK result enum
    ovk_result_enum = sa.Enum('G', 'C', 'EG', 'EJ', name='ovkresult')
    ovk_result_enum.create(op.get_bind(), checkfirst=True)

    # System type enum
    system_type_enum = sa.Enum('S', 'F', 'FT', 'FTX', 'FX', 'T', name='systemtype')
    system_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('inspections', sa.Column(
        'ovk_result',
        sa.Enum('G', 'C', 'EG', 'EJ', name='ovkresult'),
        nullable=True,
        comment='OVK result: G=Godkänd, C=Kompletteringsbesiktning, EG=Egenkontroll, EJ=Ej besiktigad',
    ))
    op.add_column('inspections', sa.Column(
        'next_inspection_date',
        sa.Date(),
        nullable=True,
        comment='Nästa ordinarie besiktningsdatum',
    ))
    op.add_column('inspections', sa.Column(
        'reinspection_date',
        sa.Date(),
        nullable=True,
        comment='Ombesiktningsdatum (if result C)',
    ))
    op.add_column('inspections', sa.Column(
        'system_number',
        sa.String(20),
        nullable=True,
        comment='Ventilationssystemnummer (e.g. B1)',
    ))
    op.add_column('inspections', sa.Column(
        'system_type',
        sa.Enum('S', 'F', 'FT', 'FTX', 'FX', 'T', name='systemtype'),
        nullable=True,
        comment='Systemtyp: S/F/FT/FTX/FX/T',
    ))
    op.add_column('inspections', sa.Column(
        'inspection_category',
        sa.Integer(),
        nullable=True,
        comment='Besiktningskategori 0–4',
    ))
    op.add_column('inspections', sa.Column(
        'energy_saving_measures',
        sa.String(200),
        nullable=True,
        comment='Kommaseparerade nr för energibesparande åtgärder 0–31',
    ))

    # ── measurements ─────────────────────────────────────────────────────────

    airflow_dir_enum = sa.Enum('T', 'F', name='airflowdirection')
    airflow_dir_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('measurements', sa.Column(
        'direction',
        sa.Enum('T', 'F', name='airflowdirection'),
        nullable=True,
        comment='Airflow direction: T=Tilluft, F=Frånluft',
    ))
    op.add_column('measurements', sa.Column(
        'projected_value',
        sa.Float(),
        nullable=True,
        comment='Projekterat värde (l/s) for L-blankett comparison',
    ))
    op.add_column('measurements', sa.Column(
        'measurement_method',
        sa.String(20),
        nullable=True,
        comment='Mätmetod SS-EN 16211:2015 (B1, ID1, ET1, ST1, ...)',
    ))
    op.add_column('measurements', sa.Column(
        'room_name',
        sa.String(100),
        nullable=True,
        comment='Rum/don benämning for L-blankett',
    ))


def downgrade():
    # ── measurements ─────────────────────────────────────────────────────────
    op.drop_column('measurements', 'room_name')
    op.drop_column('measurements', 'measurement_method')
    op.drop_column('measurements', 'projected_value')
    op.drop_column('measurements', 'direction')

    sa.Enum(name='airflowdirection').drop(op.get_bind(), checkfirst=True)

    # ── inspections ──────────────────────────────────────────────────────────
    op.drop_column('inspections', 'energy_saving_measures')
    op.drop_column('inspections', 'inspection_category')
    op.drop_column('inspections', 'system_type')
    op.drop_column('inspections', 'system_number')
    op.drop_column('inspections', 'reinspection_date')
    op.drop_column('inspections', 'next_inspection_date')
    op.drop_column('inspections', 'ovk_result')

    sa.Enum(name='systemtype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='ovkresult').drop(op.get_bind(), checkfirst=True)

    op.alter_column(
        'inspections', 'notes',
        existing_type=sa.Text(),
        type_=sa.String(2000),
        existing_nullable=True,
    )
