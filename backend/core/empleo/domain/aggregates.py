"""
Empleo — domain: integración con JobXeeker (Sprint 10b, Hito 5).

A diferencia de `core/negocio` (ADAN, sin refresh token, obligado a guardar
la contraseña de la cuenta de servicio), JobXeeker sí expone
`POST /api/auth/refresh` con un refresh token rotativo -- verificado en
vivo el 6 sept 2026. Por eso acá **no se guarda ninguna contraseña**: se
usa una sola vez en el registro y se descarta; de ahí en adelante todo pasa
por el refresh token, que se reemplaza en cada uso (rota)."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class EmpleoIntegration(SQLModel, table=True):
    __tablename__ = "empleo_integrations"

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="migration_cases.id", index=True, unique=True)

    jobxeeker_user_id: str
    access_token: str
    refresh_token: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
