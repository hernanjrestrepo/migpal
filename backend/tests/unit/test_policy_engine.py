"""
Policy Engine — filtrado y ranking de rutas candidatas (Sprint 3, Hito 3).

Sin red, sin DB -- `evaluate_candidate_routes` es pura (regla obligatoria 08).
"""

from core.policy_engine.catalog import ROUTE_CATALOG
from core.policy_engine.rules import evaluate_candidate_routes


def test_never_returns_empty_even_with_no_matched_signals():
    """Perfil sin ninguna señal detectada -- la regla de exclusión se
    desactiva para no dejar a Recommendation sin primary_evaluation."""
    evaluations = evaluate_candidate_routes(matched_signals=set(), objective_country=None)

    assert len(evaluations) == len(ROUTE_CATALOG)


def test_excludes_routes_with_zero_signal_overlap_when_some_route_qualifies():
    """Australia solo requiere "education" en el catálogo actual -- un
    perfil con únicamente "experience" no la sustenta y debe quedar fuera,
    mientras que O-1/Express Entry/España (que sí requieren "experience")
    califican y se devuelven."""
    evaluations = evaluate_candidate_routes(matched_signals={"experience"}, objective_country=None)

    countries = {ev.route.country for ev in evaluations}
    assert "Australia" not in countries
    assert countries == {"Estados Unidos", "Canadá", "España"}
    assert all(ev.route.fit_score > 0 for ev in evaluations)


def test_sorted_descending_by_fit_score():
    evaluations = evaluate_candidate_routes(matched_signals={"experience", "education"}, objective_country=None)

    scores = [ev.route.fit_score for ev in evaluations]
    assert scores == sorted(scores, reverse=True)


def test_objective_country_gives_a_bonus_to_the_matching_route():
    without_destination = evaluate_candidate_routes(matched_signals={"experience"}, objective_country=None)
    with_destination = evaluate_candidate_routes(matched_signals={"experience"}, objective_country="Canadá")

    fit_without = next(ev.route.fit_score for ev in without_destination if ev.route.country == "Canadá")
    fit_with = next(ev.route.fit_score for ev in with_destination if ev.route.country == "Canadá")

    assert fit_with > fit_without
    # Con el país declarado, esa ruta debe quedar primera (mayor fit).
    assert with_destination[0].route.country == "Canadá"


def test_missing_signals_reports_what_the_profile_lacks_for_each_route():
    """A-ADR-009 -- explicabilidad: cada RouteEvaluation expone qué señales
    requeridas por ESA ruta el perfil no tiene, no una lista genérica."""
    evaluations = evaluate_candidate_routes(matched_signals={"experience"}, objective_country=None)

    for ev in evaluations:
        expected_missing = {s for s in ev.missing_signals}
        assert "experience" not in expected_missing  # ya la tiene, no puede faltarle
        assert all(isinstance(s, str) for s in ev.missing_signals)


def test_route_fully_matched_has_no_missing_signals():
    canada = next(
        ev
        for ev in evaluate_candidate_routes(matched_signals={"experience", "education"}, objective_country=None)
        if ev.route.country == "Canadá"
    )
    assert canada.missing_signals == []


def test_same_inputs_produce_the_same_output():
    first = evaluate_candidate_routes(matched_signals={"experience", "education"}, objective_country="España")
    second = evaluate_candidate_routes(matched_signals={"experience", "education"}, objective_country="España")

    assert first == second
