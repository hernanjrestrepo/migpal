"""
Recommendation — application: orquestador (Sprint 3 + Sprint 4, Hito 3).

`generate_recommendation()` (Sprint 3) compone Decision Engine (vía Policy
Engine, que ya calcula el fit) + Policy Engine + Knowledge (catálogo) en una
Recommendation completa. 100% determinístico -- NO llama al AI Adapter ni a
ningún LLM. Mismo Assessment + mismas versiones -> misma Recommendation
(invariante 7, §2 del diseño).

`attach_narrative()` (Sprint 4) es la única función de este módulo que toca
el LLM -- redacta `narrative_summary` sobre una Recommendation ya decidida,
sin modificar ningún campo determinístico. Separarlas en dos funciones deja
`generate_recommendation()` testeable sin red (ver
tests/unit/test_recommendation_orchestrator.py) y dice explícitamente en la
firma cuál de las dos partes del proceso es no-determinística.

Entradas: Assessment ya persistido (no texto crudo -- ver nota en
`decision_engine.infrastructure.scoring.matched_signals_from_findings`) y el
MigrationCase del que depende (para `objective_country`, entrada legítima
según §3 del diseño). `recommendation` puede depender de `decision_engine`
(vía Policy Engine), de `policy_engine` y de su propio AI Adapter --
dirección de dependencia declarada en el diseño ("Ubicación del bounded
context").
"""

from __future__ import annotations

from core.case_engine.domain.aggregates import MigrationCase
from core.decision_engine.domain.aggregates import Assessment
from core.decision_engine.infrastructure.scoring import matched_signals_from_findings
from core.policy_engine.rules import evaluate_candidate_routes
from core.recommendation.domain.aggregates import Recommendation
from core.recommendation.domain.rules import build_recommendation, issue, next_step_for_route
from core.recommendation.infrastructure.ai_adapter import RecommendationAIAdapter

MAX_ALTERNATIVE_ROUTES = 3
DECISION_ENGINE_VERSION = "1.0"
POLICY_VERSION = "1.0"
KNOWLEDGE_VERSION = "1.0"
RECOMMENDATION_VERSION = "1.0"


def generate_recommendation(*, case: MigrationCase, assessment: Assessment) -> Recommendation:
    """Genera y emite (ISSUED) una Recommendation completa a partir de un
    Assessment ya persistido. No la guarda -- eso es responsabilidad de
    quien orquesta con el repositorio (Sprint 5, adapter de API), para que
    esta función siga siendo pura y testeable sin sesión de DB."""

    matched_signals = matched_signals_from_findings(assessment.findings)
    evaluations = evaluate_candidate_routes(
        matched_signals=matched_signals, objective_country=case.objective_country
    )

    primary = evaluations[0]
    alternatives = evaluations[1 : 1 + MAX_ALTERNATIVE_ROUTES]

    # confidence nunca puede superar la del Assessment (invariante 3) --
    # tomar el mínimo lo garantiza por construcción, no por validación externa.
    confidence = min(assessment.confidence, round(primary.route.fit_score / 100.0, 2))

    rationale = [
        f"{finding} -- coincide con los requisitos de {primary.route.visa_type} ({primary.route.country})."
        for finding in assessment.findings
        if finding.startswith("Señal detectada:")
    ]
    if case.objective_country and case.objective_country.strip().lower() == primary.route.country.strip().lower():
        rationale.append(f"El destino declarado en tu caso ({case.objective_country}) coincide con esta ruta.")
    if not rationale:
        rationale = [f"Ruta con mejor ajuste disponible en el catálogo actual ({primary.route.visa_type})."]

    next_step = next_step_for_route(primary)

    recommendation = build_recommendation(
        case_id=case.id,
        assessment_id=assessment.id,
        assessment_confidence=assessment.confidence,
        primary_evaluation=primary,
        alternative_evaluations=alternatives,
        next_step=next_step,
        confidence=confidence,
        rationale=rationale,
        decision_engine_version=DECISION_ENGINE_VERSION,
        policy_version=POLICY_VERSION,
        knowledge_version=KNOWLEDGE_VERSION,
        recommendation_version=RECOMMENDATION_VERSION,
    )
    return issue(recommendation)


async def attach_narrative(
    recommendation: Recommendation, ai_adapter: RecommendationAIAdapter
) -> Recommendation:
    """Sprint 4: redacta `narrative_summary` sobre una Recommendation YA
    decidida (Sprint 3) -- no toca `primary_evaluation`, `rationale`,
    `confidence` ni ningún campo determinístico. Si el LLM falla,
    `generate_narrative_summary` devuelve su propio fallback -- la
    Recommendation sigue siendo válida y accionable de cualquier forma."""

    primary = recommendation.primary_route_evaluation()
    recommendation.narrative_summary = await ai_adapter.narrate(
        primary=primary, rationale=recommendation.rationale
    )
    return recommendation
