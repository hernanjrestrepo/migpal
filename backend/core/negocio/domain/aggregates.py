"""
Negocio — domain: integración con ADAN (Sprint 10, Hito 5).

ADAN no expone refresh token (verificado contra su OpenAPI real, 6 sept
2026 -- `TokenResponse` solo trae `access_token`) y su JWT dura 24h por
defecto (`JWT_EXPIRATION_MINUTES=1440`). Sin refresh, la única forma de
obtener un token nuevo cuando el guardado vence es volver a loguearse --
por eso `adan_password` se guarda acá, a diferencia de todo lo demás en
este repo (que solo guarda contraseñas hasheadas, nunca en texto plano).

Nota de seguridad explícita, no un descuido: esto es aceptable para un
piloto con un puñado de casos, pero antes de producción real esto tiene
que migrar a un secreto cifrado o a un mecanismo de credencial de servicio
si ADAN llega a ofrecer uno."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class NegocioIntegration(SQLModel, table=True):
    __tablename__ = "negocio_integrations"

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="migration_cases.id", index=True, unique=True)

    adan_email: str
    adan_password: str
    adan_user_id: str
    adan_company_id: str

    access_token: str
    token_created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
