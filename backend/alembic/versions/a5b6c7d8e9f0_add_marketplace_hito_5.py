"""add marketplace_listings and marketplace_transactions (Hito 5 Sprint 6)

Revision ID: a5b6c7d8e9f0
Revises: f4d5e6f7a8b9
Create Date: 2026-09-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a5b6c7d8e9f0'
down_revision: Union[str, None] = 'f4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('marketplace_listings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('provider_user_id', sa.Integer(), nullable=False),
    sa.Column(
        'category',
        sa.Enum(
            'PLOMERIA', 'PINTURA', 'CUIDADO_INFANTIL', 'MUDANZAS', 'CLASES', 'BELLEZA', 'ELECTRICIDAD', 'OTRO',
            name='servicecategory',
        ),
        nullable=False,
    ),
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('price_amount', sa.Float(), nullable=False),
    sa.Column('price_unit', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('city', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['provider_user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_marketplace_listings_provider_user_id'), 'marketplace_listings', ['provider_user_id'], unique=False)
    op.create_index(op.f('ix_marketplace_listings_category'), 'marketplace_listings', ['category'], unique=False)
    op.create_index(op.f('ix_marketplace_listings_city'), 'marketplace_listings', ['city'], unique=False)

    op.create_table('marketplace_transactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('listing_id', sa.Integer(), nullable=False),
    sa.Column('buyer_user_id', sa.Integer(), nullable=False),
    sa.Column('seller_user_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('commission_rate', sa.Float(), nullable=False),
    sa.Column('commission_amount', sa.Float(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'CANCELLED', name='transactionstatus'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['listing_id'], ['marketplace_listings.id'], ),
    sa.ForeignKeyConstraint(['buyer_user_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['seller_user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_marketplace_transactions_listing_id'), 'marketplace_transactions', ['listing_id'], unique=False)
    op.create_index(op.f('ix_marketplace_transactions_buyer_user_id'), 'marketplace_transactions', ['buyer_user_id'], unique=False)
    op.create_index(op.f('ix_marketplace_transactions_seller_user_id'), 'marketplace_transactions', ['seller_user_id'], unique=False)
    op.create_index(op.f('ix_marketplace_transactions_status'), 'marketplace_transactions', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_marketplace_transactions_status'), table_name='marketplace_transactions')
    op.drop_index(op.f('ix_marketplace_transactions_seller_user_id'), table_name='marketplace_transactions')
    op.drop_index(op.f('ix_marketplace_transactions_buyer_user_id'), table_name='marketplace_transactions')
    op.drop_index(op.f('ix_marketplace_transactions_listing_id'), table_name='marketplace_transactions')
    op.drop_table('marketplace_transactions')
    op.drop_index(op.f('ix_marketplace_listings_city'), table_name='marketplace_listings')
    op.drop_index(op.f('ix_marketplace_listings_category'), table_name='marketplace_listings')
    op.drop_index(op.f('ix_marketplace_listings_provider_user_id'), table_name='marketplace_listings')
    op.drop_table('marketplace_listings')
