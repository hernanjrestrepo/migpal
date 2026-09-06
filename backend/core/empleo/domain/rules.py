"""Empleo — domain: invariantes (Sprint 10b, Hito 5)."""

from __future__ import annotations

import secrets
import string


class EmpleoInvariantError(ValueError):
    """Se violó una invariante de Empleo."""


def validate_can_connect(*, already_connected: bool) -> None:
    if already_connected:
        raise EmpleoInvariantError("Este caso ya tiene una cuenta de JobXeeker conectada.")


def generate_service_credentials(case_id: int) -> tuple[str, str]:
    """Igual criterio que `core.negocio.domain.rules` -- email
    determinístico por caso, contraseña aleatoria de un solo uso. Acá la
    contraseña se descarta después de usarla una vez (ver docstring de
    `domain/aggregates.py`: JobXeeker sí tiene refresh token, no hace falta
    guardarla)."""

    email = f"migpal-case-{case_id}@migpal.internal"
    alphabet = string.ascii_letters + string.digits
    password = "".join(secrets.choice(alphabet) for _ in range(24))
    return email, password
