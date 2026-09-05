"""Identity — infrastructure: persistencia. Único lugar que conoce Session."""

from __future__ import annotations

from datetime import datetime

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

    def get_by_email(self, email: str) -> User | None:
        return self._session.exec(select(User).where(User.email == email)).first()

    def get_by_verification_token(self, token_hash: str) -> User | None:
        """Busca por el HASH del token, nunca por el token en claro -- en la
        base solo vive el hash (ver domain/rules.py)."""
        return self._session.exec(
            select(User).where(User.email_verification_token == token_hash)
        ).first()

    def get_by_reset_token(self, token_hash: str) -> User | None:
        return self._session.exec(
            select(User).where(User.password_reset_token == token_hash)
        ).first()

    def add(self, user: User) -> User:
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user

    def save(self, user: User) -> User:
        """Persiste un usuario ya modificado (verificación, cambio de
        contraseña, emisión de token)."""
        user.updated_at = datetime.utcnow()
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user
