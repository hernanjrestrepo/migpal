"""
Recommendation — adapters: superficie Web API (Sprint 5, Hito 3).

Generación Y lectura viven ambas acá -- a diferencia de Assessment (Hito 2),
donde la generación tuvo que vivir en Conversation porque Decision Engine no
podía depender del AI Adapter. `recommendation` es su propio bounded
context y sí puede depender del AI Adapter directamente (ver
docs/RECOMMENDATION_DESIGN.md §9 y "Ubicación del bounded context").
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
from core.recommendation.application.orchestrator import attach_narrative, generate_recommendation
from core.recommendation.domain.aggregates import Recommendation
from core.recommendation.domain.rules import (
    RecommendationInvariantError,
    RecommendationTransitionError,
    accept,
    discard,
)
from core.recommendation.infrastructure.ai_adapter import RecommendationAIAdapter
from core.recommendation.infrastructure.repository import RecommendationRepository
from core.shared.exceptions import CaseNotFound

router = APIRouter(prefix="/v1/recommendation", tags=["recommendation"])


class MigrationRouteRead(BaseModel):
    visa_type: str
    country: str
    fit_score: float


class RouteEvaluationRead(BaseModel):
    route: MigrationRouteRead
    strengths: list[str]
    risks: list[str]
    required_documents: list[str]


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


def _get_owned_recommendation_or_404(recommendation_id: int, case_id: int, repo: RecommendationRepository):
    rec = repo.get_by_id(recommendation_id)
    if not rec or rec.case_id != case_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation no encontrada.")
    return rec


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

    recommendation = generate_recommendation(case=case, assessment=assessment)
    recommendation = await attach_narrative(recommendation, RecommendationAIAdapter())

    recommendation_repo = RecommendationRepository(session)
    saved = recommendation_repo.save(recommendation)
    return _to_read(saved)


@router.get("", response_model=RecommendationRead)
def get_my_latest_recommendation(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)

    recommendation_repo = RecommendationRepository(session)
    rec = recommendation_repo.get_latest_for_case(case.id)
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
    rec = _get_owned_recommendation_or_404(recommendation_id, case.id, recommendation_repo)

    already_accepted = recommendation_repo.get_accepted_for_case(case.id)
    if already_accepted and already_accepted.id != rec.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una Recommendation ACCEPTED para este caso (invariante 6).",
        )

    try:
        accept(rec)
    except (RecommendationTransitionError, RecommendationInvariantError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    saved = recommendation_repo.save(rec)
    return _to_read(saved)


@router.post("/{recommendation_id}/discard", response_model=RecommendationRead)
def discard_recommendation(
    recommendation_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    recommendation_repo = RecommendationRepository(session)
    rec = _get_owned_recommendation_or_404(recommendation_id, case.id, recommendation_repo)

    try:
        discard(rec)
    except (RecommendationTransitionError, RecommendationInvariantError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    saved = recommendation_repo.save(rec)
    return _to_read(saved)
