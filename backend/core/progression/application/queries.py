"""
Progression — application: consultas (Sprint 7, Hito 5).

Sin infraestructura propia -- Progression no tiene tabla ni aggregate:
todo se deriva en el momento de leer, del event log compartido
(`core/shared/event_log.py`) y, para "trámites 100%", de una consulta de
estado directa a Settlement (dependencia de aplicación, no de dominio --
mismo criterio que `execution_plan` dependiendo de `recommendation` para
resolver el país en Settlement, ver `core/settlement/application/handlers.py`).

El event log no indexa por `case_id`/`user_id` (el payload es JSON de texto
libre, ver docstring de `core/shared/event_log.py`) -- se filtra en Python
después de traer los eventos por nombre. Aceptable para el volumen de un
piloto; si esto escala, el primer cambio sería tipar el payload."""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlmodel import Session

from core.progression.domain.rules import SETTLEMENT_COMPLETE_MILESTONE_KEY, ProgressResult, compute_progress
from core.settlement.application.queries import ConsultarMiChecklistQuery, handle_consultar_mi_checklist
from core.settlement.infrastructure.repository import SettlementRepository
from core.shared.event_log import get_event_log

CASE_SCOPED_EVENT_KEYS = {
    "AssessmentCompleted",
    "RecommendationAccepted",
    "BudgetEstimateCalculated",
    "SettlementChecklistCreated",
    "GeographicSelectionUpdated",
    "FamilySurveyResponseSubmitted",
    "ExecutionPlanCreated",
    "ExecutionPlanCompleted",
}

USER_SCOPED_EVENT_KEYS = {
    "CommunityPostPublished",
    "MarketplaceTransactionCompleted",
}


@dataclass(frozen=True)
class ConsultarProgresoQuery:
    case_id: int
    user_id: int


def _any_event_matches(session: Session, *, event_name: str, field: str, value: int) -> bool:
    for event in get_event_log(session, name=event_name, limit=1000):
        try:
            payload = json.loads(event.payload)
        except (json.JSONDecodeError, TypeError):
            continue
        if payload.get(field) == value:
            return True
    return False


def handle_consultar_progreso(query: ConsultarProgresoQuery, session: Session) -> ProgressResult:
    achieved: set[str] = set()

    for event_name in CASE_SCOPED_EVENT_KEYS:
        if _any_event_matches(session, event_name=event_name, field="case_id", value=query.case_id):
            achieved.add(event_name)

    for event_name in USER_SCOPED_EVENT_KEYS:
        if _any_event_matches(session, event_name=event_name, field="user_id", value=query.user_id):
            achieved.add(event_name)

    checklist_view = handle_consultar_mi_checklist(
        ConsultarMiChecklistQuery(case_id=query.case_id), SettlementRepository(session)
    )
    settlement_complete = (
        checklist_view is not None
        and checklist_view.total_count > 0
        and checklist_view.done_count == checklist_view.total_count
    )
    if settlement_complete:
        achieved.add(SETTLEMENT_COMPLETE_MILESTONE_KEY)

    return compute_progress(achieved_keys=achieved)
