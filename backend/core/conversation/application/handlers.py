"""
Conversation — application: handlers.

`handle_request_assessment` es la orquestación real del Hito 2: Conversation
(Capa 2, Handbook Module Dependency Rules) puede depender de Decision Engine
(Capa 1) -- la dirección correcta. Decision Engine nunca llama de vuelta a
Conversation ni al AI Adapter.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from core.conversation.application.commands import (
    ChatConEspecialistaCommand,
    RequestAssessmentCommand,
    SendMessageCommand,
)
from core.conversation.domain.personas import personas_for_context, system_prompt_for
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


@dataclass(frozen=True)
class SpecialistReply:
    persona_id: str
    persona_name: str
    text: str


async def handle_chat_con_especialista(
    cmd: ChatConEspecialistaCommand, ai_adapter: AIAdapter
) -> list[SpecialistReply]:
    """Sprint 9, Hito 5. Un contexto normal resuelve a un solo especialista;
    "negocio" resuelve a los 4 del Board de ADAN -- una junta real, cada
    uno responde por su cuenta (en paralelo, no uno simulando a los otros).
    `personas_for_context` nunca devuelve una lista vacía (cae en Angela),
    así que esta función siempre devuelve al menos una respuesta."""

    personas = personas_for_context(cmd.context)

    async def _reply_for(persona) -> SpecialistReply:
        text = await ai_adapter.chat_as_persona(system_prompt=system_prompt_for(persona), message=cmd.message)
        return SpecialistReply(persona_id=persona.persona_id, persona_name=persona.name, text=text)

    return list(await asyncio.gather(*(_reply_for(p) for p in personas)))
