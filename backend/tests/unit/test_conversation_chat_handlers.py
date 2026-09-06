"""
Conversation — handle_chat_con_especialista (Sprint 9, Hito 5).

Adapter falso -- no llama a ningún proveedor de IA real, mismo criterio
que los tests de handlers del resto del repo (sin DB, sin red)."""

import pytest

from core.conversation.application.commands import ChatConEspecialistaCommand
from core.conversation.application.handlers import handle_chat_con_especialista


class _FakeAIAdapter:
    def __init__(self):
        self.calls: list[str] = []

    async def chat_as_persona(self, *, system_prompt: str, message: str) -> str:
        self.calls.append(system_prompt)
        return f"respuesta a: {message}"


@pytest.mark.asyncio
async def test_single_specialist_context_returns_one_reply():
    adapter = _FakeAIAdapter()
    replies = await handle_chat_con_especialista(
        ChatConEspecialistaCommand(case_id=5, context="rutas", message="¿por qué mi puntaje es bajo?"), adapter
    )
    assert len(replies) == 1
    assert replies[0].persona_id == "dany"
    assert replies[0].text == "respuesta a: ¿por qué mi puntaje es bajo?"
    assert len(adapter.calls) == 1


@pytest.mark.asyncio
async def test_negocio_context_convenes_the_full_board():
    adapter = _FakeAIAdapter()
    replies = await handle_chat_con_especialista(
        ChatConEspecialistaCommand(case_id=5, context="negocio", message="¿es viable mi idea?"), adapter
    )
    assert {r.persona_id for r in replies} == {"tommy", "gabby", "ivan", "marcus"}
    assert len(adapter.calls) == 4


@pytest.mark.asyncio
async def test_unknown_context_falls_back_to_angela():
    adapter = _FakeAIAdapter()
    replies = await handle_chat_con_especialista(
        ChatConEspecialistaCommand(case_id=5, context="no_existe", message="hola"), adapter
    )
    assert len(replies) == 1
    assert replies[0].persona_id == "angela"


@pytest.mark.asyncio
async def test_each_persona_gets_its_own_system_prompt():
    adapter = _FakeAIAdapter()
    await handle_chat_con_especialista(
        ChatConEspecialistaCommand(case_id=5, context="negocio", message="hola"), adapter
    )
    assert len(set(adapter.calls)) == 4  # 4 system prompts distintos, uno por especialista
