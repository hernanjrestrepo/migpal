"""
Fixtures compartidos de pytest (Sprint 0 — Foundation).

Antes, varios tests (test_data_sources.py, test_knowledge.py,
test_marketplace.py) importaban `app.db.session.engine` asumiendo que las
tablas ya existían -- dependían de que `migpal.db` estuviera previamente
poblado a mano, en vez de crear su propio esquema. Esto los hacía fallar en
cualquier checkout limpio (exactamente el problema que Foundation existe
para eliminar).
"""

import os

import pytest
from sqlmodel import SQLModel

# Debe fijarse ANTES de importar `app.middleware` (lee el entorno al
# importarse). Los contract tests registran y loguean decenas de usuarios
# seguidos desde la IP única del TestClient, y chocarían con el rate limit
# de producción. El limitador se prueba aparte, directo, en
# tests/unit/test_middleware.py.
#
# Asignación directa, NO `setdefault`: el contenedor ya define
# RATE_LIMIT_ENABLED=true (docker-compose.yml), así que un setdefault no
# haría nada y la suite seguiría chocando con el límite.
os.environ["RATE_LIMIT_ENABLED"] = "false"

# Mismo criterio, mismo motivo de orden (antes de que se importe
# `app.config`, que lee el entorno una sola vez al crear `settings`):
# `.env` de este entorno de desarrollo trae credenciales SMTP reales
# (la cuenta real de Paradixe) para que un humano pueda probar el flujo
# de verificación/recuperación a mano. Los contract tests registran
# decenas de usuarios por corrida con emails @example.com -- sin este
# blanqueo, cada uno dispara un envío real a través de esa cuenta real
# (incidente real, 7 sept 2026: una corrida completa de la suite inundó
# la bandeja de entrada real con cientos de correos de verificación).
# `app/services/email_sender.py::_smtp_configured()` ya está diseñado
# para no fallar si el SMTP no está configurado -- solo hace falta
# asegurar que "no configurado" sea lo que vea el proceso de test,
# nunca lo que haya en `.env`.
os.environ["SMTP_HOST"] = ""
os.environ["SMTP_USER"] = ""
os.environ["SMTP_PASSWORD"] = ""

from app.db.base import metadata  # noqa: E402,F401 (importa y registra todos los modelos)
from app.db.session import engine  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _create_test_schema():
    """Crea el esquema completo una vez por sesión de test, sobre el motor
    configurado por DATABASE_URL (SQLite local por defecto, Postgres en CI)."""
    SQLModel.metadata.create_all(engine)
    yield
