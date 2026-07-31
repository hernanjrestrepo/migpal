"""
Recommendation — application: orquestador (Sprint 3, Hito 3).

Compone Decision Engine (vía Policy Engine, que ya calcula el fit) + Policy
Engine + Knowledge (catálogo) en una Recommendation completa. 100%
determinístico -- NO llama al AI Adapter ni a ningún LLM (eso es Sprint 4,
`ai_recommendation.py`, y solo toca `narrative_summary`). Mismo Assessment +
mismas versiones -> misma Recommendation (invariante 7, §2 del diseño).

Entradas: Assessment ya persistido (no texto crudo -- ver nota en
`decision_engine.infrastructure.scoring.matched_signals_from_findings`) y el
MigrationCase del que depende (para `objective_country`, entrada legítima
según §3 del diseño). `recommendation` puede depender de `decision_engine`
(vía Policy Engine) y de `policy_engine` -- dirección de dependencia
declarada en el diseño ("Ubicación del bounded context").
"""

from __future__ import annotations

from core.case_engine.domain.aggregates import MigrationCase
from core.decision_engine.domain.aggregates import Assessment
from core.decision_engine.infrastructure.scoring import matched_signals_from_findings
from core.policy_engine.rules import evaluate_candidate_routes
from core.recommendation.domain.aggregates import Recommendation
from core.recommendation.domain.rules import build_recommendation, issue
from core.recommendation.domain.value_objects import NextStep

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

    next_step = NextStep(
        title="Perfilamiento completo",
        description=(
            f"Preparar documentación para {primary.route.visa_type} ({primary.route.country}): "
            + ", ".join(primary.required_documents)
        ),
    )

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
