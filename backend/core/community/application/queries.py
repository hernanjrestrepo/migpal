"""Community — application: consultas (Sprint 5, Hito 5)."""

from __future__ import annotations

from dataclasses import dataclass

from core.community.domain.aggregates import CommunityComment, CommunityGroup, CommunityPost
from core.community.infrastructure.repository import (
    CommunityGroupRepository,
    LikeRepository,
    MembershipRepository,
    PostRepository,
)


@dataclass(frozen=True)
class GroupView:
    id: int
    name: str
    description: str | None
    city: str | None
    country: str | None
    member_count: int
    is_member: bool


@dataclass(frozen=True)
class PostView:
    id: int
    group_id: int
    author_user_id: int
    body: str
    created_at: str
    like_count: int
    comment_count: int
    liked_by_me: bool


def build_group_view(
    group: CommunityGroup,
    *,
    group_repo: CommunityGroupRepository,
    membership_repo: MembershipRepository,
    current_user_id: int,
) -> GroupView:
    return GroupView(
        id=group.id,
        name=group.name,
        description=group.description,
        city=group.city,
        country=group.country,
        member_count=group_repo.member_count(group.id),
        is_member=membership_repo.is_member(group.id, current_user_id),
    )


def list_groups(
    group_repo: CommunityGroupRepository, membership_repo: MembershipRepository, current_user_id: int
) -> list[GroupView]:
    return [
        build_group_view(g, group_repo=group_repo, membership_repo=membership_repo, current_user_id=current_user_id)
        for g in group_repo.list_all()
    ]


def build_post_view(
    post: CommunityPost, *, post_repo: PostRepository, like_repo: LikeRepository, current_user_id: int
) -> PostView:
    return PostView(
        id=post.id,
        group_id=post.group_id,
        author_user_id=post.author_user_id,
        body=post.body,
        created_at=post.created_at.isoformat(),
        like_count=post_repo.like_count(post.id),
        comment_count=post_repo.comment_count(post.id),
        liked_by_me=like_repo.get(post.id, current_user_id) is not None,
    )


def list_posts_for_group(
    group_id: int, *, post_repo: PostRepository, like_repo: LikeRepository, current_user_id: int
) -> list[PostView]:
    return [
        build_post_view(p, post_repo=post_repo, like_repo=like_repo, current_user_id=current_user_id)
        for p in post_repo.list_for_group(group_id)
    ]


@dataclass(frozen=True)
class CommentView:
    id: int
    post_id: int
    author_user_id: int
    body: str
    created_at: str


def build_comment_view(comment: CommunityComment) -> CommentView:
    return CommentView(
        id=comment.id, post_id=comment.post_id, author_user_id=comment.author_user_id,
        body=comment.body, created_at=comment.created_at.isoformat(),
    )
