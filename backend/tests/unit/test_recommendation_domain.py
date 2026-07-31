"""
Recommendation — dominio (Sprint 1, Hito 3).

Sin red, sin IA, sin base de datos -- `build_recommendation`/`issue`/
`accept`/`discard` son funciones puras sobre objetos en memoria. Mismo
espíritu que test_decision_engine_scoring.py: si esto se rompe, se rompió
una invariante del dominio, no un detalle de infraestructura.
"""

import pytest

from core.recommendation.domain.rules import (
    RecommendationInvariantError,
    RecommendationTransitionError,
    accept,
    build_recommendation,
    discard,
    issue,
)
from core.recommendation.domain.value_objects import (
    MigrationRoute,
    NextStep,
    RecommendationStatus,
    RouteEvaluation,
)

ROUTE = MigrationRoute(visa_type="O-1", country="Estados Unidos", fit_score=82.0)
EVALUATION = RouteEvaluation(
    route=ROUTE,
    strengths=["Experiencia sólida"],
    risks=["Falta evidencia documental"],
    required_documents=["CV", "Cartas de recomendación"],
)
NEXT_STEP = NextStep(title="Perfilamiento completo", description="Documentar logros para O-1")


def _base_kwargs(**overrides):
    kwargs = dict(
        case_id=5,
        assessment_id=2,
        assessment_confidence=1.0,
        primary_evaluation=EVALUATION,
        next_step=NEXT_STEP,
        confidence=0.8,
        rationale=["Señal detectada: experience", "Señal detectada: education"],
    )
    kwargs.update(overrides)
    return kwargs


# -- Invariantes de construcción (§2) --


def test_build_recommendation_succeeds_with_valid_inputs():
    rec = build_recommendation(**_base_kwargs())

    assert rec.status == RecommendationStatus.DRAFT
    assert rec.case_id == 5
    assert rec.assessment_id == 2
    assert rec.confidence == 0.8
    assert rec.decision_engine_version == "1.0"
    assert rec.policy_version == "1.0"
    assert rec.knowledge_version == "1.0"
    assert rec.recommendation_version == "1.0"


def test_requires_case_id():
    with pytest.raises(RecommendationInvariantError):
        build_recommendation(**_base_kwargs(case_id=0))


def test_requires_assessment_id():
    with pytest.raises(RecommendationInvariantError):
        build_recommendation(**_base_kwargs(assessment_id=0))


def test_requires_primary_evaluation():
    with pytest.raises(RecommendationInvariantError):
        build_recommendation(**_base_kwargs(primary_evaluation=None))


def test_confidence_must_be_within_zero_and_one():
    with pytest.raises(RecommendationInvariantError):
        build_recommendation(**_base_kwargs(confidence=1.5))
    with pytest.raises(RecommendationInvariantError):
        build_recommendation(**_base_kwargs(confidence=-0.1))


def test_confidence_cannot_exceed_assessment_confidence():
    """Invariante 3 -- no se puede estar más seguro de la ruta que del
    perfil sobre el que se basa (consistencia causal)."""
    with pytest.raises(RecommendationInvariantError):
        build_recommendation(**_base_kwargs(assessment_confidence=0.5, confidence=0.8))

    # Igual a la confidence del Assessment sí es válido (límite inclusive).
    rec = build_recommendation(**_base_kwargs(assessment_confidence=0.8, confidence=0.8))
    assert rec.confidence == 0.8


def test_requires_all_four_versions():
    with pytest.raises(RecommendationInvariantError):
        build_recommendation(**_base_kwargs(decision_engine_version=""))
    with pytest.raises(RecommendationInvariantError):
        build_recommendation(**_base_kwargs(policy_version=""))
    with pytest.raises(RecommendationInvariantError):
        build_recommendation(**_base_kwargs(knowledge_version=""))
    with pytest.raises(RecommendationInvariantError):
        build_recommendation(**_base_kwargs(recommendation_version=""))


def test_alternative_evaluations_defaults_to_empty_list_not_none():
    rec = build_recommendation(**_base_kwargs())
    assert rec.alternative_evaluations == []


# -- Reproducibilidad determinística (invariante 7) --


def test_same_inputs_produce_the_same_business_fields():
    """No se compara created_at (no determinístico por diseño -- es un
    timestamp de auditoría, no parte de la decisión). Todo lo demás debe
    ser idéntico byte a byte entre dos construcciones con el mismo input."""
    first = build_recommendation(**_base_kwargs())
    second = build_recommendation(**_base_kwargs())

    assert first.primary_evaluation == second.primary_evaluation
    assert first.alternative_evaluations == second.alternative_evaluations
    assert first.rationale == second.rationale
    assert first.confidence == second.confidence
    assert first.next_step == second.next_step
    assert first.status == second.status


# -- Serialización VO <-> JSON persistido --


def test_primary_route_evaluation_round_trips_through_the_value_object():
    rec = build_recommendation(**_base_kwargs())
    evaluation = rec.primary_route_evaluation()

    assert evaluation == EVALUATION
    assert evaluation.route.visa_type == "O-1"


def test_next_step_detail_round_trips_through_the_value_object():
    rec = build_recommendation(**_base_kwargs())
    assert rec.next_step_detail() == NEXT_STEP


# -- Transiciones de estado (ciclo de vida, §2) --


def test_issue_moves_draft_to_issued():
    rec = build_recommendation(**_base_kwargs())
    issued = issue(rec)
    assert issued.status == RecommendationStatus.ISSUED


def test_issue_requires_non_empty_rationale():
    rec = build_recommendation(**_base_kwargs(rationale=[]))
    with pytest.raises(RecommendationInvariantError):
        issue(rec)


def test_issue_fails_if_not_in_draft():
    rec = issue(build_recommendation(**_base_kwargs()))
    with pytest.raises(RecommendationTransitionError):
        issue(rec)


def test_accept_moves_issued_to_accepted_and_sets_decided_at():
    rec = issue(build_recommendation(**_base_kwargs()))
    assert rec.decided_at is None

    accepted = accept(rec)
    assert accepted.status == RecommendationStatus.ACCEPTED
    assert accepted.decided_at is not None


def test_accept_fails_if_not_issued():
    rec = build_recommendation(**_base_kwargs())  # DRAFT
    with pytest.raises(RecommendationTransitionError):
        accept(rec)


def test_discard_moves_issued_to_discarded_and_sets_decided_at():
    rec = issue(build_recommendation(**_base_kwargs()))
    discarded = discard(rec)
    assert discarded.status == RecommendationStatus.DISCARDED
    assert discarded.decided_at is not None


def test_discard_fails_if_not_issued():
    rec = accept(issue(build_recommendation(**_base_kwargs())))
    with pytest.raises(RecommendationTransitionError):
        discard(rec)
