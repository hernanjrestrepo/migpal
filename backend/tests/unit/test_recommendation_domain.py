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
    select_route,
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


def test_accept_fails_if_a_different_recommendation_is_already_accepted():
    """Invariante 6 -- vive en domain/rules.py, no en application/ ni en
    adapters/ (corrección de arquitectura post-revisión de Hito 3)."""
    rec = issue(build_recommendation(**_base_kwargs()))
    other_already_accepted = issue(build_recommendation(**_base_kwargs()))
    other_already_accepted.id = 999  # simula que ya fue persistida con otro id

    with pytest.raises(RecommendationInvariantError):
        accept(rec, existing_accepted=other_already_accepted)


def test_accept_succeeds_when_existing_accepted_is_the_same_recommendation():
    rec = issue(build_recommendation(**_base_kwargs()))
    rec.id = 42

    accepted = accept(rec, existing_accepted=rec)
    assert accepted.status == RecommendationStatus.ACCEPTED


def test_accept_succeeds_when_there_is_no_existing_accepted():
    rec = issue(build_recommendation(**_base_kwargs()))
    accepted = accept(rec, existing_accepted=None)
    assert accepted.status == RecommendationStatus.ACCEPTED


def test_discard_moves_issued_to_discarded_and_sets_decided_at():
    rec = issue(build_recommendation(**_base_kwargs()))
    discarded = discard(rec)
    assert discarded.status == RecommendationStatus.DISCARDED
    assert discarded.decided_at is not None


def test_discard_fails_if_not_issued():
    rec = accept(issue(build_recommendation(**_base_kwargs())))
    with pytest.raises(RecommendationTransitionError):
        discard(rec)


# -- select_route (A-ADR-009) --

ALT_ROUTE_A = MigrationRoute(visa_type="Express Entry", country="Canadá", fit_score=60.0)
ALT_EVAL_A = RouteEvaluation(route=ALT_ROUTE_A, strengths=["..."], risks=["..."], required_documents=["..."])
ALT_ROUTE_B = MigrationRoute(visa_type="Subclass 189", country="Australia", fit_score=40.0)
ALT_EVAL_B = RouteEvaluation(route=ALT_ROUTE_B, strengths=["..."], risks=["..."], required_documents=["..."])


def _issued_with_alternatives():
    rec = build_recommendation(**_base_kwargs(alternative_evaluations=[ALT_EVAL_A, ALT_EVAL_B]))
    return issue(rec)


def test_select_route_promotes_alternative_to_primary_and_demotes_previous_primary():
    rec = _issued_with_alternatives()

    updated = select_route(rec, alternative_index=0)

    assert updated.primary_route_evaluation() == ALT_EVAL_A
    remaining = updated.alternative_route_evaluations()
    assert ALT_EVAL_B in remaining
    assert EVALUATION in remaining  # la primaria original queda como alternativa
    assert len(remaining) == 2


def test_select_route_appends_a_deterministic_manual_choice_note_to_rationale():
    rec = _issued_with_alternatives()
    original_rationale = list(rec.rationale)

    updated = select_route(rec, alternative_index=1)

    assert updated.rationale[: len(original_rationale)] == original_rationale
    assert "Elegiste esta ruta manualmente" in updated.rationale[-1]


def test_select_route_does_not_change_confidence():
    rec = _issued_with_alternatives()
    original_confidence = rec.confidence

    updated = select_route(rec, alternative_index=0)

    assert updated.confidence == original_confidence


def test_select_route_fails_outside_issued():
    draft = build_recommendation(**_base_kwargs(alternative_evaluations=[ALT_EVAL_A]))
    with pytest.raises(RecommendationTransitionError):
        select_route(draft, alternative_index=0)

    accepted = accept(_issued_with_alternatives())
    with pytest.raises(RecommendationTransitionError):
        select_route(accepted, alternative_index=0)


def test_select_route_rejects_out_of_range_index():
    rec = _issued_with_alternatives()

    with pytest.raises(RecommendationInvariantError):
        select_route(rec, alternative_index=99)

    with pytest.raises(RecommendationInvariantError):
        select_route(rec, alternative_index=-1)
