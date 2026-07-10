"""
Identity — Aggregate Root: User (Anexo A).

Sprint 1, regla "reutiliza primero, refactoriza después, reconstruye solo
cuando sea imprescindible": la tabla `user` ya existe, está probada y migrada
(alembic 8310df2c8f4c). No se duplica -- este módulo re-exporta el modelo
real como la superficie oficial del bounded context Identity, para que el
resto de core/ dependa de `core.identity`, nunca de `app.models` directamente
(regla obligatoria 01: ningún contexto accede a la tabla de otro sin pasar
por su API).
"""

from app.models.user import User, UserCreate, UserRead

__all__ = ["User", "UserCreate", "UserRead"]
