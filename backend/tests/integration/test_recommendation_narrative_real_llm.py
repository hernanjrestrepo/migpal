"""
Recommendation — narrative_summary contra Ollama real (Sprint 4, Hito 3).

A diferencia de test_recommendation_ai_adapter.py (stub, sin red), esto
llama al Ollama real -- mismo espíritu que
tests/contracts/test_conversation_assessment_contract.py: si el AI Adapter
de Recommendation se rompe, debe fallar acá, no en producción.
"""

import pytest

from core.recommendation.application.orchestrator import attach_narrative, generate_recommendation
from core.recommendation.infrastructure.ai_adapter import RecommendationAIAdapter
from tests.unit.test_recommendation_orchestrator import _assessment, _case


@pytest.mark.asyncio
async def test_attach_narrative_against_real_ollama_produces_non_fallback_text():
    rec = generate_recommendation(case=_case(), assessment=_assessment())

    result = await attach_narrative(rec, RecommendationAIAdapter())

    assert result.narrative_summary
    assert len(result.narrative_summary) > 10
    # No verificamos contenido exacto (no determinístico por diseño) -- solo
    # que no cayó al fallback, es decir, que Ollama respondió de verdad.
    assert result.narrative_summary != "No fue posible generar la explicación narrativa en este momento."
