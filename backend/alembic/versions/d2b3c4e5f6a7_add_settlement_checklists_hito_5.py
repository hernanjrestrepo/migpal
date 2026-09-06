"""add settlement_checklists and settlement_items (Hito 5 Sprint 2)

Revision ID: d2b3c4e5f6a7
Revises: c1a2b3d4e5f6
Create Date: 2026-09-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'd2b3c4e5f6a7'
down_revision: Union[str, None] = 'c1a2b3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('settlement_checklists',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('case_id', sa.Integer(), nullable=False),
    sa.Column('country', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['case_id'], ['migration_cases.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('case_id')
    )
    op.create_index(op.f('ix_settlement_checklists_case_id'), 'settlement_checklists', ['case_id'], unique=True)
    op.create_table('settlement_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('checklist_id', sa.Integer(), nullable=False),
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column(
        'status',
        sa.Enum('PENDING', 'IN_PROGRESS', 'DONE', 'NOT_APPLICABLE', name='settlementitemstatus'),
        nullable=False,
    ),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['checklist_id'], ['settlement_checklists.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_settlement_items_checklist_id'), 'settlement_items', ['checklist_id'], unique=False)
    op.create_index(op.f('ix_settlement_items_status'), 'settlement_items', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_settlement_items_status'), table_name='settlement_items')
    op.drop_index(op.f('ix_settlement_items_checklist_id'), table_name='settlement_items')
    op.drop_table('settlement_items')
    op.drop_index(op.f('ix_settlement_checklists_case_id'), table_name='settlement_checklists')
    op.drop_table('settlement_checklists')
