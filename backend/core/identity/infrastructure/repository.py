"""Identity — infrastructure: persistencia. Único lugar que conoce Session."""

from __future__ import annotations

from sqlmodel import Session, select

from core.identity.domain.aggregates import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_email_or_username(self, email: str, username: str) -> User | None:
        return self._session.exec(
            select(User).where((User.email == email) | (User.username == username))
        ).first()

    def get_by_username(self, username: str) -> User | None:
        return self._session.exec(select(User).where(User.username == username)).first()

    def add(self, user: User) -> User:
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user
