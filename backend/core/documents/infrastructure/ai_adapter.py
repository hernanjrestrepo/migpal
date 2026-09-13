"""
Documents — infrastructure: AI Adapter (post-Hito 5).

Único punto de este bounded context que importa `app.services.ai_documents`
-- mismo patrón que `core.recommendation.infrastructure.ai_adapter.RecommendationAIAdapter`
y el resto de los bounded contexts que tocan el LLM (A-ADR-006)."""

from __future__ import annotations

from app.services.ai_documents import generate_document_verdict


class DocumentAIAdapter:
    """Puerto único hacia el veredicto de IA sobre un documento."""

    async def review(self, *, document_type: str, extracted_text: str) -> dict:
        return await generate_document_verdict(document_type=document_type, extracted_text=extracted_text)
