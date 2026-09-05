"""
Recommendation — adapters: superficie Web API (Sprint 5 + estabilización, Hito 3).

Solo traduce HTTP <-> application. Ninguna decisión de negocio vive acá --
ni la generación (delegada a `application.handlers.handle_request_recommendation`,
que a su vez usa `orchestrator.py`), ni la invariante 6 de `accept`
(delegada a `domain.rules.accept`, vía `application.handlers.handle_accept_recommendation`).
Corrección de arquitectura post-revisión: la primera versión de este archivo
tenía la validación de invariante 6 acá mismo -- se movió (ver
`domain/rules.py`, nota en `accept()`).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.auth import get_current_user
from app.db.session import get_session
from core.case_engine.application.queries import GetCaseForUserQuery, handle_get_case_for_user
from core.case_engine.infrastructure.repository import CaseRepository
from core.decision_engine.infrastructure.repository import AssessmentRepository
from core.identity.domain.aggregates import User
from core.recommendation.application.commands import AcceptRecommendationCommand, DiscardRecommendationCommand
from core.recommendation.application.handlers import (
    handle_accept_recommendation,
    handle_discard_recommendation,
    handle_request_recommendation,
)
from core.recommendation.application.queries import (
    GetLatestRecommendationQuery,
    handle_get_latest_recommendation,
)
from core.recommendation.domain.aggregates import Recommendation
from core.recommendation.domain.rules import RecommendationInvariantError, RecommendationTransitionError
from core.recommendation.infrastructure.ai_adapter import RecommendationAIAdapter
from core.recommendation.infrastructure.repository import RecommendationRepository
from core.shared.exceptions import CaseNotFound, RecommendationNotFound

router = APIRouter(prefix="/v1/recommendation", tags=["recommendation"])


class MigrationRouteRead(BaseModel):
    visa_type: str
    country: str
    fit_score: float


class RouteSourceRead(BaseModel):
    """Procedencia del dato de la ruta (A-ADR-008). `verified_at` en `null`
    significa que no se pudo verificar contra la fuente oficial -- el
    frontend lo muestra distinto, no lo oculta."""

    name: str
    url: str
    verified_at: str | None = None


class RouteEvaluationRead(BaseModel):
    route: MigrationRouteRead
    strengths: list[str]
    risks: list[str]
    required_documents: list[str]
    source: RouteSourceRead | None = None


class NextStepRead(BaseModel):
    title: str
    description: str
    priority: str | None
    estimated_effort: str | None
    estimated_cost_usd: float | None
    blocking: bool
    depends_on: list[str]


class RecommendationRead(BaseModel):
    id: int
    case_id: int
    assessment_id: int
    status: str
    primary_evaluation: RouteEvaluationRead
    alternative_evaluations: list[RouteEvaluationRead]
    confidence: float
    rationale: list[str]
    narrative_summary: str
    next_step: NextStepRead
    decision_engine_version: str
    policy_version: str
    knowledge_version: str
    recommendation_version: str
    version: int


def _to_read(rec: Recommendation) -> RecommendationRead:
    return RecommendationRead(
        id=rec.id,
        case_id=rec.case_id,
        assessment_id=rec.assessment_id,
        status=rec.status.value,
        primary_evaluation=rec.primary_evaluation,
        alternative_evaluations=rec.alternative_evaluations,
        confidence=rec.confidence,
        rationale=rec.rationale,
        narrative_summary=rec.narrative_summary,
        next_step=rec.next_step,
        decision_engine_version=rec.decision_engine_version,
        policy_version=rec.policy_version,
        knowledge_version=rec.knowledge_version,
        recommendation_version=rec.recommendation_version,
        version=rec.version,
    )


def _get_case_or_404(current_user: User, session: Session):
    case_repo = CaseRepository(session)
    try:
        return handle_get_case_for_user(GetCaseForUserQuery(user_id=current_user.id), case_repo)
    except CaseNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=RecommendationRead)
async def request_recommendation(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)

    assessment_repo = AssessmentRepository(session)
    assessment = assessment_repo.get_latest_for_case(case.id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todavía no hay Assessment para tu caso -- generá uno primero (invariante 1).",
        )

    recommendation_repo = RecommendationRepository(session)
    saved = await handle_request_recommendation(case, assessment, RecommendationAIAdapter(), recommendation_repo)
    return _to_read(saved)


@router.get("", response_model=RecommendationRead)
def get_my_latest_recommendation(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)

    recommendation_repo = RecommendationRepository(session)
    rec = handle_get_latest_recommendation(GetLatestRecommendationQuery(case_id=case.id), recommendation_repo)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todavía no hay Recommendation para tu caso.")
    return _to_read(rec)


@router.post("/{recommendation_id}/accept", response_model=RecommendationRead)
def accept_recommendation(
    recommendation_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    recommendation_repo = RecommendationRepository(session)

    try:
        saved = handle_accept_recommendation(
            AcceptRecommendationCommand(recommendation_id=recommendation_id, case_id=case.id), recommendation_repo
        )
    except RecommendationNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (RecommendationTransitionError, RecommendationInvariantError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_read(saved)


@router.post("/{recommendation_id}/discard", response_model=RecommendationRead)
def discard_recommendation(
    recommendation_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    recommendation_repo = RecommendationRepository(session)

    try:
        saved = handle_discard_recommendation(
            DiscardRecommendationCommand(recommendation_id=recommendation_id, case_id=case.id), recommendation_repo
        )
    except RecommendationNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (RecommendationTransitionError, RecommendationInvariantError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_read(saved)
