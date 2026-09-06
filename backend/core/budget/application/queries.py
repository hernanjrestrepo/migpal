"""Budget — application: consultas (Sprint 1, Hito 5)."""

from __future__ import annotations

from dataclasses import dataclass

from core.budget.domain.aggregates import BudgetEstimate
from core.budget.domain.rules import CostBreakdown, breakeven_months, monthly_income_differential
from core.budget.infrastructure.repository import BudgetRepository


@dataclass(frozen=True)
class ConsultarPresupuestoQuery:
    case_id: int


@dataclass(frozen=True)
class BudgetView:
    id: int
    case_id: int
    family_size: int
    breakdown: CostBreakdown
    origin_monthly_income: float
    destination_monthly_income: float
    monthly_differential: float
    breakeven_months: float | None


def build_budget_view(estimate: BudgetEstimate) -> BudgetView:
    """Recalcula el diferencial y el punto de equilibrio a partir de lo
    persistido -- nunca se guardan como columnas propias para no tener dos
    fuentes de verdad del mismo cálculo (la misma razón por la que
    ExecutionPlanView deriva `blocked`/`completed_count` en vez de
    persistirlos, ver `execution_plan/application/queries.py`)."""

    breakdown = CostBreakdown(
        migpal_service_fee=estimate.migpal_service_fee,
        government_fee=estimate.government_fee,
        relocation_cost_low=estimate.relocation_cost_low,
        relocation_cost_high=estimate.relocation_cost_high,
        settlement_cost=estimate.settlement_cost,
        legal_fee_low=estimate.legal_fee_low,
        legal_fee_high=estimate.legal_fee_high,
    )
    differential = monthly_income_differential(
        origin_monthly_income=estimate.origin_monthly_income,
        destination_monthly_income=estimate.destination_monthly_income,
    )
    return BudgetView(
        id=estimate.id,
        case_id=estimate.case_id,
        family_size=estimate.family_size,
        breakdown=breakdown,
        origin_monthly_income=estimate.origin_monthly_income,
        destination_monthly_income=estimate.destination_monthly_income,
        monthly_differential=differential,
        breakeven_months=breakeven_months(total_cost=breakdown.total_high, monthly_differential=differential),
    )


def handle_consultar_presupuesto(query: ConsultarPresupuestoQuery, repo: BudgetRepository) -> BudgetView | None:
    estimate = repo.get_latest_for_case(query.case_id)
    if estimate is None:
        return None
    return build_budget_view(estimate)
