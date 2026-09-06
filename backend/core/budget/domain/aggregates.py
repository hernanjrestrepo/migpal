"""
Budget — domain: Aggregate Root BudgetEstimate (Sprint 1, Hito 5).

Cada cálculo se persiste como una fila nueva (historial append-only) en vez
de mutar una única estimación "activa" -- a diferencia de ExecutionPlan
(que sí tiene invariante de unicidad), acá el usuario puede recalcular
tantas veces como quiera al ajustar sus estimados de traslado o de ingreso,
y ver cómo cambió respecto a la vez anterior tiene valor propio. `GET
/v1/budget` (adapters/api.py) siempre devuelve la más reciente.
"""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class BudgetEstimate(SQLModel, table=True):
    __tablename__ = "budget_estimates"

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="migration_cases.id", index=True)

    family_size: int

    migpal_service_fee: float
    government_fee: float
    relocation_cost_low: float
    relocation_cost_high: float
    settlement_cost: float
    legal_fee_low: float
    legal_fee_high: float

    origin_monthly_income: float
    destination_monthly_income: float

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
