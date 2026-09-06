"""Community — infrastructure: persistencia (Sprint 5, Hito 5)."""

from __future__ import annotations

from sqlmodel import Session, func, select

from core.community.domain.aggregates import (
    CommunityComment,
    CommunityGroup,
    CommunityLike,
    CommunityPost,
    GroupMembership,
)


class CommunityGroupRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, group: CommunityGroup) -> CommunityGroup:
        self._session.add(group)
        self._session.commit()
        self._session.refresh(group)
        return group

    def get_by_id(self, group_id: int) -> CommunityGroup | None:
        return self._session.get(CommunityGroup, group_id)

    def list_all(self) -> list[CommunityGroup]:
        return list(self._session.exec(select(CommunityGroup).order_by(CommunityGroup.name)))

    def member_count(self, group_id: int) -> int:
        return self._session.exec(
            select(func.count()).select_from(GroupMembership).where(GroupMembership.group_id == group_id)
        ).one()


class MembershipRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, membership: GroupMembership) -> GroupMembership:
        self._session.add(membership)
        self._session.commit()
        self._session.refresh(membership)
        return membership

    def is_member(self, group_id: int, user_id: int) -> bool:
        return (
            self._session.exec(
                select(GroupMembership).where(
                    GroupMembership.group_id == group_id, GroupMembership.user_id == user_id
                )
            ).first()
            is not None
        )


class PostRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, post: CommunityPost) -> CommunityPost:
        self._session.add(post)
        self._session.commit()
        self._session.refresh(post)
        return post

    def get_by_id(self, post_id: int) -> CommunityPost | None:
        return self._session.get(CommunityPost, post_id)

    def list_for_group(self, group_id: int) -> list[CommunityPost]:
        return list(
            self._session.exec(
                select(CommunityPost)
                .where(CommunityPost.group_id == group_id)
                .order_by(CommunityPost.created_at.desc())
            )
        )

    def comment_count(self, post_id: int) -> int:
        return self._session.exec(
            select(func.count()).select_from(CommunityComment).where(CommunityComment.post_id == post_id)
        ).one()

    def like_count(self, post_id: int) -> int:
        return self._session.exec(
            select(func.count()).select_from(CommunityLike).where(CommunityLike.post_id == post_id)
        ).one()


class CommentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, comment: CommunityComment) -> CommunityComment:
        self._session.add(comment)
        self._session.commit()
        self._session.refresh(comment)
        return comment

    def list_for_post(self, post_id: int) -> list[CommunityComment]:
        return list(
            self._session.exec(
                select(CommunityComment)
                .where(CommunityComment.post_id == post_id)
                .order_by(CommunityComment.created_at)
            )
        )


class LikeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, like: CommunityLike) -> CommunityLike:
        self._session.add(like)
        self._session.commit()
        self._session.refresh(like)
        return like

    def get(self, post_id: int, user_id: int) -> CommunityLike | None:
        return self._session.exec(
            select(CommunityLike).where(CommunityLike.post_id == post_id, CommunityLike.user_id == user_id)
        ).first()

    def remove(self, like: CommunityLike) -> None:
        self._session.delete(like)
        self._session.commit()
