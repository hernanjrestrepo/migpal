"""
Community — adapters: superficie Web API (Sprint 5, Hito 5).

- 404: grupo o publicación inexistente.
- 409: invariante de Community (ya sos miembro, ya diste me gusta, no sos
  miembro y querés publicar/comentar/dar me gusta).

Nota de alcance: no hay moderación acá (ver docstring de
core/community/domain/rules.py) -- queda fuera de este sprint.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.auth import get_current_user
from app.db.session import get_session
from core.community.application.commands import (
    ComentarCommand,
    CrearGrupoCommand,
    DarMeGustaCommand,
    PublicarCommand,
    QuitarMeGustaCommand,
    UnirseAGrupoCommand,
)
from core.community.application.handlers import (
    handle_comentar,
    handle_crear_grupo,
    handle_dar_me_gusta,
    handle_publicar,
    handle_quitar_me_gusta,
    handle_unirse_a_grupo,
)
from core.community.application.queries import (
    build_comment_view,
    build_group_view,
    build_post_view,
    list_groups,
    list_posts_for_group,
)
from core.community.domain.rules import CommunityInvariantError
from core.community.infrastructure.repository import (
    CommentRepository,
    CommunityGroupRepository,
    LikeRepository,
    MembershipRepository,
    PostRepository,
)
from core.identity.domain.aggregates import User
from core.shared.exceptions import CommunityGroupNotFound, CommunityPostNotFound

router = APIRouter(prefix="/v1/community", tags=["community"])


class CrearGrupoRequest(BaseModel):
    name: str
    description: str | None = None
    city: str | None = None
    country: str | None = None


class GroupRead(BaseModel):
    id: int
    name: str
    description: str | None
    city: str | None
    country: str | None
    member_count: int
    is_member: bool


class PublicarRequest(BaseModel):
    body: str


class PostRead(BaseModel):
    id: int
    group_id: int
    author_user_id: int
    body: str
    created_at: str
    like_count: int
    comment_count: int
    liked_by_me: bool


class ComentarRequest(BaseModel):
    body: str


class CommentRead(BaseModel):
    id: int
    post_id: int
    author_user_id: int
    body: str
    created_at: str


@router.post("/groups", response_model=GroupRead)
def crear_grupo(
    body: CrearGrupoRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    group_repo = CommunityGroupRepository(session)
    membership_repo = MembershipRepository(session)
    group = handle_crear_grupo(
        CrearGrupoCommand(created_by_user_id=current_user.id, **body.model_dump()), group_repo, membership_repo
    )
    return build_group_view(group, group_repo=group_repo, membership_repo=membership_repo, current_user_id=current_user.id)


@router.get("/groups", response_model=list[GroupRead])
def listar_grupos(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return list_groups(CommunityGroupRepository(session), MembershipRepository(session), current_user.id)


@router.post("/groups/{group_id}/join", response_model=GroupRead)
def unirse_a_grupo(
    group_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    group_repo = CommunityGroupRepository(session)
    membership_repo = MembershipRepository(session)
    try:
        handle_unirse_a_grupo(UnirseAGrupoCommand(group_id=group_id, user_id=current_user.id), group_repo, membership_repo)
    except CommunityGroupNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CommunityInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    group = group_repo.get_by_id(group_id)
    return build_group_view(group, group_repo=group_repo, membership_repo=membership_repo, current_user_id=current_user.id)


@router.post("/groups/{group_id}/posts", response_model=PostRead)
def publicar(
    group_id: int,
    body: PublicarRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    group_repo = CommunityGroupRepository(session)
    membership_repo = MembershipRepository(session)
    post_repo = PostRepository(session)
    like_repo = LikeRepository(session)

    try:
        post = handle_publicar(
            PublicarCommand(group_id=group_id, author_user_id=current_user.id, body=body.body),
            group_repo, membership_repo, post_repo,
        )
    except CommunityGroupNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CommunityInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return build_post_view(post, post_repo=post_repo, like_repo=like_repo, current_user_id=current_user.id)


@router.get("/groups/{group_id}/posts", response_model=list[PostRead])
def listar_posts(
    group_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return list_posts_for_group(
        group_id, post_repo=PostRepository(session), like_repo=LikeRepository(session), current_user_id=current_user.id
    )


@router.post("/posts/{post_id}/comments", response_model=CommentRead)
def comentar(
    post_id: int,
    body: ComentarRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        comment = handle_comentar(
            ComentarCommand(post_id=post_id, author_user_id=current_user.id, body=body.body),
            PostRepository(session), MembershipRepository(session), CommentRepository(session),
        )
    except CommunityPostNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CommunityInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return build_comment_view(comment)


@router.get("/posts/{post_id}/comments", response_model=list[CommentRead])
def listar_comentarios(post_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return [build_comment_view(c) for c in CommentRepository(session).list_for_post(post_id)]


@router.post("/posts/{post_id}/like", response_model=PostRead)
def dar_me_gusta(
    post_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    post_repo = PostRepository(session)
    like_repo = LikeRepository(session)
    try:
        handle_dar_me_gusta(
            DarMeGustaCommand(post_id=post_id, user_id=current_user.id),
            post_repo, MembershipRepository(session), like_repo,
        )
    except CommunityPostNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CommunityInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    post = post_repo.get_by_id(post_id)
    return build_post_view(post, post_repo=post_repo, like_repo=like_repo, current_user_id=current_user.id)


@router.delete("/posts/{post_id}/like", response_model=PostRead)
def quitar_me_gusta(
    post_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    post_repo = PostRepository(session)
    like_repo = LikeRepository(session)
    try:
        handle_quitar_me_gusta(QuitarMeGustaCommand(post_id=post_id, user_id=current_user.id), post_repo, like_repo)
    except CommunityPostNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CommunityInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    post = post_repo.get_by_id(post_id)
    return build_post_view(post, post_repo=post_repo, like_repo=like_repo, current_user_id=current_user.id)
