"""
Case Engine — domain: Aggregate Root MigrationCase + entidad CaseFamilyMember
(Anexo A).

Nota de implementación: estas clases son SQLModel `table=True` -- en este
proyecto el modelo de dominio y el mapeo ORM son la misma clase (compromiso
deliberado de velocidad; separar un DTO de dominio puro de la fila de tabla
duplicaría cada campo sin aportar aislamiento real mientras el proyecto siga
en un único proceso/una única base). Lo que SÍ se separa estrictamente es la
*capa*: nada fuera de `infrastructure/repository.py` importa `Session` ni
hace `session.add/commit`, y nada fuera de `adapters/api.py` conoce FastAPI.
Ese es el límite que main.py estaba a punto de saltarse.

Regla de diseño vinculante (Anexo A): "Case Engine nunca contiene lógica.
Solo estado y consistencia del caso." Estas clases no tienen métodos de
negocio -- son estado puro. La lógica de transición vive en application/.
"""

from datetime import UTC, datetime
from typing import List  # noqa: UP035 -- ver nota junto a family_members

from sqlmodel import Field, Relationship, SQLModel

from core.case_engine.domain.value_objects import CaseStatus


class MigrationCase(SQLModel, table=True):
    """Aggregate Root. Frontera transaccional (Anexo D)."""

    __tablename__ = "migration_cases"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, unique=True)

    status: CaseStatus = Field(default=CaseStatus.DRAFT, index=True)

    objective_country: str | None = Field(default=None)
    objective_visa_type: str | None = Field(default=None)
    next_step_ref: str | None = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # typing.List, no el builtin `list` -- SQLAlchemy 2.0 no resuelve el
    # genérico builtin dentro de Relationship() (InvalidRequestError en
    # tiempo de arranque). No dejar que ruff "modernice" esto (UP006/UP035).
    family_members: List["CaseFamilyMember"] = Relationship(back_populates="case")  # noqa: UP006, UP035


class CaseFamilyMember(SQLModel, table=True):
    """Entidad dentro del aggregate MigrationCase (Anexo A)."""

    __tablename__ = "case_family_members"

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="migration_cases.id", index=True)

    full_name: str
    relationship_type: str  # spouse, child, other
    birth_date: datetime | None = Field(default=None)

    case: MigrationCase | None = Relationship(back_populates="family_members")
