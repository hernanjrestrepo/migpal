"""Family Planning — application: consultas (Sprint 4, Hito 5)."""

from __future__ import annotations

from dataclasses import dataclass

from core.family_planning.infrastructure.repository import (
    FamilySurveyRepository,
    GeographicSelectionRepository,
)


@dataclass(frozen=True)
class ConsultarPlanificacionQuery:
    case_id: int
    total_family_members: int
    """Cuántos CaseFamilyMember tiene el caso -- lo aporta quien llama
    (adapters/api.py, que ya tiene el `MigrationCase` cargado con su
    relación `family_members`) para no acoplar esta consulta a
    case_engine.infrastructure."""


@dataclass(frozen=True)
class PlanificacionView:
    country: str | None
    state: str | None
    city: str | None
    neighborhood: str | None
    survey_completed_count: int
    survey_total_count: int


def handle_consultar_planificacion(
    query: ConsultarPlanificacionQuery,
    geo_repo: GeographicSelectionRepository,
    survey_repo: FamilySurveyRepository,
) -> PlanificacionView:
    selection = geo_repo.get_for_case(query.case_id)
    responses = survey_repo.list_for_case(query.case_id)

    return PlanificacionView(
        country=selection.country if selection else None,
        state=selection.state if selection else None,
        city=selection.city if selection else None,
        neighborhood=selection.neighborhood if selection else None,
        survey_completed_count=sum(1 for r in responses if r.completed),
        survey_total_count=query.total_family_members + 1,  # +1 = el titular del caso
    )
