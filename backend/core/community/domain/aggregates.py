"""
Community — domain (Sprint 5, Hito 5): grupos, membresías, publicaciones,
comentarios y likes.

Cinco tablas, ninguna aggregate compuesto -- a diferencia de ExecutionPlan/
Settlement (donde la entidad hija vive dentro del aggregate root cargado en
memoria), acá cada fila se opera de forma independiente vía su propio
repositorio (mismo criterio que Recommendation/ExecutionPlan bajo
MigrationCase: no hay una relación ORM `group.posts` cargada completa en
cada request, sería cargar todo el feed en memoria para publicar un post).

`author_user_id`/`user_id` referencian `user.id` (la tabla legacy de
`app.models.user.User` contra la que ya resuelve `app.auth.get_current_user`
-- mismo FK que usa `MigrationCase.user_id`, ver
core/case_engine/domain/aggregates.py)."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class CommunityGroup(SQLModel, table=True):
    __tablename__ = "community_groups"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    description: str | None = Field(default=None)
    city: str | None = Field(default=None)
    country: str | None = Field(default=None)
    created_by_user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GroupMembership(SQLModel, table=True):
    __tablename__ = "community_group_memberships"

    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="community_groups.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CommunityPost(SQLModel, table=True):
    __tablename__ = "community_posts"

    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="community_groups.id", index=True)
    author_user_id: int = Field(foreign_key="user.id")
    body: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CommunityComment(SQLModel, table=True):
    __tablename__ = "community_comments"

    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="community_posts.id", index=True)
    author_user_id: int = Field(foreign_key="user.id")
    body: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CommunityLike(SQLModel, table=True):
    __tablename__ = "community_likes"

    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="community_posts.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
