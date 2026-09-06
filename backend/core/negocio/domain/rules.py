"""Negocio — domain: invariantes (Sprint 10, Hito 5)."""

from __future__ import annotations

import secrets
import string


class NegocioInvariantError(ValueError):
    """Se violó una invariante de Negocio."""


def validate_can_connect(*, already_connected: bool) -> None:
    if already_connected:
        raise NegocioInvariantError("Este caso ya tiene una cuenta de ADAN conectada.")


def generate_service_credentials(case_id: int) -> tuple[str, str]:
    """Email determinístico por caso (para poder reconocerlo del lado de
    ADAN si hace falta soporte), contraseña aleatoria de un solo uso --
    nunca se reutiliza entre casos, nunca la elige un humano."""

    email = f"migpal-case-{case_id}@migpal.internal"
    alphabet = string.ascii_letters + string.digits
    password = "".join(secrets.choice(alphabet) for _ in range(24))
    return email, password
