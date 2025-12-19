# app/db/base.py
"""
Carga explícitamente todos los modelos para que SQLModel.metadata
quede poblada y Alembic autogenerate detecte las tablas.
"""

from sqlmodel import SQLModel

# Importa TODOS los modelos aquí (side-effect: registran tablas en metadata)
from app.models.user import User  # noqa: F401
from app.models.referral_level import ReferralLevel  # noqa: F401

# Resuelve las referencias circulares (forward references) entre los modelos
User.model_rebuild()
ReferralLevel.model_rebuild()

metadata = SQLModel.metadata
