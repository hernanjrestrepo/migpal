"""
Settlement — application: handlers (Sprint 2, Hito 5).

Mismo criterio que execution_plan/application/handlers.py: si no hay
Recommendation ACCEPTED, `RecommendationNotFound` -- no es una invariante
de Settlement (eso vive en domain/rules.py::start_checklist), es una regla
de acceso/existencia. Mapea a 404 en adapters/api.py, no a 409.
"""

from __future__ import annotations

from core.recommendation.infrastructure.repository import RecommendationRepository
from core.settlement.application.commands import ActualizarItemCommand, GenerarChecklistCommand
from core.settlement.domain.aggregates import SettlementChecklist
from core.settlement.domain.rules import build_checklist_items, start_checklist, update_item_status
from core.settlement.infrastructure.repository import SettlementRepository
from core.shared.exceptions import RecommendationNotFound, SettlementNotFound


def handle_generar_checklist(
    cmd: GenerarChecklistCommand,
    settlement_repo: SettlementRepository,
    recommendation_repo: RecommendationRepository,
) -> SettlementChecklist:
    recommendation = recommendation_repo.get_accepted_for_case(cmd.case_id)
    if recommendation is None:
        raise RecommendationNotFound(f"No hay una Recommendation ACCEPTED para el caso {cmd.case_id}.")

    country = recommendation.primary_route_evaluation().route.country
    existing = settlement_repo.get_for_case(cmd.case_id)
    checklist = start_checklist(case_id=cmd.case_id, country=country, existing=existing)
    checklist.items = build_checklist_items(country)
    return settlement_repo.add(checklist)


def _get_owned_checklist(checklist_id: int, case_id: int, repo: SettlementRepository) -> SettlementChecklist:
    checklist = repo.get_by_id(checklist_id)
    if not checklist or checklist.case_id != case_id:
        raise SettlementNotFound(f"SettlementChecklist {checklist_id} no encontrado para este caso.")
    return checklist


def handle_actualizar_item(cmd: ActualizarItemCommand, repo: SettlementRepository) -> SettlementChecklist:
    checklist = _get_owned_checklist(cmd.checklist_id, cmd.case_id, repo)
    checklist = update_item_status(checklist, cmd.item_id, cmd.status)
    return repo.save(checklist, updated_item_id=cmd.item_id)
