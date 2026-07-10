"""
Identity — domain: Aggregate Root User.

"Reutiliza primero" (regla de Sprint 1): la tabla `user` ya existe, probada
y migrada. No se duplica -- se reexporta como la superficie oficial de
dominio de este bounded context.
"""

from app.models.user import User, UserCreate, UserRead

__all__ = ["User", "UserCreate", "UserRead"]
