"""
Budget — application: handlers (Sprint 1, Hito 5).

Único lugar (junto con `domain/rules.py`, que este handler envuelve) donde
vive orquestación de BudgetEstimate. `adapters/api.py` no debe importar
`domain.rules` -- solo llama a este handler y traduce excepciones a HTTP
(mismo criterio que el resto de los bounded contexts, ver
docs/HITO_5_DESIGN.md §2).
"""

from __future__ import annotations

from core.budget.application.commands import CalcularPresupuestoCommand
from core.budget.domain.aggregates import BudgetEstimate
from core.budget.domain.rules import build_cost_breakdown
from core.budget.infrastructure.repository import BudgetRepository


def handle_calcular_presupuesto(cmd: CalcularPresupuestoCommand, repo: BudgetRepository) -> BudgetEstimate:
    breakdown = build_cost_breakdown(
        family_size=cmd.family_size,
        government_fee=cmd.government_fee,
        relocation_cost_low=cmd.relocation_cost_low,
        relocation_cost_high=cmd.relocation_cost_high,
        settlement_cost=cmd.settlement_cost,
        legal_fee_low=cmd.legal_fee_low,
        legal_fee_high=cmd.legal_fee_high,
    )

    estimate = BudgetEstimate(
        case_id=cmd.case_id,
        family_size=cmd.family_size,
        migpal_service_fee=breakdown.migpal_service_fee,
        government_fee=breakdown.government_fee,
        relocation_cost_low=breakdown.relocation_cost_low,
        relocation_cost_high=breakdown.relocation_cost_high,
        settlement_cost=breakdown.settlement_cost,
        legal_fee_low=breakdown.legal_fee_low,
        legal_fee_high=breakdown.legal_fee_high,
        origin_monthly_income=cmd.origin_monthly_income,
        destination_monthly_income=cmd.destination_monthly_income,
    )
    return repo.add(estimate)
