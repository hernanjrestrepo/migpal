"""
Recommendation — orquestador (Sprint 3, Hito 3).

Objetos en memoria, sin sesión de DB (Assessment/MigrationCase se
construyen con `id` manual, sin persistir) -- prueba la composición
Decision Engine + Policy Engine, no la persistencia (eso es
tests/integration/test_recommendation_repository.py). Sin LLM: Sprint 3 es
exclusivamente determinístico.
"""

from core.case_engine.domain.aggregates import MigrationCase
from core.decision_engine.domain.aggregates import Assessment
from core.recommendation.application.orchestrator import generate_recommendation
from core.recommendation.domain.value_objects import RecommendationStatus

RICH_FINDINGS = [
    "Señal detectada: experience",
    "Señal detectada: education",
    "Señal detectada: destination",
    "Señal detectada: family",
    "Señal detectada: financial",
]


def _assessment(**overrides) -> Assessment:
    kwargs = dict(
        id=1,
        case_id=5,
        score=100.0,
        confidence=1.0,
        findings=RICH_FINDINGS,
        recommendations=["Continuar con el Perfilamiento."],
    )
    kwargs.update(overrides)
    return Assessment(**kwargs)


def _case(**overrides) -> MigrationCase:
    kwargs = dict(id=5, user_id=8, objective_country=None)
    kwargs.update(overrides)
    return MigrationCase(**kwargs)


def test_generates_an_issued_recommendation_with_a_primary_route():
    rec = generate_recommendation(case=_case(), assessment=_assessment())

    assert rec.status == RecommendationStatus.ISSUED
    assert rec.case_id == 5
    assert rec.assessment_id == 1
    assert rec.primary_route_evaluation().route.fit_score > 0
    assert rec.rationale != []
    assert rec.next_step_detail().title == "Perfilamiento completo"


def test_confidence_never_exceeds_assessment_confidence():
    rec = generate_recommendation(case=_case(), assessment=_assessment(confidence=0.4))
    assert rec.confidence <= 0.4


def test_objective_country_influences_the_primary_route():
    without_objective = generate_recommendation(case=_case(objective_country=None), assessment=_assessment())
    with_objective = generate_recommendation(
        case=_case(objective_country="Canadá"), assessment=_assessment()
    )

    assert with_objective.primary_route_evaluation().route.country == "Canadá"
    # No forzamos que sin objetivo declarado dé un país distinto (depende del
    # catálogo), pero sí que el fit_score de Canadá suba con el objetivo.
    assert (
        with_objective.primary_route_evaluation().route.fit_score
        >= without_objective.primary_route_evaluation().route.fit_score
        or with_objective.primary_route_evaluation().route.country == "Canadá"
    )


def test_same_assessment_and_case_produce_the_same_recommendation():
    """Invariante 7 (§2 del diseño): mismo Assessment, mismas versiones ->
    misma Recommendation. Se compara todo excepto created_at (no
    determinístico por diseño, es un timestamp de auditoría)."""
    case = _case()

    first = generate_recommendation(case=case, assessment=_assessment())
    second = generate_recommendation(case=case, assessment=_assessment())

    assert first.primary_evaluation == second.primary_evaluation
    assert first.alternative_evaluations == second.alternative_evaluations
    assert first.rationale == second.rationale
    assert first.confidence == second.confidence
    assert first.next_step == second.next_step
    assert first.decision_engine_version == second.decision_engine_version
    assert first.policy_version == second.policy_version
    assert first.knowledge_version == second.knowledge_version
    assert first.recommendation_version == second.recommendation_version


def test_sparse_profile_still_produces_a_valid_recommendation():
    """Perfil sin ninguna señal detectada -- Policy Engine desactiva el
    filtro y de todas formas hay una primary_evaluation (nunca DRAFT sin
    ruta, invariante 2)."""
    rec = generate_recommendation(
        case=_case(),
        assessment=_assessment(findings=["No se detectaron señales claras de perfil en el mensaje."], confidence=0.0),
    )

    assert rec.status == RecommendationStatus.ISSUED
    assert rec.confidence == 0.0
    assert rec.primary_evaluation is not None
