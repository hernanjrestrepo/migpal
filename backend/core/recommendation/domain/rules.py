"""
Recommendation — domain: invariantes y transiciones de estado (Sprint 1, Hito 3).

Funciones puras, sin efectos secundarios y sin acceso a base de datos --
mismo espíritu que `decision_engine/infrastructure/scoring.py` (regla
obligatoria 08: reproducibilidad). Case Engine/Anexo A: el aggregate no
contiene lógica, así que las reglas viven acá, no en `aggregates.py`.

Invariante 6 (§2 -- "solo una Recommendation ACCEPTED por caso a la vez") NO
se valida en este módulo: requiere consultar el repositorio para saber si ya
existe una Recommendation ACCEPTED de ese caso, y el repositorio (Sprint 2)
todavía no existe. Queda documentada acá para que la orquestación de
Sprint 3 la aplique antes de llamar a `accept()`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from core.recommendation.domain.aggregates import Recommendation
from core.recommendation.domain.value_objects import NextStep, RecommendationStatus, RouteEvaluation


class RecommendationInvariantError(ValueError):
    """Se violó una invariante del aggregate Recommendation."""


class RecommendationTransitionError(ValueError):
    """Transición de estado no permitida para el status actual."""


def build_recommendation(
    *,
    case_id: int,
    assessment_id: int,
    assessment_confidence: float,
    primary_evaluation: RouteEvaluation,
    next_step: NextStep,
    confidence: float,
    rationale: list[str],
    alternative_evaluations: list[RouteEvaluation] | None = None,
    narrative_summary: str = "",
    decision_engine_version: str = "1.0",
    policy_version: str = "1.0",
    knowledge_version: str = "1.0",
    recommendation_version: str = "1.0",
    version: int = 1,
) -> Recommendation:
    """Único punto de construcción de una Recommendation válida -- aplica las
    invariantes 1-5 de §2 del diseño. Nace siempre en estado DRAFT; `issue()`
    la hace visible (invariante 5: rationale obligatorio a partir de ahí)."""

    if not case_id:
        raise RecommendationInvariantError("Recommendation requiere case_id (invariante 1 extendida).")
    if not assessment_id:
        raise RecommendationInvariantError(
            "Recommendation no puede existir sin un Assessment que la origine (invariante 1)."
        )
    if primary_evaluation is None:
        raise RecommendationInvariantError("primary_evaluation es obligatoria (invariante 2).")
    if not (0.0 <= confidence <= 1.0):
        raise RecommendationInvariantError("confidence debe estar en [0.0, 1.0].")
    if confidence > assessment_confidence:
        raise RecommendationInvariantError(
            "confidence de la Recommendation no puede superar la confidence del Assessment "
            "que la origina (invariante 3 -- consistencia causal)."
        )
    if not decision_engine_version or not policy_version or not knowledge_version or not recommendation_version:
        raise RecommendationInvariantError(
            "Ninguna Recommendation nace sin sus cuatro versiones de trazabilidad (invariante 4)."
        )

    return Recommendation(
        case_id=case_id,
        assessment_id=assessment_id,
        status=RecommendationStatus.DRAFT,
        primary_evaluation=primary_evaluation.model_dump(mode="json"),
        alternative_evaluations=[ev.model_dump(mode="json") for ev in (alternative_evaluations or [])],
        confidence=confidence,
        rationale=list(rationale),
        narrative_summary=narrative_summary,
        next_step=next_step.model_dump(mode="json"),
        decision_engine_version=decision_engine_version,
        policy_version=policy_version,
        knowledge_version=knowledge_version,
        recommendation_version=recommendation_version,
        version=version,
    )


def issue(recommendation: Recommendation) -> Recommendation:
    """DRAFT -> ISSUED. Aplica invariante 5: rationale no puede estar vacío
    a partir de este punto (antes, en DRAFT, sí se permite mientras se
    compone el resultado -- ver §2, ciclo de vida)."""

    if recommendation.status != RecommendationStatus.DRAFT:
        raise RecommendationTransitionError(
            f"Solo se puede emitir (issue) desde DRAFT, no desde {recommendation.status}."
        )
    if not recommendation.rationale:
        raise RecommendationInvariantError(
            "rationale no puede estar vacío al emitir una Recommendation (invariante 5)."
        )

    recommendation.status = RecommendationStatus.ISSUED
    return recommendation


def accept(recommendation: Recommendation) -> Recommendation:
    """ISSUED -> ACCEPTED. La invariante 6 (una sola ACCEPTED por caso) se
    valida en la capa de aplicación/repositorio (Sprint 2/3), no acá."""

    if recommendation.status != RecommendationStatus.ISSUED:
        raise RecommendationTransitionError(
            f"Solo se puede aceptar desde ISSUED, no desde {recommendation.status}."
        )

    recommendation.status = RecommendationStatus.ACCEPTED
    recommendation.decided_at = datetime.now(UTC)
    return recommendation


def discard(recommendation: Recommendation) -> Recommendation:
    """ISSUED -> DISCARDED. No se permite reabrir una Recommendation
    descartada (§2) -- se genera una nueva versión en su lugar."""

    if recommendation.status != RecommendationStatus.ISSUED:
        raise RecommendationTransitionError(
            f"Solo se puede descartar desde ISSUED, no desde {recommendation.status}."
        )

    recommendation.status = RecommendationStatus.DISCARDED
    recommendation.decided_at = datetime.now(UTC)
    return recommendation
