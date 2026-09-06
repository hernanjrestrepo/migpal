"""add geographic_selections, family_survey_responses, place_options (Hito 5 Sprint 4)

Revision ID: e3c4d5e6f7a8
Revises: d2b3c4e5f6a7
Create Date: 2026-09-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'e3c4d5e6f7a8'
down_revision: Union[str, None] = 'd2b3c4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('geographic_selections',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('case_id', sa.Integer(), nullable=False),
    sa.Column('country', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('state', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('city', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('neighborhood', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['case_id'], ['migration_cases.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('case_id')
    )
    op.create_index(op.f('ix_geographic_selections_case_id'), 'geographic_selections', ['case_id'], unique=True)

    op.create_table('family_survey_responses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('case_id', sa.Integer(), nullable=False),
    sa.Column('case_family_member_id', sa.Integer(), nullable=True),
    sa.Column('is_primary_applicant', sa.Boolean(), nullable=False),
    sa.Column('climate_preference', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('top_priority', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('completed', sa.Boolean(), nullable=False),
    sa.Column('submitted_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['case_id'], ['migration_cases.id'], ),
    sa.ForeignKeyConstraint(['case_family_member_id'], ['case_family_members.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_survey_responses_case_id'), 'family_survey_responses', ['case_id'], unique=False)

    op.create_table('place_options',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('case_id', sa.Integer(), nullable=False),
    sa.Column('option_type', sa.Enum('SCHOOL', 'HOUSING', name='placeoptiontype'), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('website', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('phone', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('requirements', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('cost_amount', sa.Float(), nullable=True),
    sa.Column('cost_period', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('image_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['case_id'], ['migration_cases.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_place_options_case_id'), 'place_options', ['case_id'], unique=False)
    op.create_index(op.f('ix_place_options_option_type'), 'place_options', ['option_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_place_options_option_type'), table_name='place_options')
    op.drop_index(op.f('ix_place_options_case_id'), table_name='place_options')
    op.drop_table('place_options')
    op.drop_index(op.f('ix_family_survey_responses_case_id'), table_name='family_survey_responses')
    op.drop_table('family_survey_responses')
    op.drop_index(op.f('ix_geographic_selections_case_id'), table_name='geographic_selections')
    op.drop_table('geographic_selections')
