"""
Fixtures compartidos de pytest (Sprint 0 — Foundation).

Antes, varios tests (test_data_sources.py, test_knowledge.py,
test_marketplace.py) importaban `app.db.session.engine` asumiendo que las
tablas ya existían -- dependían de que `migpal.db` estuviera previamente
poblado a mano, en vez de crear su propio esquema. Esto los hacía fallar en
cualquier checkout limpio (exactamente el problema que Foundation existe
para eliminar).
"""

import pytest
from sqlmodel import SQLModel

from app.db.base import metadata  # noqa: F401 (importa y registra todos los modelos)
from app.db.session import engine


@pytest.fixture(scope="session", autouse=True)
def _create_test_schema():
    """Crea el esquema completo una vez por sesión de test, sobre el motor
    configurado por DATABASE_URL (SQLite local por defecto, Postgres en CI)."""
    SQLModel.metadata.create_all(engine)
    yield
