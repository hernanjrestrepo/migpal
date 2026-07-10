"""Identity — application: handlers de comando/query."""

from __future__ import annotations

from app.utils.password import get_password_hash, verify_password
from core.identity.application.commands import AuthenticateCommand, RegisterUserCommand
from core.identity.domain.aggregates import User
from core.identity.infrastructure.repository import UserRepository
from core.shared.events import event_bus
from core.shared.exceptions import IdentityAlreadyExists


def handle_register_user(cmd: RegisterUserCommand, repo: UserRepository) -> User:
    if repo.get_by_email_or_username(cmd.email, cmd.username):
        raise IdentityAlreadyExists(f"Ya existe un usuario con email={cmd.email} o username={cmd.username}")

    user = User(email=cmd.email, username=cmd.username, hashed_password=get_password_hash(cmd.password))
    user = repo.add(user)

    event_bus.publish("IdentityCreated", {"user_id": user.id, "email": user.email})
    return user


def handle_authenticate(cmd: AuthenticateCommand, repo: UserRepository) -> User | None:
    user = repo.get_by_username(cmd.username)
    if not user or not verify_password(cmd.password, user.hashed_password):
        return None
    return user
