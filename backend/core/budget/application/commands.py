"""Budget — application: comandos (Sprint 1, Hito 5)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CalcularPresupuestoCommand:
    case_id: int
    family_size: int
    origin_monthly_income: float
    destination_monthly_income: float
    government_fee: float
    relocation_cost_low: float
    relocation_cost_high: float
    settlement_cost: float
    legal_fee_low: float = 0.0
    legal_fee_high: float = 0.0
