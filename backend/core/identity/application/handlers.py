"""Identity — application: handlers de comando/query."""

from __future__ import annotations

from app.utils.password import get_password_hash, verify_password
from core.identity.application.commands import (
    AuthenticateCommand,
    RegisterUserCommand,
    RequestPasswordResetCommand,
    ResetPasswordCommand,
    VerifyEmailCommand,
)
from core.identity.domain.aggregates import User
from core.identity.domain.rules import (
    InvalidTokenError,
    generate_token,
    hash_token,
    is_expired,
    reset_expiry,
    validate_password,
    verification_expiry,
)
from core.identity.infrastructure.repository import UserRepository
from core.shared.events import event_bus
from core.shared.exceptions import IdentityAlreadyExists


def handle_register_user(cmd: RegisterUserCommand, repo: UserRepository) -> tuple[User, str]:
    """Devuelve `(usuario, token_de_verificacion_en_claro)`.

    El token en claro solo existe acá y en el email: en la base se guarda su
    hash (ver domain/rules.py). Quien orquesta es responsable de enviarlo."""

    if repo.get_by_email_or_username(cmd.email, cmd.username):
        raise IdentityAlreadyExists(f"Ya existe un usuario con email={cmd.email} o username={cmd.username}")

    validate_password(cmd.password)

    raw_token, token_hash = generate_token()
    user = User(
        email=cmd.email,
        username=cmd.username,
        hashed_password=get_password_hash(cmd.password),
        email_verification_token=token_hash,
        email_verification_expires_at=verification_expiry(),
    )
    user = repo.add(user)

    event_bus.publish("IdentityCreated", {"user_id": user.id, "email": user.email})
    return user, raw_token


def handle_verify_email(cmd: VerifyEmailCommand, repo: UserRepository) -> User:
    """Idempotente a propósito: volver a abrir el mismo enlace devuelve
    éxito, no error.

    Es un caso real y frecuente -- la gente hace clic dos veces, y algunos
    clientes de correo pre-cargan los enlaces antes de que la persona los
    abra. Mostrar "enlace inválido" después de una verificación exitosa
    haría creer que algo falló cuando no falló nada.

    Por eso el token NO se borra al verificar (a diferencia del de
    recuperación, que sí es de un solo uso). Mantenerlo es seguro: sobre una
    cuenta ya verificada, lo único que puede hacer es volver a marcarla como
    verificada. No abre ningún camino a tomar la cuenta."""

    user = repo.get_by_verification_token(hash_token(cmd.token))
    if user is None:
        raise InvalidTokenError("El enlace de verificación no es válido.")

    if user.email_verified:
        return user

    if is_expired(user.email_verification_expires_at):
        raise InvalidTokenError("El enlace de verificación venció. Pedí uno nuevo.")

    user.email_verified = True
    user.email_verification_expires_at = None
    user = repo.save(user)

    event_bus.publish("IdentityEmailVerified", {"user_id": user.id, "email": user.email})
    return user


def handle_issue_verification_token(user: User, repo: UserRepository) -> str:
    """Reemite el token (reenviar email). Invalida el anterior por diseño:
    solo el último enlace enviado debe funcionar."""
    raw_token, token_hash = generate_token()
    user.email_verification_token = token_hash
    user.email_verification_expires_at = verification_expiry()
    repo.save(user)
    return raw_token


def handle_request_password_reset(
    cmd: RequestPasswordResetCommand, repo: UserRepository
) -> tuple[User, str] | None:
    """Devuelve `(usuario, token_en_claro)` si el email existe, o `None`.

    IMPORTANTE: quien llama debe responder lo mismo en ambos casos. Si el
    API respondiera distinto para un email registrado que para uno que no lo
    está, se convertiría en un oráculo para enumerar usuarios."""

    user = repo.get_by_email(cmd.email)
    if user is None:
        return None

    raw_token, token_hash = generate_token()
    user.password_reset_token = token_hash
    user.password_reset_expires_at = reset_expiry()
    user = repo.save(user)
    return user, raw_token


def handle_reset_password(cmd: ResetPasswordCommand, repo: UserRepository) -> User:
    user = repo.get_by_reset_token(hash_token(cmd.token))
    if user is None:
        raise InvalidTokenError("El enlace de recuperación no es válido o ya se usó.")
    if is_expired(user.password_reset_expires_at):
        raise InvalidTokenError("El enlace de recuperación venció. Pedí uno nuevo.")

    validate_password(cmd.new_password)

    user.hashed_password = get_password_hash(cmd.new_password)
    user.password_reset_token = None          # un solo uso
    user.password_reset_expires_at = None
    # Recuperar la contraseña por email demuestra control de la casilla, que
    # es justamente lo que verifica el email. No tiene sentido seguir
    # pidiéndole verificar después de esto.
    user.email_verified = True
    user = repo.save(user)

    event_bus.publish("IdentityPasswordReset", {"user_id": user.id})
    return user


def handle_authenticate(cmd: AuthenticateCommand, repo: UserRepository) -> User | None:
    user = repo.get_by_username(cmd.username)
    if not user or not verify_password(cmd.password, user.hashed_password):
        return None
    return user
