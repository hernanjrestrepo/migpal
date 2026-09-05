"""
Identity — domain: reglas de tokens de verificación y recuperación.

Funciones puras, sin DB y sin efectos secundarios -- mismo criterio que
`recommendation/domain/rules.py` y `execution_plan/domain/rules.py`.

Decisión de seguridad central de este módulo: **el token se entrega en claro
a la persona (por email) pero en la base solo se guarda su hash SHA-256**.

Por qué importa: un token de recuperación en claro en la base es una llave
maestra. Quien consiga una copia del backup —o una inyección SQL de solo
lectura— podría tomar cualquier cuenta sin conocer ninguna contraseña.
Guardando el hash, la base deja de contener nada reutilizable: para tomar
una cuenta hay que interceptar el email concreto.

Es el mismo razonamiento que ya se aplica a `hashed_password`; acá se
extiende a los tokens, que son credenciales temporales igual de sensibles.

Se usa SHA-256 y no bcrypt a propósito: bcrypt existe para resistir fuerza
bruta sobre secretos de baja entropía elegidos por humanos. Estos tokens son
256 bits de `secrets.token_urlsafe`, no adivinables por fuerza bruta, y se
verifican en cada request -- un hash lento acá solo agregaría latencia sin
ganar seguridad.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

# Ventanas de validez. La de recuperación es corta a propósito: es la que
# permite tomar el control de una cuenta.
EMAIL_VERIFICATION_TTL = timedelta(hours=24)
PASSWORD_RESET_TTL = timedelta(hours=1)

MIN_PASSWORD_LENGTH = 8


class WeakPasswordError(ValueError):
    """La contraseña no cumple el mínimo exigido."""


class InvalidTokenError(ValueError):
    """El token no existe, ya se usó, o expiró."""


def generate_token() -> tuple[str, str]:
    """Devuelve `(token_en_claro, hash_para_guardar)`.

    El primero va al email de la persona; el segundo es lo único que toca la
    base de datos."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def verification_expiry(now: datetime | None = None) -> datetime:
    return (now or datetime.now(UTC)) + EMAIL_VERIFICATION_TTL


def reset_expiry(now: datetime | None = None) -> datetime:
    return (now or datetime.now(UTC)) + PASSWORD_RESET_TTL


def is_expired(expires_at: datetime | None, now: datetime | None = None) -> bool:
    """Un token sin fecha de expiración se considera expirado: no se confía
    en un estado incompleto para conceder acceso."""
    if expires_at is None:
        return True
    reference = now or datetime.now(UTC)
    # Las fechas guardadas por SQLModel pueden venir sin tzinfo (naive).
    # Compararlas con una fecha aware lanza TypeError, así que se normaliza.
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=UTC)
    return reference >= expires_at


def validate_password(password: str) -> None:
    """Mínimo real, no decorativo. La política completa (mayúsculas,
    símbolos) se deja al medidor de la UI: forzarla acá empuja a la gente a
    patrones predecibles tipo `Password1!`, que no suman seguridad."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise WeakPasswordError(
            f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres."
        )
