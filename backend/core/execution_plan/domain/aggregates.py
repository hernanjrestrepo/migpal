"""
Execution Plan — domain: Aggregate Root ExecutionPlan + entidad PlanStep
(Sprint 1, Hito 4).

Ver docs/HITO_4_DESIGN.md §2-§3. `PlanStep` es una ENTIDAD, no un Value
Object (a diferencia de MigrationRoute/RouteEvaluation/NextStep en
Recommendation) -- se referencia individualmente vía `depends_on` y se
actualiza uno por uno, por eso se persiste como fila propia (tabla
`plan_steps`), no como JSON embebido. Mismo patrón que
MigrationCase/CaseFamilyMember (core/case_engine/domain/aggregates.py):
`typing.List` (no el builtin `list`) en la `Relationship`, y sin
`from __future__ import annotations` en este archivo -- con ese import
activo, SQLAlchemy 2.0 no logra resolver `Relationship(List["PlanStep"])`
en tiempo de arranque (`InvalidRequestError`, pide `Mapped[List[...]]`).
Se confirmó reproduciendo el error y quitando el import -- no es una
suposición copiada del comentario de case_engine.

Sprint 1 -- solo estado y persistencia. Ninguna función de este módulo
valida invariantes (eso es `application/`, Sprint 2, según el orden de
sprints aprobado para Hito 4) -- ver docs/HITO_4_DESIGN.md §5, que las
enumera, pero no las implementa hasta Sprint 2.
"""

from datetime import UTC, datetime
from typing import List  # noqa: UP035 -- ver nota junto a steps

from sqlmodel import JSON as SQLModelJSON
from sqlmodel import Column, Field, Relationship, SQLModel

from core.execution_plan.domain.value_objects import ExecutionPlanStatus, PlanStepStatus


class ExecutionPlan(SQLModel, table=True):
    """Aggregate Root. Nace de una Recommendation ACCEPTED, vive bajo un
    MigrationCase -- ninguno de los dos conoce a ExecutionPlan (mismo
    principio ya aplicado a Assessment/Recommendation: el caso es operado
    sobre, no posee)."""

    __tablename__ = "execution_plans"

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="migration_cases.id", index=True)
    recommendation_id: int = Field(foreign_key="recommendations.id", index=True)

    status: ExecutionPlanStatus = Field(default=ExecutionPlanStatus.ACTIVE, index=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = Field(default=None)

    steps: List["PlanStep"] = Relationship(back_populates="plan")  # noqa: UP006, UP035


class PlanStep(SQLModel, table=True):
    """Entidad dentro del aggregate ExecutionPlan (ver docstring del
    módulo). `depends_on` es JSON (lista de ids de otros PlanStep del mismo
    plan) -- no relacional, porque no se consulta individualmente por
    dependencia, solo se lee junto con el paso (docs/HITO_4_DESIGN.md §11)."""

    __tablename__ = "plan_steps"

    id: int | None = Field(default=None, primary_key=True)
    execution_plan_id: int = Field(foreign_key="execution_plans.id", index=True)

    title: str
    description: str
    sequence: int

    depends_on: list[int] = Field(default_factory=list, sa_column=Column(SQLModelJSON))

    status: PlanStepStatus = Field(default=PlanStepStatus.PENDING, index=True)
    completed_at: datetime | None = Field(default=None)

    plan: ExecutionPlan | None = Relationship(back_populates="steps")
