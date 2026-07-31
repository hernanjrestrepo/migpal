"""
Conversation — infrastructure: AI Adapter.

Regla del Hito 2: "Conversation NO puede depender de ai_brain.py.
Debe depender únicamente del AI Adapter." Este es ese límite -- la ÚNICA
clase de todo `core/` que importa `app.services.*`. Si mañana `ai_brain.py`
o `ai_assessment.py` desaparecen y se reemplazan por el AI Orchestrator
completo (Tool Registry, RAG, memoria -- vNext 1.2), solo este archivo
cambia. Conversation, Decision Engine y todo lo demás no se enteran.

Desde A-ADR-006 (docs/adr/A-ADR-006-separar-casos-de-uso-llm.md), `chat()` y
`understand()` NO comparten el mismo servicio de `app.services`: son casos
de uso distintos (diálogo con estado vs. reflexión sin estado) y cada uno
tiene su propio contrato. No se modifica `ai_brain.py` salvo lo
estrictamente necesario -- este adaptador se ajusta a las firmas que ya
existen, no al revés.
"""

from __future__ import annotations

from app.services.ai_assessment import summarize_profile
from app.services.ai_brain import process_message


class AIAdapter:
    """Puerto único hacia la capacidad de IA conversacional y analítica."""

    async def chat(self, message: str, conversation_history: list[str] | None = None) -> str:
        """Respuesta conversacional -- lo que el usuario ve en el chat."""
        return await process_message(message, user_data={}, conversation_history=conversation_history or [])

    async def understand(self, profile_text: str) -> str:
        """
        Extrae/refleja lo que MigPAL entendió del perfil del usuario.

        Usa `ai_assessment.summarize_profile` (A-ADR-006), no
        `ai_brain.process_message` -- ese último es una máquina de estados
        de onboarding que ignora el contenido del mensaje en favor de la
        etapa que le pasás en `user_data`; no sirve para resumir un perfil
        ya escrito. El resultado se usa como `ai_reflection` cualitativa del
        Assessment. El SCORE no sale de aquí: Decision Engine lo calcula de
        forma determinística sobre el texto crudo, nunca sobre lo que el
        LLM "opine" (Constitución, regla 2).
        """
        return await summarize_profile(profile_text)
