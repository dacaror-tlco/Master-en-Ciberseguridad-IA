"""create timeline_events table

Adaptada respecto al original de feature/timeline-integration:
- FK a cases.id con ON DELETE CASCADE (así está ya confirmado en Aiven
  el 04/09/2026 — no se introduce, se refleja lo que ya existe).
- Índice compuesto (origen_modulo, origen_id), exigido por CLAUDE.md y
  ausente en el original. Ambos cambios son sobre timeline_events, que
  es propiedad exclusiva de este backend — no tocan tablas ajenas.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'timeline_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('fecha_hora', sa.DateTime(), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.Column('origen_modulo', sa.String(length=30), nullable=False),
        sa.Column('origen_id', sa.Integer(), nullable=False),
        sa.Column('orden', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_timeline_events_case_id', 'timeline_events', ['case_id'])
    op.create_index('ix_timeline_events_origen', 'timeline_events', ['origen_modulo', 'origen_id'])

def downgrade() -> None:
    op.drop_index('ix_timeline_events_origen', table_name='timeline_events')
    op.drop_index('ix_timeline_events_case_id', table_name='timeline_events')
    op.drop_table('timeline_events')
