"""
Recommendation — domain: Aggregate Root (Sprint 1, Hito 3).

Ver docs/RECOMMENDATION_DESIGN.md §2 y §6. Igual convención que Assessment
(core/decision_engine/domain/aggregates.py) y MigrationCase
(core/case_engine/domain/aggregates.py): la clase de dominio y el mapeo ORM
son la misma clase (compromiso deliberado del proyecto -- ver nota en
case_engine/domain/aggregates.py).

`primary_evaluation`/`alternative_evaluations`/`rationale`/`next_step` se
guardan como JSON crudo (dict/list), no como los Value Objects tipados
(`RouteEvaluation`, `NextStep`) -- mismo patrón que `Assessment.findings`
(lista de strings en columna JSON). Los helpers `*_evaluation()`/`set_*()`
convierten entre el JSON persistido y los VOs tipados; son estructurales
(serialización), no lógica de negocio -- la lógica de negocio (invariantes,
transiciones) vive en `domain/rules.py`, no en esta clase (regla de Case
Engine/Anexo A: "el aggregate nunca contiene lógica, solo estado").

Nota Sprint 1 (dominio, sin persistencia real todavía): esta clase NO está
registrada en `app/db/base.py` ni tiene migración Alembic -- eso es Sprint 2.
Se puede instanciar e importar como objeto Python puro sin tocar la base de
datos.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import JSON as SQLModelJSON
from sqlmodel import Column, Field, SQLModel

from core.recommendation.domain.value_objects import NextStep, RecommendationStatus, RouteEvaluation


class Recommendation(SQLModel, table=True):
    """Aggregate Root. Vinculado a un MigrationCase y a un Assessment,
    nunca al revés (mismo principio que Assessment sobre MigrationCase)."""

    __tablename__ = "recommendations"

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="migration_cases.id", index=True)
    assessment_id: int = Field(foreign_key="assessments.id", index=True)

    status: RecommendationStatus = Field(default=RecommendationStatus.DRAFT, index=True)

    primary_evaluation: dict = Field(sa_column=Column(SQLModelJSON))
    alternative_evaluations: list[dict] = Field(default_factory=list, sa_column=Column(SQLModelJSON))

    confidence: float

    rationale: list[str] = Field(default_factory=list, sa_column=Column(SQLModelJSON))
    narrative_summary: str = Field(default="")

    next_step: dict = Field(sa_column=Column(SQLModelJSON))

    # Trazabilidad -- ninguna Recommendation nace sin sus cuatro versiones (§7).
    decision_engine_version: str = Field(default="1.0")
    policy_version: str = Field(default="1.0")
    knowledge_version: str = Field(default="1.0")
    recommendation_version: str = Field(default="1.0")

    version: int = Field(default=1)  # regeneraciones del mismo caso, igual que Assessment.version
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    decided_at: datetime | None = Field(default=None)

    # -- Helpers estructurales (serialización VO <-> JSON), no lógica de negocio. --

    def primary_route_evaluation(self) -> RouteEvaluation:
        return RouteEvaluation.model_validate(self.primary_evaluation)

    def alternative_route_evaluations(self) -> list[RouteEvaluation]:
        return [RouteEvaluation.model_validate(item) for item in self.alternative_evaluations]

    def next_step_detail(self) -> NextStep:
        return NextStep.model_validate(self.next_step)
