"""add negocio_integrations (Hito 5 Sprint 10a)

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-09-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b6c7d8e9f0a1'
down_revision: Union[str, None] = 'a5b6c7d8e9f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('negocio_integrations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('case_id', sa.Integer(), nullable=False),
    sa.Column('adan_email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('adan_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('adan_user_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('adan_company_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('access_token', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('token_created_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['case_id'], ['migration_cases.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('case_id')
    )
    op.create_index(op.f('ix_negocio_integrations_case_id'), 'negocio_integrations', ['case_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_negocio_integrations_case_id'), table_name='negocio_integrations')
    op.drop_table('negocio_integrations')
