"""Community — application: handlers (Sprint 5, Hito 5)."""

from __future__ import annotations

from core.community.application.commands import (
    ComentarCommand,
    CrearGrupoCommand,
    DarMeGustaCommand,
    PublicarCommand,
    QuitarMeGustaCommand,
    UnirseAGrupoCommand,
)
from core.community.domain.aggregates import (
    CommunityComment,
    CommunityGroup,
    CommunityLike,
    CommunityPost,
    GroupMembership,
)
from core.community.domain.rules import (
    validate_can_comment,
    validate_can_join,
    validate_can_like,
    validate_can_post,
    validate_can_unlike,
)
from core.community.infrastructure.repository import (
    CommentRepository,
    CommunityGroupRepository,
    LikeRepository,
    MembershipRepository,
    PostRepository,
)
from core.shared.exceptions import CommunityGroupNotFound, CommunityPostNotFound


def handle_crear_grupo(
    cmd: CrearGrupoCommand, group_repo: CommunityGroupRepository, membership_repo: MembershipRepository
) -> CommunityGroup:
    """Quien crea el grupo queda unido automáticamente -- no tendría sentido
    que el fundador de un grupo no pudiera publicar en él sin un paso extra."""

    group = group_repo.add(
        CommunityGroup(
            name=cmd.name, description=cmd.description, city=cmd.city, country=cmd.country,
            created_by_user_id=cmd.created_by_user_id,
        )
    )
    membership_repo.add(GroupMembership(group_id=group.id, user_id=cmd.created_by_user_id))
    return group


def _get_group_or_404(group_id: int, repo: CommunityGroupRepository) -> CommunityGroup:
    group = repo.get_by_id(group_id)
    if group is None:
        raise CommunityGroupNotFound(f"No existe el grupo {group_id}.")
    return group


def handle_unirse_a_grupo(
    cmd: UnirseAGrupoCommand, group_repo: CommunityGroupRepository, membership_repo: MembershipRepository
) -> GroupMembership:
    _get_group_or_404(cmd.group_id, group_repo)
    validate_can_join(already_member=membership_repo.is_member(cmd.group_id, cmd.user_id))
    return membership_repo.add(GroupMembership(group_id=cmd.group_id, user_id=cmd.user_id))


def handle_publicar(
    cmd: PublicarCommand,
    group_repo: CommunityGroupRepository,
    membership_repo: MembershipRepository,
    post_repo: PostRepository,
) -> CommunityPost:
    _get_group_or_404(cmd.group_id, group_repo)
    validate_can_post(is_member=membership_repo.is_member(cmd.group_id, cmd.author_user_id))
    return post_repo.add(CommunityPost(group_id=cmd.group_id, author_user_id=cmd.author_user_id, body=cmd.body))


def _get_post_or_404(post_id: int, repo: PostRepository) -> CommunityPost:
    post = repo.get_by_id(post_id)
    if post is None:
        raise CommunityPostNotFound(f"No existe la publicación {post_id}.")
    return post


def handle_comentar(
    cmd: ComentarCommand,
    post_repo: PostRepository,
    membership_repo: MembershipRepository,
    comment_repo: CommentRepository,
) -> CommunityComment:
    post = _get_post_or_404(cmd.post_id, post_repo)
    validate_can_comment(is_member=membership_repo.is_member(post.group_id, cmd.author_user_id))
    return comment_repo.add(CommunityComment(post_id=cmd.post_id, author_user_id=cmd.author_user_id, body=cmd.body))


def handle_dar_me_gusta(
    cmd: DarMeGustaCommand,
    post_repo: PostRepository,
    membership_repo: MembershipRepository,
    like_repo: LikeRepository,
) -> CommunityLike:
    post = _get_post_or_404(cmd.post_id, post_repo)
    validate_can_like(
        is_member=membership_repo.is_member(post.group_id, cmd.user_id),
        already_liked=like_repo.get(cmd.post_id, cmd.user_id) is not None,
    )
    return like_repo.add(CommunityLike(post_id=cmd.post_id, user_id=cmd.user_id))


def handle_quitar_me_gusta(cmd: QuitarMeGustaCommand, post_repo: PostRepository, like_repo: LikeRepository) -> None:
    _get_post_or_404(cmd.post_id, post_repo)
    like = like_repo.get(cmd.post_id, cmd.user_id)
    validate_can_unlike(already_liked=like is not None)
    like_repo.remove(like)
