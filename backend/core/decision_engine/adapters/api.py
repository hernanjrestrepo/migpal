"""
Decision Engine — adapters: superficie de solo lectura (Anexo C).

GET /v1/assessment -- lectura pura del último Assessment del caso. La
generación (que necesita AI Adapter) vive en el adaptador de Conversation,
que es quien puede depender de Decision Engine (no al revés).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.auth import get_current_user
from app.db.session import get_session
from core.case_engine.application.queries import GetCaseForUserQuery, handle_get_case_for_user
from core.case_engine.infrastructure.repository import CaseRepository
from core.decision_engine.application.queries import GetLatestAssessmentQuery, handle_get_latest_assessment
from core.decision_engine.infrastructure.repository import AssessmentRepository
from core.identity.domain.aggregates import User
from core.shared.exceptions import CaseNotFound

router = APIRouter(prefix="/v1/assessment", tags=["decision-engine"])


class AssessmentRead(BaseModel):
    id: int
    case_id: int
    score: float
    confidence: float
    findings: list[str]
    recommendations: list[str]
    decision_engine_version: str
    policy_version: str
    knowledge_version: str
    version: int


@router.get("", response_model=AssessmentRead)
def get_my_latest_assessment(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case_repo = CaseRepository(session)
    try:
        case = handle_get_case_for_user(GetCaseForUserQuery(user_id=current_user.id), case_repo)
    except CaseNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    assessment_repo = AssessmentRepository(session)
    assessment = handle_get_latest_assessment(GetLatestAssessmentQuery(case_id=case.id), assessment_repo)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todavía no hay Assessment para tu caso."
        )

    return AssessmentRead(
        id=assessment.id,
        case_id=assessment.case_id,
        score=assessment.score,
        confidence=assessment.confidence,
        findings=assessment.findings,
        recommendations=assessment.recommendations,
        decision_engine_version=assessment.decision_engine_version,
        policy_version=assessment.policy_version,
        knowledge_version=assessment.knowledge_version,
        version=assessment.version,
    )
