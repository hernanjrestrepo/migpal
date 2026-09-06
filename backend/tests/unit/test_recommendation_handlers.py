"""
Recommendation — application handlers (estabilización, Hito 3).

Repositorio en memoria (cumple el Protocol `RecommendationRepository` de
domain/repository.py) -- sin DB. Prueba que la orquestación de accept/discard
vive en application/ (delegando la invariante 6 a domain/rules.py), no en el
adapter de API. El adapter real se sigue probando contra Postgres real en
tests/contracts/test_recommendation_contract.py.
"""

import pytest

from core.recommendation.application.commands import (
    AcceptRecommendationCommand,
    DiscardRecommendationCommand,
    SelectRouteCommand,
)
from core.recommendation.application.handlers import (
    handle_accept_recommendation,
    handle_discard_recommendation,
    handle_select_route,
)
from core.recommendation.domain.rules import (
    RecommendationInvariantError,
    RecommendationTransitionError,
    build_recommendation,
    issue,
)
from core.recommendation.domain.value_objects import MigrationRoute, NextStep, RouteEvaluation
from core.shared.exceptions import RecommendationNotFound

ROUTE = MigrationRoute(visa_type="O-1", country="Estados Unidos", fit_score=82.0)
EVALUATION = RouteEvaluation(route=ROUTE, strengths=[], risks=[], required_documents=[])
NEXT_STEP = NextStep(title="Perfilamiento completo", description="...")


class _InMemoryRecommendationRepository:
    """Implementa el mismo Protocol que la versión real contra Postgres."""

    def __init__(self):
        self._by_id = {}
        self._next_id = 1

    def add(self, recommendation):
        recommendation.id = self._next_id
        self._next_id += 1
        self._by_id[recommendation.id] = recommendation
        return recommendation

    def save(self, recommendation):
        if recommendation.id is None:
            return self.add(recommendation)
        self._by_id[recommendation.id] = recommendation
        return recommendation

    def save_route_selection(self, recommendation):
        self._by_id[recommendation.id] = recommendation
        return recommendation

    def get_latest_for_case(self, case_id):
        matches = [r for r in self._by_id.values() if r.case_id == case_id]
        return max(matches, key=lambda r: r.id) if matches else None

    def get_by_id(self, recommendation_id):
        return self._by_id.get(recommendation_id)

    def get_accepted_for_case(self, case_id):
        for r in self._by_id.values():
            if r.case_id == case_id and r.status.value == "ACCEPTED":
                return r
        return None


ALT_ROUTE = MigrationRoute(visa_type="Express Entry", country="Canadá", fit_score=60.0)
ALT_EVALUATION = RouteEvaluation(route=ALT_ROUTE, strengths=[], risks=[], required_documents=[])


class _StubAIAdapter:
    async def narrate(self, *, primary, rationale):
        return f"Narrativa para {primary.route.visa_type}."


def _issued(case_id=5, assessment_id=2, alternative_evaluations=None):
    rec = build_recommendation(
        case_id=case_id,
        assessment_id=assessment_id,
        assessment_confidence=1.0,
        primary_evaluation=EVALUATION,
        alternative_evaluations=alternative_evaluations,
        next_step=NEXT_STEP,
        confidence=0.8,
        rationale=["Señal detectada: experience"],
    )
    return issue(rec)


def test_handle_accept_persists_and_returns_accepted():
    repo = _InMemoryRecommendationRepository()
    rec = repo.add(_issued())

    result = handle_accept_recommendation(
        AcceptRecommendationCommand(recommendation_id=rec.id, case_id=rec.case_id), repo
    )

    assert result.status.value == "ACCEPTED"
    assert repo.get_by_id(rec.id).status.value == "ACCEPTED"


def test_handle_accept_raises_not_found_for_wrong_case_id():
    """El adapter le pasa siempre el case_id del usuario autenticado -- si
    la Recommendation es de otro caso, no debe poder aceptarla ni verla."""
    repo = _InMemoryRecommendationRepository()
    rec = repo.add(_issued(case_id=5))

    with pytest.raises(RecommendationNotFound):
        handle_accept_recommendation(
            AcceptRecommendationCommand(recommendation_id=rec.id, case_id=999), repo
        )


