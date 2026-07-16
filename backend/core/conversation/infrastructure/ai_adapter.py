"""
Conversation — infrastructure: AI Adapter.

Regla del Hito 2: "Conversation NO puede depender de ai_brain.py.
Debe depender únicamente del AI Adapter." Este es ese límite -- la ÚNICA
clase de todo `core/` que importa `app.services.ai_brain`. Si mañana
`ai_brain.py` desaparece y se reemplaza por el AI Orchestrator completo
(Tool Registry, RAG, memoria -- vNext 1.2), solo este archivo cambia.
Conversation, Decision Engine y todo lo demás no se enteran.

No se modifica ai_brain.py salvo lo estrictamente necesario (regla del
Hito 2) -- este adaptador se ajusta a la firma que ya existe
(`process_message(message, user_data, conversation_history)`), no al revés.
"""

from __future__ import annotations

from app.services.ai_brain import process_message


class AIAdapter:
    """Puerto único hacia la capacidad de IA conversacional."""

    async def chat(self, message: str, conversation_history: list[str] | None = None) -> str:
        """Respuesta conversacional -- lo que el usuario ve en el chat."""
        return await process_message(message, user_data={}, conversation_history=conversation_history or [])

    async def understand(self, profile_text: str) -> str:
        """
        Extrae/refleja lo que MigPAL entendió del perfil del usuario.

        Reutiliza el mismo `process_message` (no hay un endpoint de
        extracción separado en ai_brain.py todavía) -- el resultado se usa
        como `findings` cualitativo del Assessment. El SCORE no sale de
        aquí: Decision Engine lo calcula de forma determinística sobre el
        texto crudo, nunca sobre lo que el LLM "opine" (Constitución, regla 2).
        """
        return await process_message(
            f"Resume en 3-4 líneas qué entendiste de mi perfil migratorio a partir de esto: {profile_text}",
            user_data={},
            conversation_history=[],
        )
