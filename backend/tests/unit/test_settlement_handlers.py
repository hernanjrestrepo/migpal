"""
Settlement — application handlers (Sprint 2, Hito 5).

Repositorios en memoria, mismo criterio que
tests/unit/test_execution_plan_handlers.py -- sin DB.
"""

import pytest

from core.recommendation.domain.rules import accept, build_recommendation, issue
from core.recommendation.domain.value_objects import MigrationRoute, NextStep, RouteEvaluation
from core.settlement.application.commands import ActualizarItemCommand, GenerarChecklistCommand
from core.settlement.application.handlers import handle_actualizar_item, handle_generar_checklist
from core.settlement.application.queries import ConsultarMiChecklistQuery, handle_consultar_mi_checklist
from core.settlement.domain.rules import SettlementInvariantError
from core.settlement.domain.value_objects import SettlementItemStatus
from core.shared.exceptions import RecommendationNotFound, SettlementNotFound

ROUTE = MigrationRoute(visa_type="Express Entry", country="Canadá", fit_score=81.0)
EVALUATION = RouteEvaluation(route=ROUTE, strengths=[], risks=[], required_documents=["Perfil Express Entry"])
NEXT_STEP = NextStep(title="Crear tu perfil", description="Crear el perfil en el sistema de Express Entry")


class _InMemoryRecommendationRepository:
    def __init__(self):
        self._by_id = {}
        self._next_id = 1

    def add(self, recommendation):
        recommendation.id = self._next_id
        self._next_id += 1
        self._by_id[recommendation.id] = recommendation
        return recommendation

    def get_accepted_for_case(self, case_id):
        for r in self._by_id.values():
            if r.case_id == case_id and r.status.value == "ACCEPTED":
                return r
        return None


class _InMemorySettlementRepository:
    def __init__(self):
        self._by_case = {}
        self._by_id = {}
        self._next_checklist_id = 1
        self._next_item_id = 1

    def add(self, checklist):
        checklist.id = self._next_checklist_id
        self._next_checklist_id += 1
        for item in checklist.items:
            item.id = self._next_item_id
            self._next_item_id += 1
            item.checklist_id = checklist.id
        self._by_case[checklist.case_id] = checklist
        self._by_id[checklist.id] = checklist
        return checklist

    def save(self, checklist, *, updated_item_id=None):
        return checklist

    def get_for_case(self, case_id):
        return self._by_case.get(case_id)

    def get_by_id(self, checklist_id):
        return self._by_id.get(checklist_id)


def _accepted_recommendation(repo, case_id=5):
    rec = build_recommendation(
        case_id=case_id,
        assessment_id=1,
        assessment_confidence=1.0,
        primary_evaluation=EVALUATION,
        next_step=NEXT_STEP,
        confidence=0.8,
        rationale=["Señal detectada: experience"],
    )
    rec = accept(issue(rec))
    return repo.add(rec)


# ---- handle_generar_checklist ----


def test_handle_generar_checklist_persists_checklist_with_items_from_recommendation_country():
    rec_repo = _InMemoryRecommendationRepository()
    settlement_repo = _InMemorySettlementRepository()
    _accepted_recommendation(rec_repo, case_id=5)

    checklist = handle_generar_checklist(GenerarChecklistCommand(case_id=5), settlement_repo, rec_repo)

    assert checklist.id is not None
    assert checklist.case_id == 5
    assert checklist.country == "Canadá"
    assert len(checklist.items) == 6
    assert all(i.id is not None for i in checklist.items)


def test_handle_generar_checklist_raises_not_found_if_no_accepted_recommendation():
    rec_repo = _InMemoryRecommendationRepository()
    settlement_repo = _InMemorySettlementRepository()

    with pytest.raises(RecommendationNotFound):
        handle_generar_checklist(GenerarChecklistCommand(case_id=5), settlement_repo, rec_repo)


def test_handle_generar_checklist_raises_if_case_already_has_checklist():
    rec_repo = _InMemoryRecommendationRepository()
    settlement_repo = _InMemorySettlementRepository()
    _accepted_recommendation(rec_repo, case_id=5)
    handle_generar_checklist(GenerarChecklistCommand(case_id=5), settlement_repo, rec_repo)

    with pytest.raises(SettlementInvariantError):
        handle_generar_checklist(GenerarChecklistCommand(case_id=5), settlement_repo, rec_repo)


# ---- handle_actualizar_item ----


def test_handle_actualizar_item_updates_status():
    rec_repo = _InMemoryRecommendationRepository()
    settlement_repo = _InMemorySettlementRepository()
    _accepted_recommendation(rec_repo, case_id=5)
    checklist = handle_generar_checklist(GenerarChecklistCommand(case_id=5), settlement_repo, rec_repo)
    item = checklist.items[0]

    result = handle_actualizar_item(
        ActualizarItemCommand(checklist_id=checklist.id, item_id=item.id, case_id=5, status=SettlementItemStatus.DONE),
        settlement_repo,
    )

    updated = next(i for i in result.items if i.id == item.id)
    assert updated.status == SettlementItemStatus.DONE


def test_handle_actualizar_item_raises_for_wrong_case_id():
    rec_repo = _InMemoryRecommendationRepository()
    settlement_repo = _InMemorySettlementRepository()
    _accepted_recommendation(rec_repo, case_id=5)
    checklist = handle_generar_checklist(GenerarChecklistCommand(case_id=5), settlement_repo, rec_repo)
    item = checklist.items[0]

    with pytest.raises(SettlementNotFound):
        handle_actualizar_item(
            ActualizarItemCommand(
                checklist_id=checklist.id, item_id=item.id, case_id=999, status=SettlementItemStatus.DONE
            ),
            settlement_repo,
        )


# ---- handle_consultar_mi_checklist ----


def test_handle_consultar_mi_checklist_returns_view_with_counts():
    rec_repo = _InMemoryRecommendationRepository()
    settlement_repo = _InMemorySettlementRepository()
    _accepted_recommendation(rec_repo, case_id=5)
    checklist = handle_generar_checklist(GenerarChecklistCommand(case_id=5), settlement_repo, rec_repo)
    handle_actualizar_item(
        ActualizarItemCommand(
            checklist_id=checklist.id, item_id=checklist.items[0].id, case_id=5, status=SettlementItemStatus.DONE
        ),
        settlement_repo,
    )

    view = handle_consultar_mi_checklist(ConsultarMiChecklistQuery(case_id=5), settlement_repo)

    assert view is not None
    assert view.total_count == 6
    assert view.done_count == 1


def test_handle_consultar_mi_checklist_returns_none_if_no_checklist_exists():
    settlement_repo = _InMemorySettlementRepository()
    assert handle_consultar_mi_checklist(ConsultarMiChecklistQuery(case_id=5), settlement_repo) is None
