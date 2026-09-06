"""add community groups, memberships, posts, comments, likes (Hito 5 Sprint 5)

Revision ID: f4d5e6f7a8b9
Revises: e3c4d5e6f7a8
Create Date: 2026-09-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'f4d5e6f7a8b9'
down_revision: Union[str, None] = 'e3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('community_groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('city', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('country', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_by_user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.create_table('community_group_memberships',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('joined_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['community_groups.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_community_group_memberships_group_id'), 'community_group_memberships', ['group_id'], unique=False)
    op.create_index(op.f('ix_community_group_memberships_user_id'), 'community_group_memberships', ['user_id'], unique=False)

    op.create_table('community_posts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('author_user_id', sa.Integer(), nullable=False),
    sa.Column('body', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['community_groups.id'], ),
    sa.ForeignKeyConstraint(['author_user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_community_posts_group_id'), 'community_posts', ['group_id'], unique=False)

    op.create_table('community_comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('post_id', sa.Integer(), nullable=False),
    sa.Column('author_user_id', sa.Integer(), nullable=False),
    sa.Column('body', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['post_id'], ['community_posts.id'], ),
    sa.ForeignKeyConstraint(['author_user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_community_comments_post_id'), 'community_comments', ['post_id'], unique=False)

    op.create_table('community_likes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('post_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['post_id'], ['community_posts.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_community_likes_post_id'), 'community_likes', ['post_id'], unique=False)
    op.create_index(op.f('ix_community_likes_user_id'), 'community_likes', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_community_likes_user_id'), table_name='community_likes')
    op.drop_index(op.f('ix_community_likes_post_id'), table_name='community_likes')
    op.drop_table('community_likes')
    op.drop_index(op.f('ix_community_comments_post_id'), table_name='community_comments')
    op.drop_table('community_comments')
    op.drop_index(op.f('ix_community_posts_group_id'), table_name='community_posts')
    op.drop_table('community_posts')
    op.drop_index(op.f('ix_community_group_memberships_user_id'), table_name='community_group_memberships')
    op.drop_index(op.f('ix_community_group_memberships_group_id'), table_name='community_group_memberships')
    op.drop_table('community_group_memberships')
    op.drop_table('community_groups')
