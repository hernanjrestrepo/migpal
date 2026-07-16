"""
Conversation — application: handlers.

`handle_request_assessment` es la orquestación real del Hito 2: Conversation
(Capa 2, Handbook Module Dependency Rules) puede depender de Decision Engine
(Capa 1) -- la dirección correcta. Decision Engine nunca llama de vuelta a
Conversation ni al AI Adapter.
"""

from __future__ import annotations

from core.conversation.application.commands import RequestAssessmentCommand, SendMessageCommand
from core.conversation.infrastructure.ai_adapter import AIAdapter
from core.decision_engine.application.commands import GenerateAssessmentCommand
from core.decision_engine.application.handlers import handle_generate_assessment
from core.decision_engine.domain.aggregates import Assessment
from core.decision_engine.infrastructure.repository import AssessmentRepository


async def handle_send_message(cmd: SendMessageCommand, ai_adapter: AIAdapter) -> str:
    return await ai_adapter.chat(cmd.message)


async def handle_request_assessment(
    cmd: RequestAssessmentCommand,
    ai_adapter: AIAdapter,
    assessment_repo: AssessmentRepository,
) -> tuple[Assessment, str]:
    """Devuelve (Assessment persistido y determinístico, reflexión de MigPAL).

    La reflexión (AI Adapter) y el score (Decision Engine) se calculan por
    separado a propósito -- la reflexión es cualitativa y puede variar; el
    score nunca depende de ella (regla obligatoria 08)."""
    ai_reflection = await ai_adapter.understand(cmd.profile_text)

    decision_cmd = GenerateAssessmentCommand(case_id=cmd.case_id, profile_text=cmd.profile_text)
    assessment = handle_generate_assessment(decision_cmd, assessment_repo)

    return assessment, ai_reflection
