"""
Recommendation — application: handlers (Sprint 5 + estabilización, Hito 3).

Único lugar (además de `orchestrator.py`, que estos handlers envuelven)
donde vive orquestación de Recommendation. `adapters/api.py` no debe
importar `domain.rules` ni tomar ninguna decisión de negocio -- solo llama
a estos handlers y traduce las excepciones resultantes a HTTP.
"""

from __future__ import annotations

from core.case_engine.domain.aggregates import MigrationCase
from core.decision_engine.domain.aggregates import Assessment
from core.recommendation.application.commands import (
    AcceptRecommendationCommand,
    DiscardRecommendationCommand,
    SelectRouteCommand,
)
from core.recommendation.application.orchestrator import attach_narrative, generate_recommendation
from core.recommendation.domain.aggregates import Recommendation
from core.recommendation.domain.rules import accept, discard, select_route
from core.recommendation.infrastructure.ai_adapter import RecommendationAIAdapter
from core.recommendation.infrastructure.repository import RecommendationRepository
from core.shared.exceptions import RecommendationNotFound


async def handle_request_recommendation(
    case: MigrationCase,
    assessment: Assessment,
    ai_adapter: RecommendationAIAdapter,
    repo: RecommendationRepository,
) -> Recommendation:
    recommendation = generate_recommendation(case=case, assessment=assessment)
    recommendation = await attach_narrative(recommendation, ai_adapter)
    return repo.save(recommendation)


def _get_owned_recommendation(recommendation_id: int, case_id: int, repo: RecommendationRepository) -> Recommendation:
    rec = repo.get_by_id(recommendation_id)
    if not rec or rec.case_id != case_id:
        raise RecommendationNotFound(f"Recommendation {recommendation_id} no encontrada para este caso.")
    return rec


def handle_accept_recommendation(
    cmd: AcceptRecommendationCommand, repo: RecommendationRepository
) -> Recommendation:
    """La invariante 6 (una sola ACCEPTED por caso) se valida dentro de
    `domain.rules.accept()` -- acá solo se obtiene `existing_accepted` del
    repositorio y se pasa. La decisión de negocio no está en este handler,
    está en el dominio."""
    rec = _get_owned_recommendation(cmd.recommendation_id, cmd.case_id, repo)
    existing_accepted = repo.get_accepted_for_case(cmd.case_id)
    accept(rec, existing_accepted=existing_accepted)
    return repo.save(rec)


def handle_discard_recommendation(
    cmd: DiscardRecommendationCommand, repo: RecommendationRepository
) -> Recommendation:
    rec = _get_owned_recommendation(cmd.recommendation_id, cmd.case_id, repo)
    discard(rec)
    return repo.save(rec)


async def handle_select_route(
    cmd: SelectRouteCommand,
    repo: RecommendationRepository,
    ai_adapter: RecommendationAIAdapter,
) -> Recommendation:
    """A-ADR-009 -- promueve una alternativa a `primary_evaluation`. Vuelve
    a redactar `narrative_summary` (mismo AI Adapter de `attach_narrative`,
    Sprint 4) para que describa la ruta que el usuario efectivamente
    eligió, no la que el sistema había sugerido -- si el LLM falla, cae al
    mismo fallback ya existente, la decisión ya quedó tomada de forma
    determinística antes de esta llamada."""
    rec = _get_owned_recommendation(cmd.recommendation_id, cmd.case_id, repo)
    select_route(rec, cmd.alternative_index)
    rec = await attach_narrative(rec, ai_adapter)
    return repo.save_route_selection(rec)
