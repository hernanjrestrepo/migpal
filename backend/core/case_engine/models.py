"""
Case Engine — Aggregate Root: MigrationCase (Anexo A, Domain Model).

El expediente completo del cliente. Regla de diseño vinculante (Anexo A):
"Case Engine nunca contiene lógica. Solo estado y consistencia del caso."
MigrationCase no calcula nada -- Decision Engine, Policy Engine y Workflow
operan sobre él y le devuelven un resultado que aquí solo se registra.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import List  # noqa: UP035 -- ver nota junto a family_members

from sqlmodel import Field, Relationship, SQLModel


class CaseStatus(str, Enum):
    """Value object CaseStatus (Anexo A)."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class MigrationCase(SQLModel, table=True):
    """Aggregate Root. Frontera transaccional (Anexo D, Persistence
    Strategy) -- ninguna transacción cruza este aggregate y otro."""

    __tablename__ = "migration_cases"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, unique=True)

    status: CaseStatus = Field(default=CaseStatus.DRAFT, index=True)

    # Value object Objective (Anexo A) aplanado en columnas -- sin tabla propia,
    # es parte del estado del aggregate, no una entidad independiente.
    objective_country: str | None = Field(default=None)
    objective_visa_type: str | None = Field(default=None)

    # NextStepRef (Anexo A): referencia de solo lectura poblada por Workflow.
    # Sprint 1 todavía no tiene Workflow -- queda null hasta ese bloque.
    next_step_ref: str | None = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # typing.List, no el builtin `list` -- SQLAlchemy 2.0 no resuelve el
    # genérico builtin dentro de Relationship() (InvalidRequestError en
    # tiempo de arranque). No dejar que ruff "modernice" esto (UP035).
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
