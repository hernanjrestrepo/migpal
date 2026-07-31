"""
Recommendation — AI Adapter y attach_narrative (Sprint 4, Hito 3).

Sin red: `generate_narrative_summary` (app.services.ai_recommendation) se
reemplaza por un stub. Prueba el contrato -- que attach_narrative() solo
toca narrative_summary, y que un fallo del LLM no invalida la
Recommendation -- no la latencia real de Ollama (eso vive en
tests/integration/test_recommendation_narrative_real_llm.py).
"""

import pytest

from core.recommendation.application.orchestrator import attach_narrative, generate_recommendation
from core.recommendation.infrastructure.ai_adapter import RecommendationAIAdapter
from tests.unit.test_recommendation_orchestrator import RICH_FINDINGS, _assessment, _case


class _StubAIAdapter:
    def __init__(self, response: str):
        self._response = response
        self.called_with = None

    async def narrate(self, *, primary, rationale):
        self.called_with = (primary, rationale)
        return self._response


@pytest.mark.asyncio
async def test_attach_narrative_sets_only_narrative_summary():
    rec = generate_recommendation(case=_case(), assessment=_assessment())
    before = (
        rec.primary_evaluation,
        rec.alternative_evaluations,
        rec.rationale,
        rec.confidence,
        rec.next_step,
        rec.status,
    )

    stub = _StubAIAdapter("Esta es tu mejor ruta explicada en lenguaje natural.")
    result = await attach_narrative(rec, stub)

    after = (
        result.primary_evaluation,
        result.alternative_evaluations,
        result.rationale,
        result.confidence,
        result.next_step,
        result.status,
    )
    assert before == after  # nada determinístico cambió
    assert result.narrative_summary == "Esta es tu mejor ruta explicada en lenguaje natural."


@pytest.mark.asyncio
async def test_attach_narrative_survives_llm_failure_via_adapter_fallback():
    """El adapter real (RecommendationAIAdapter -> generate_narrative_summary)
    ya devuelve FALLBACK_MESSAGE ante cualquier excepción/red caída -- acá se
    simula ese contrato con un stub que "falla" devolviendo el fallback,
    igual que haría el servicio real."""
    rec = generate_recommendation(case=_case(), assessment=_assessment())

    stub = _StubAIAdapter("No fue posible generar la explicación narrativa en este momento.")
    result = await attach_narrative(rec, stub)

    assert result.status == "ISSUED" or result.status.value == "ISSUED"
    assert result.primary_evaluation is not None
    assert result.rationale != []
    assert "No fue posible" in result.narrative_summary


def test_recommendation_ai_adapter_is_the_only_importer_of_ai_recommendation_in_this_context():
    """Espejo de la regla de A-ADR-006 para Conversation: dentro de
    core/recommendation, solo infrastructure/ai_adapter.py puede importar
    app.services.ai_recommendation."""
    import ast
    from pathlib import Path

    recommendation_dir = Path(__file__).resolve().parents[2] / "core" / "recommendation"
    offenders = []
    for path in recommendation_dir.rglob("*.py"):
        if path.name == "ai_adapter.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "ai_recommendation" in node.module:
                offenders.append(str(path))

    assert offenders == []
