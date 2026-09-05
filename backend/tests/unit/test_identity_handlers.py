"""
Identity — handlers de verificación de email y recuperación de contraseña.

Repositorio en memoria (mismo patrón que test_recommendation_handlers.py),
sin DB. Lo que se prueba son las decisiones de seguridad del flujo, no el
happy path solamente: un solo uso del token de reset, idempotencia del
enlace de verificación, y que el flujo no revele qué emails existen.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.utils.password import verify_password
from core.identity.application.commands import (
    RegisterUserCommand,
    RequestPasswordResetCommand,
    ResetPasswordCommand,
    VerifyEmailCommand,
)
from core.identity.application.handlers import (
    handle_issue_verification_token,
    handle_register_user,
    handle_request_password_reset,
    handle_reset_password,
    handle_verify_email,
)
from core.identity.domain.aggregates import User
from core.identity.domain.rules import InvalidTokenError, WeakPasswordError
from core.shared.exceptions import IdentityAlreadyExists


class _InMemoryUserRepository:
    """Mismo contrato que la versión real contra Postgres."""

    def __init__(self):
        self._by_id: dict[int, User] = {}
        self._next_id = 1

    def add(self, user: User) -> User:
        user.id = self._next_id
        self._next_id += 1
        self._by_id[user.id] = user
        return user

    def save(self, user: User) -> User:
        self._by_id[user.id] = user
        return user

    def get_by_email_or_username(self, email, username):
        return next(
            (u for u in self._by_id.values() if u.email == email or u.username == username), None
        )

    def get_by_username(self, username):
        return next((u for u in self._by_id.values() if u.username == username), None)

    def get_by_email(self, email):
        return next((u for u in self._by_id.values() if u.email == email), None)

    def get_by_verification_token(self, token_hash):
        return next(
            (u for u in self._by_id.values() if u.email_verification_token == token_hash), None
        )

    def get_by_reset_token(self, token_hash):
        return next((u for u in self._by_id.values() if u.password_reset_token == token_hash), None)


def _registrar(repo, email="ana@ejemplo.com", username="ana", password="Passw0rd!"):
    return handle_register_user(
        RegisterUserCommand(email=email, username=username, password=password), repo
    )


# -------------------------------------------------------------- registro


def test_al_registrar_se_emite_un_token_y_la_cuenta_nace_sin_verificar():
    repo = _InMemoryUserRepository()
    user, raw_token = _registrar(repo)

    assert user.email_verified is False
    assert raw_token
    # En la base queda el hash, no el token que se manda por email.
    assert user.email_verification_token != raw_token
    assert user.email_verification_expires_at is not None


def test_la_contrasena_nunca_se_guarda_en_claro():
    repo = _InMemoryUserRepository()
    user, _ = _registrar(repo, password="MiClaveSecreta1")

    assert user.hashed_password != "MiClaveSecreta1"
    assert verify_password("MiClaveSecreta1", user.hashed_password)


def test_no_permite_registrar_dos_veces_el_mismo_email():
    repo = _InMemoryUserRepository()
    _registrar(repo)
    with pytest.raises(IdentityAlreadyExists):
        _registrar(repo, username="otro")


def test_rechaza_contrasenas_debiles_al_registrar():
    repo = _InMemoryUserRepository()
    with pytest.raises(WeakPasswordError):
        _registrar(repo, password="corta")


# ---------------------------------------------------- verificación de email


def test_verificar_con_el_token_correcto_marca_la_cuenta():
    repo = _InMemoryUserRepository()
    user, raw_token = _registrar(repo)

    verificado = handle_verify_email(VerifyEmailCommand(token=raw_token), repo)

    assert verificado.email_verified is True
    assert verificado.email_verification_expires_at is None


def test_verificar_dos_veces_el_mismo_enlace_no_da_error():
    """Caso real y frecuente: la gente hace clic dos veces, y algunos
    clientes de correo pre-cargan el enlace. Mostrar 'inválido' después de
    una verificación exitosa haría creer que algo falló."""
    repo = _InMemoryUserRepository()
    _, raw_token = _registrar(repo)

    handle_verify_email(VerifyEmailCommand(token=raw_token), repo)
    otra_vez = handle_verify_email(VerifyEmailCommand(token=raw_token), repo)

    assert otra_vez.email_verified is True


def test_verificar_con_token_inventado_falla():
    repo = _InMemoryUserRepository()
    _registrar(repo)
    with pytest.raises(InvalidTokenError):
        handle_verify_email(VerifyEmailCommand(token="no-existe"), repo)


def test_verificar_con_token_vencido_falla():
    repo = _InMemoryUserRepository()
    user, raw_token = _registrar(repo)
    user.email_verification_expires_at = datetime.now(UTC) - timedelta(minutes=1)
    repo.save(user)

    with pytest.raises(InvalidTokenError):
        handle_verify_email(VerifyEmailCommand(token=raw_token), repo)


def test_reenviar_invalida_el_token_anterior():
    """Solo el último enlace enviado debe funcionar: si el primero siguiera
    vivo, un email viejo filtrado seguiría sirviendo."""
    repo = _InMemoryUserRepository()
    user, primer_token = _registrar(repo)

    segundo_token = handle_issue_verification_token(user, repo)

    assert segundo_token != primer_token
    with pytest.raises(InvalidTokenError):
        handle_verify_email(VerifyEmailCommand(token=primer_token), repo)
    assert handle_verify_email(VerifyEmailCommand(token=segundo_token), repo).email_verified


# -------------------------------------------------- recuperación de contraseña


def test_pedir_recuperacion_de_un_email_inexistente_devuelve_none():
    """Devolver `None` en vez de lanzar es lo que permite al adapter
    responder igual exista o no la cuenta, y no delatar qué emails están
    registrados."""
    repo = _InMemoryUserRepository()
    assert handle_request_password_reset(RequestPasswordResetCommand(email="nadie@x.com"), repo) is None


def test_pedir_recuperacion_emite_un_token_con_vencimiento():
    repo = _InMemoryUserRepository()
    _registrar(repo)

    user, raw_token = handle_request_password_reset(
        RequestPasswordResetCommand(email="ana@ejemplo.com"), repo
    )

    assert raw_token
    assert user.password_reset_token != raw_token   # se guarda hasheado
    assert user.password_reset_expires_at is not None


def test_restablecer_cambia_la_contrasena_de_verdad():
    repo = _InMemoryUserRepository()
    _registrar(repo, password="ViejaClave1")
    _, raw_token = handle_request_password_reset(
        RequestPasswordResetCommand(email="ana@ejemplo.com"), repo
    )

    user = handle_reset_password(
        ResetPasswordCommand(token=raw_token, new_password="NuevaClave2026"), repo
    )

    assert verify_password("NuevaClave2026", user.hashed_password)
    assert not verify_password("ViejaClave1", user.hashed_password)


def test_el_token_de_recuperacion_es_de_un_solo_uso():
    """Si el token siguiera sirviendo, cualquiera con acceso al email viejo
    podría volver a tomar la cuenta más adelante."""
    repo = _InMemoryUserRepository()
    _registrar(repo)
    _, raw_token = handle_request_password_reset(
        RequestPasswordResetCommand(email="ana@ejemplo.com"), repo
    )

    handle_reset_password(ResetPasswordCommand(token=raw_token, new_password="Primera2026"), repo)

    with pytest.raises(InvalidTokenError):
        handle_reset_password(ResetPasswordCommand(token=raw_token, new_password="Segunda2026"), repo)


def test_restablecer_con_token_vencido_falla():
    repo = _InMemoryUserRepository()
    _registrar(repo)
    user, raw_token = handle_request_password_reset(
        RequestPasswordResetCommand(email="ana@ejemplo.com"), repo
    )
    user.password_reset_expires_at = datetime.now(UTC) - timedelta(minutes=1)
    repo.save(user)

    with pytest.raises(InvalidTokenError):
        handle_reset_password(ResetPasswordCommand(token=raw_token, new_password="Nueva2026"), repo)


def test_restablecer_rechaza_una_contrasena_debil():
    repo = _InMemoryUserRepository()
    _registrar(repo)
    _, raw_token = handle_request_password_reset(
        RequestPasswordResetCommand(email="ana@ejemplo.com"), repo
    )

    with pytest.raises(WeakPasswordError):
        handle_reset_password(ResetPasswordCommand(token=raw_token, new_password="corta"), repo)


def test_restablecer_tambien_deja_el_email_verificado():
    """Haber recibido el enlace demuestra control de la casilla, que es
    exactamente lo que verifica el email. Seguir pidiéndolo después sería
    fricción sin sentido."""
    repo = _InMemoryUserRepository()
    _registrar(repo)
    _, raw_token = handle_request_password_reset(
        RequestPasswordResetCommand(email="ana@ejemplo.com"), repo
    )

    user = handle_reset_password(
        ResetPasswordCommand(token=raw_token, new_password="NuevaClave2026"), repo
    )

    assert user.email_verified is True
