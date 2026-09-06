"""
Conversation — adapters: superficie Web API (Anexo C).

POST /v1/messages: chat con MigPAL.
POST /v1/assessment: orquesta AI Adapter (entender) + Decision Engine
(calcular) -- vive aquí, no en Decision Engine, porque solo Conversation
tiene permitido depender de ambos a la vez (Handbook, Module Dependency
Rules).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.auth import get_current_user
from app.db.session import get_session
from core.case_engine.application.queries import GetCaseForUserQuery, handle_get_case_for_user
from core.case_engine.infrastructure.repository import CaseRepository
from core.conversation.application.commands import (
    ChatConEspecialistaCommand,
    RequestAssessmentCommand,
    SendMessageCommand,
)
from core.conversation.application.handlers import (
    handle_chat_con_especialista,
    handle_request_assessment,
    handle_send_message,
)
from core.conversation.infrastructure.ai_adapter import AIAdapter
from core.decision_engine.infrastructure.repository import AssessmentRepository
from core.identity.domain.aggregates import User
from core.shared.exceptions import CaseNotFound

router = APIRouter(prefix="/v1", tags=["conversation"])


class MessageRequest(BaseModel):
    message: str


class MessageResponse(BaseModel):
    reply: str


class AssessmentRequest(BaseModel):
    profile_text: str


class AssessmentResponse(BaseModel):
    id: int
    case_id: int
    score: float
    confidence: float
    findings: list[str]
    recommendations: list[str]
    decision_engine_version: str
    policy_version: str
    knowledge_version: str
    ai_reflection: str


def _ai_adapter() -> AIAdapter:
    return AIAdapter()


@router.post("/messages", response_model=MessageResponse)
async def send_message(
    body: MessageRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    ai_adapter: AIAdapter = Depends(_ai_adapter),
):
    case_repo = CaseRepository(session)
    try:
        case = handle_get_case_for_user(GetCaseForUserQuery(user_id=current_user.id), case_repo)
    except CaseNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    reply = await handle_send_message(SendMessageCommand(case_id=case.id, message=body.message), ai_adapter)
    return MessageResponse(reply=reply)


@router.post("/assessment", response_model=AssessmentResponse)
async def request_assessment(
    body: AssessmentRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    ai_adapter: AIAdapter = Depends(_ai_adapter),
):
    case_repo = CaseRepository(session)
    try:
        case = handle_get_case_for_user(GetCaseForUserQuery(user_id=current_user.id), case_repo)
    except CaseNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    assessment_repo = AssessmentRepository(session)
    cmd = RequestAssessmentCommand(case_id=case.id, profile_text=body.profile_text)
    assessment, ai_reflection = await handle_request_assessment(cmd, ai_adapter, assessment_repo)

    return AssessmentResponse(
        id=assessment.id,
        case_id=assessment.case_id,
        score=assessment.score,
        confidence=assessment.confidence,
        findings=assessment.findings,
        recommendations=assessment.recommendations,
        decision_engine_version=assessment.decision_engine_version,
        policy_version=assessment.policy_version,
        knowledge_version=assessment.knowledge_version,
        ai_reflection=ai_reflection,
    )


class ChatConEspecialistaRequest(BaseModel):
    context: str
    message: str


class SpecialistReplyRead(BaseModel):
    persona_id: str
    persona_name: str
    text: str


class ChatConEspecialistaResponse(BaseModel):
    replies: list[SpecialistReplyRead]


@router.post("/conversation/chat", response_model=ChatConEspecialistaResponse)
async def chat_con_especialista(
    body: ChatConEspecialistaRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    ai_adapter: AIAdapter = Depends(_ai_adapter),
):
    case_repo = CaseRepository(session)
    try:
        case = handle_get_case_for_user(GetCaseForUserQuery(user_id=current_user.id), case_repo)
    except CaseNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    replies = await handle_chat_con_especialista(
        ChatConEspecialistaCommand(case_id=case.id, context=body.context, message=body.message), ai_adapter
    )
    return ChatConEspecialistaResponse(
        replies=[SpecialistReplyRead(persona_id=r.persona_id, persona_name=r.persona_name, text=r.text) for r in replies]
    )