def test_handle_accept_raises_not_found_for_missing_id():
    repo = _InMemoryRecommendationRepository()
    with pytest.raises(RecommendationNotFound):
        handle_accept_recommendation(AcceptRecommendationCommand(recommendation_id=1234, case_id=5), repo)


def test_handle_accept_enforces_invariant_6_via_domain_not_via_handler_logic():
    """La invariante 6 se prueba de verdad en domain/rules.py
    (test_recommendation_domain.py) -- acá solo se confirma que el handler
    la respeta end-to-end usando el repositorio en memoria."""
    repo = _InMemoryRecommendationRepository()
    first = repo.add(_issued(case_id=5))
    second = repo.add(_issued(case_id=5))

    handle_accept_recommendation(
        AcceptRecommendationCommand(recommendation_id=first.id, case_id=5), repo
    )

    with pytest.raises(RecommendationInvariantError):
        handle_accept_recommendation(
            AcceptRecommendationCommand(recommendation_id=second.id, case_id=5), repo
        )


def test_handle_accept_fails_on_second_call_for_the_same_recommendation():
    repo = _InMemoryRecommendationRepository()
    rec = repo.add(_issued())
    handle_accept_recommendation(AcceptRecommendationCommand(recommendation_id=rec.id, case_id=rec.case_id), repo)

    with pytest.raises(RecommendationTransitionError):
        handle_accept_recommendation(
            AcceptRecommendationCommand(recommendation_id=rec.id, case_id=rec.case_id), repo
        )


def test_handle_discard_persists_and_returns_discarded():
    repo = _InMemoryRecommendationRepository()
    rec = repo.add(_issued())

    result = handle_discard_recommendation(
        DiscardRecommendationCommand(recommendation_id=rec.id, case_id=rec.case_id), repo
    )

    assert result.status.value == "DISCARDED"


def test_handle_discard_raises_not_found_for_wrong_case_id():
    repo = _InMemoryRecommendationRepository()
    rec = repo.add(_issued(case_id=5))

    with pytest.raises(RecommendationNotFound):
        handle_discard_recommendation(
            DiscardRecommendationCommand(recommendation_id=rec.id, case_id=999), repo
        )


# -- handle_select_route (A-ADR-009) --


@pytest.mark.asyncio
async def test_handle_select_route_promotes_alternative_and_rewrites_narrative():
    repo = _InMemoryRecommendationRepository()
    rec = repo.add(_issued(alternative_evaluations=[ALT_EVALUATION]))

    result = await handle_select_route(
        SelectRouteCommand(recommendation_id=rec.id, case_id=rec.case_id, alternative_index=0),
        repo,
        _StubAIAdapter(),
    )

    assert result.primary_route_evaluation() == ALT_EVALUATION
    assert "Express Entry" in result.narrative_summary
    assert repo.get_by_id(rec.id).primary_route_evaluation() == ALT_EVALUATION


@pytest.mark.asyncio
async def test_handle_select_route_raises_not_found_for_wrong_case_id():
    repo = _InMemoryRecommendationRepository()
    rec = repo.add(_issued(case_id=5, alternative_evaluations=[ALT_EVALUATION]))

    with pytest.raises(RecommendationNotFound):
        await handle_select_route(
            SelectRouteCommand(recommendation_id=rec.id, case_id=999, alternative_index=0),
            repo,
            _StubAIAdapter(),
        )


@pytest.mark.asyncio
async def test_handle_select_route_raises_invariant_error_for_bad_index():
    repo = _InMemoryRecommendationRepository()
    rec = repo.add(_issued(alternative_evaluations=[ALT_EVALUATION]))

    with pytest.raises(RecommendationInvariantError):
        await handle_select_route(
            SelectRouteCommand(recommendation_id=rec.id, case_id=rec.case_id, alternative_index=7),
            repo,
            _StubAIAdapter(),
        )


@pytest.mark.asyncio
async def test_handle_select_route_fails_after_accept():
    repo = _InMemoryRecommendationRepository()
    rec = repo.add(_issued(alternative_evaluations=[ALT_EVALUATION]))
    handle_accept_recommendation(AcceptRecommendationCommand(recommendation_id=rec.id, case_id=rec.case_id), repo)

    with pytest.raises(RecommendationTransitionError):
        await handle_select_route(
            SelectRouteCommand(recommendation_id=rec.id, case_id=rec.case_id, alternative_index=0),
            repo,
            _StubAIAdapter(),
        )
