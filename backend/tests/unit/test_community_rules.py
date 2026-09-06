"""Community — domain rules (Sprint 5, Hito 5). Funciones puras, sin DB."""

import pytest

from core.community.domain.rules import (
    CommunityInvariantError,
    validate_can_comment,
    validate_can_join,
    validate_can_like,
    validate_can_post,
    validate_can_unlike,
)


def test_validate_can_join_allows_new_member():
    validate_can_join(already_member=False)  # no debe lanzar


def test_validate_can_join_raises_if_already_member():
    with pytest.raises(CommunityInvariantError):
        validate_can_join(already_member=True)


def test_validate_can_post_raises_if_not_member():
    with pytest.raises(CommunityInvariantError):
        validate_can_post(is_member=False)


def test_validate_can_comment_raises_if_not_member():
    with pytest.raises(CommunityInvariantError):
        validate_can_comment(is_member=False)


def test_validate_can_like_raises_if_not_member():
    with pytest.raises(CommunityInvariantError):
        validate_can_like(is_member=False, already_liked=False)


def test_validate_can_like_raises_if_already_liked():
    with pytest.raises(CommunityInvariantError):
        validate_can_like(is_member=True, already_liked=True)


def test_validate_can_like_allows_member_who_has_not_liked_yet():
    validate_can_like(is_member=True, already_liked=False)  # no debe lanzar


def test_validate_can_unlike_raises_if_never_liked():
    with pytest.raises(CommunityInvariantError):
        validate_can_unlike(already_liked=False)


def test_validate_can_unlike_allows_if_already_liked():
    validate_can_unlike(already_liked=True)  # no debe lanzar
