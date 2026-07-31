"""
Recommendation — infrastructure: AI Adapter (Sprint 4, Hito 3).

Adapter propio, no el de Conversation (`core.conversation.infrastructure.ai_adapter.AIAdapter`)
-- decisión explícita del diseño (docs/RECOMMENDATION_DESIGN.md §9: "AIAdapter,
o un adapter propio si ai_recommendation.py no debe pasar por Conversation").
Se eligió adapter propio para no crear una dependencia cruzada entre bounded
contexts hermanos (`recommendation` -> `conversation`) solo para llegar al
LLM -- cada bounded context que toca el LLM tiene su propio punto único de
contacto con `app.services.*`, no uno compartido entre bounded contexts.

Única clase de `core/recommendation/` que importa `app.services.*`. La
generación de `primary_evaluation`/`rationale`/`confidence` NUNCA pasa por
acá -- eso ya está decidido antes de llegar a este adapter (ver
`recommendation/application/orchestrator.py`).
"""

from __future__ import annotations

from app.services.ai_recommendation import generate_narrative_summary
from core.recommendation.domain.value_objects import RouteEvaluation


class RecommendationAIAdapter:
    """Puerto único hacia la redacción narrativa de una Recommendation."""

    async def narrate(self, *, primary: RouteEvaluation, rationale: list[str]) -> str:
        summary = (
            f"Ruta recomendada: {primary.route.visa_type} ({primary.route.country}), "
            f"ajuste {primary.route.fit_score:.0f}/100.\n"
            f"Por qué: {'; '.join(rationale)}.\n"
            f"Fortalezas: {'; '.join(primary.strengths) or 'sin datos'}.\n"
            f"Riesgos: {'; '.join(primary.risks) or 'sin datos'}."
        )
        return await generate_narrative_summary(summary)
