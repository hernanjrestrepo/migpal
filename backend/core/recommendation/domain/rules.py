"""
Recommendation — domain: invariantes y transiciones de estado (Sprint 1, Hito 3).

Funciones puras, sin efectos secundarios y sin acceso a base de datos --
mismo espíritu que `decision_engine/infrastructure/scoring.py` (regla
obligatoria 08: reproducibilidad). Case Engine/Anexo A: el aggregate no
contiene lógica, así que las reglas viven acá, no en `aggregates.py`.

Invariante 6 (§2 -- "solo una Recommendation ACCEPTED por caso a la vez"):
`accept()` la valida acá, recibiendo `existing_accepted` como parámetro --
la función sigue siendo pura (no consulta el repositorio ella misma), pero
la regla de negocio en sí vive en `domain/`, no en la capa de aplicación ni
en el adapter de API. Quien orquesta (`application/handlers.py`) es
responsable de obtener `existing_accepted` del repositorio y pasarlo acá;
el adapter de API (`adapters/api.py`) no conoce esta regla en absoluto --
solo traduce la excepción resultante a un código HTTP.

Corrección post-cierre inicial de Hito 3 (revisión de arquitectura,
2026-07-31): la primera versión de `POST /v1/recommendation/{id}/accept`
tenía esta validación directamente en `adapters/api.py`. Se detectó como
regla de negocio mal ubicada -- un adapter no puede decidir si una
Recommendation puede aceptarse o no, eso es dominio. Se corrigió sin
cambiar el comportamiento observable (mismo 409, mismo mensaje).
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


def accept(recommendation: Recommendation, *, existing_accepted: Recommendation | None = None) -> Recommendation:
    """ISSUED -> ACCEPTED.

    `existing_accepted`: la Recommendation ACCEPTED actual del mismo caso,
    si existe (obtenida por quien llama, vía el repositorio -- ver
    docstring del módulo). Si es de un id distinto al que se está
    aceptando, viola la invariante 6. Si es `None` o es la misma
    Recommendation (aceptar dos veces la misma, idempotente a nivel de
    id), no hay conflicto."""

    if recommendation.status != RecommendationStatus.ISSUED:
        raise RecommendationTransitionError(
            f"Solo se puede aceptar desde ISSUED, no desde {recommendation.status}."
        )
    if existing_accepted is not None and existing_accepted.id != recommendation.id:
        raise RecommendationInvariantError(
            "Ya existe una Recommendation ACCEPTED para este caso (invariante 6)."
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
