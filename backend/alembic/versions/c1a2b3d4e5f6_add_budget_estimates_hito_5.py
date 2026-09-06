"""add budget_estimates (Hito 5 Sprint 1)

Revision ID: c1a2b3d4e5f6
Revises: 228566482b6c
Create Date: 2026-09-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'c1a2b3d4e5f6'
down_revision: Union[str, None] = '228566482b6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('budget_estimates',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('case_id', sa.Integer(), nullable=False),
    sa.Column('family_size', sa.Integer(), nullable=False),
    sa.Column('migpal_service_fee', sa.Float(), nullable=False),
    sa.Column('government_fee', sa.Float(), nullable=False),
    sa.Column('relocation_cost_low', sa.Float(), nullable=False),
    sa.Column('relocation_cost_high', sa.Float(), nullable=False),
    sa.Column('settlement_cost', sa.Float(), nullable=False),
    sa.Column('legal_fee_low', sa.Float(), nullable=False),
    sa.Column('legal_fee_high', sa.Float(), nullable=False),
    sa.Column('origin_monthly_income', sa.Float(), nullable=False),
    sa.Column('destination_monthly_income', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['case_id'], ['migration_cases.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_budget_estimates_case_id'), 'budget_estimates', ['case_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_budget_estimates_case_id'), table_name='budget_estimates')
    op.drop_table('budget_estimates')
