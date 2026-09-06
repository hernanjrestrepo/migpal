"""
Budget — application handlers (Sprint 1, Hito 5).

Repositorio en memoria, mismo criterio que
tests/unit/test_execution_plan_handlers.py -- sin DB.
"""

import pytest

from core.budget.application.commands import CalcularPresupuestoCommand
from core.budget.application.handlers import handle_calcular_presupuesto
from core.budget.application.queries import ConsultarPresupuestoQuery, handle_consultar_presupuesto
from core.budget.domain.rules import BudgetInvariantError


class _InMemoryBudgetRepository:
    def __init__(self):
        self._by_id = {}
        self._next_id = 1

    def add(self, estimate):
        estimate.id = self._next_id
        self._next_id += 1
        self._by_id[estimate.id] = estimate
        return estimate

    def get_latest_for_case(self, case_id):
        matches = [e for e in self._by_id.values() if e.case_id == case_id]
        return max(matches, key=lambda e: e.id) if matches else None


def _command(**overrides):
    base = dict(
        case_id=5,
        family_size=3,
        origin_monthly_income=2200,
        destination_monthly_income=8700,
        government_fee=715,
        relocation_cost_low=6450,
        relocation_cost_high=10300,
        settlement_cost=31700,
        legal_fee_low=0.0,
        legal_fee_high=0.0,
    )
    base.update(overrides)
    return CalcularPresupuestoCommand(**base)


def test_handle_calcular_presupuesto_persists_estimate_with_computed_service_fee():
    repo = _InMemoryBudgetRepository()

    estimate = handle_calcular_presupuesto(_command(), repo)

    assert estimate.id is not None
    assert estimate.case_id == 5
    assert estimate.migpal_service_fee == 1000.0


def test_handle_calcular_presupuesto_raises_for_invalid_input():
    repo = _InMemoryBudgetRepository()

    with pytest.raises(BudgetInvariantError):
        handle_calcular_presupuesto(
            _command(relocation_cost_low=99999, relocation_cost_high=1), repo
        )


def test_handle_consultar_presupuesto_returns_view_with_breakeven():
    repo = _InMemoryBudgetRepository()
    handle_calcular_presupuesto(_command(), repo)

    view = handle_consultar_presupuesto(ConsultarPresupuestoQuery(case_id=5), repo)

    assert view is not None
    assert view.monthly_differential == 6500
    assert view.breakeven_months is not None
    assert view.breakeven_months > 0


def test_handle_consultar_presupuesto_returns_latest_when_recalculated():
    repo = _InMemoryBudgetRepository()
    handle_calcular_presupuesto(_command(family_size=3), repo)
    handle_calcular_presupuesto(_command(family_size=6), repo)

    view = handle_consultar_presupuesto(ConsultarPresupuestoQuery(case_id=5), repo)

    assert view.family_size == 6
    assert view.breakdown.migpal_service_fee == 1200.0


def test_handle_consultar_presupuesto_returns_none_if_no_estimate_exists():
    repo = _InMemoryBudgetRepository()
    assert handle_consultar_presupuesto(ConsultarPresupuestoQuery(case_id=5), repo) is None
