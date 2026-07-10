"""
Identity — servicios del bounded context (Sprint 1).

Comandos síncronos que el adaptador Web API invoca en proceso (Handbook,
Module Dependency Rules: Identity es Capa 0, no depende de nadie en core/).
"""

from __future__ import annotations

from sqlmodel import Session, select

from app.utils.password import get_password_hash, verify_password
from core.identity.models import User
from core.shared.events import event_bus
from core.shared.exceptions import IdentityAlreadyExists


def register_user(session: Session, *, email: str, username: str, password: str) -> User:
    existing = session.exec(select(User).where((User.email == email) | (User.username == username))).first()
    if existing:
        raise IdentityAlreadyExists(f"Ya existe un usuario con email={email} o username={username}")

    user = User(email=email, username=username, hashed_password=get_password_hash(password))
    session.add(user)
    session.commit()
    session.refresh(user)

    event_bus.publish("IdentityCreated", {"user_id": user.id, "email": user.email})
    return user


def authenticate(session: Session, *, username: str, password: str) -> User | None:
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
