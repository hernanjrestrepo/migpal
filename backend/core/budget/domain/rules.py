"""
Budget — domain: cálculo determinístico de presupuesto y ROI migratorio
(Sprint 1, Hito 5).

Funciones puras, sin DB -- mismo espíritu que
`core/recommendation/domain/rules.py` y `core/execution_plan/domain/rules.py`.
Ver docs/HITO_5_DESIGN.md §2.

Decisión deliberada: este módulo NO trae tasas de gobierno ni costos de
asesoría legal desde un catálogo "verificado" propio -- a diferencia de
`policy_engine/catalog.py` (que exige fuente oficial citada para cada dato),
las tasas de gobierno cambian con frecuencia y varían según el caso
concreto. Inventar un número aquí violaría la misma regla que
`policy_engine/catalog.py` ya declara para sí mismo ("NADA se escribe acá si
no se leyó primero en la fuente oficial"). Por eso `compute_estimate()`
recibe esos costos como estimados que aporta el usuario o un asesor -- lo
único que este módulo calcula con autoridad propia es la tarifa de MigPAL
(que sí es un dato que la plataforma controla) y las derivaciones
aritméticas (total, diferencial, punto de equilibrio).
"""

from __future__ import annotations

from dataclasses import dataclass

BASE_SERVICE_FEE_USD = 1000.0
BASE_FEE_GROUP_SIZE = 5
EXTRA_PERSON_FEE_USD = 200.0


class BudgetInvariantError(ValueError):
    """Entrada inválida para el cálculo de presupuesto."""


def service_fee_for_family_size(family_size: int) -> float:
    """Grupo familiar hasta `BASE_FEE_GROUP_SIZE` personas (1er y 2do grado):
    tarifa plana `BASE_SERVICE_FEE_USD`. Cada persona adicional suma
    `EXTRA_PERSON_FEE_USD` -- ver docs/HITO_5_DESIGN.md §5 (modelo de
    negocio) para la justificación de estos montos."""

    if family_size < 1:
        raise BudgetInvariantError("El grupo familiar debe tener al menos 1 persona.")

    extra_people = max(0, family_size - BASE_FEE_GROUP_SIZE)
    return BASE_SERVICE_FEE_USD + extra_people * EXTRA_PERSON_FEE_USD


@dataclass(frozen=True)
class CostBreakdown:
    """Rango de costo total estimado de migrar -- suma de la tarifa de
    MigPAL (autoritativa) más los estimados que aporta el usuario."""

    migpal_service_fee: float
    government_fee: float
    relocation_cost_low: float
    relocation_cost_high: float
    settlement_cost: float
    legal_fee_low: float
    legal_fee_high: float

    @property
    def total_low(self) -> float:
        return (
            self.migpal_service_fee
            + self.government_fee
            + self.relocation_cost_low
            + self.settlement_cost
            + self.legal_fee_low
        )

    @property
    def total_high(self) -> float:
        return (
            self.migpal_service_fee
            + self.government_fee
            + self.relocation_cost_high
            + self.settlement_cost
            + self.legal_fee_high
        )


def build_cost_breakdown(
    *,
    family_size: int,
    government_fee: float,
    relocation_cost_low: float,
    relocation_cost_high: float,
    settlement_cost: float,
    legal_fee_low: float = 0.0,
    legal_fee_high: float = 0.0,
) -> CostBreakdown:
    if relocation_cost_low > relocation_cost_high:
        raise BudgetInvariantError("relocation_cost_low no puede ser mayor que relocation_cost_high.")
    if legal_fee_low > legal_fee_high:
        raise BudgetInvariantError("legal_fee_low no puede ser mayor que legal_fee_high.")
    for label, value in (
        ("government_fee", government_fee),
        ("relocation_cost_low", relocation_cost_low),
        ("settlement_cost", settlement_cost),
        ("legal_fee_low", legal_fee_low),
    ):
        if value < 0:
            raise BudgetInvariantError(f"{label} no puede ser negativo.")

    return CostBreakdown(
        migpal_service_fee=service_fee_for_family_size(family_size),
        government_fee=government_fee,
        relocation_cost_low=relocation_cost_low,
        relocation_cost_high=relocation_cost_high,
        settlement_cost=settlement_cost,
        legal_fee_low=legal_fee_low,
        legal_fee_high=legal_fee_high,
    )


def monthly_income_differential(*, origin_monthly_income: float, destination_monthly_income: float) -> float:
    return destination_monthly_income - origin_monthly_income


def breakeven_months(*, total_cost: float, monthly_differential: float) -> float | None:
    """Meses para recuperar `total_cost` con el diferencial mensual de
    ingresos. `None` si el diferencial no es positivo -- no hay "punto de
    equilibrio" que reportar como un número (evita devolver infinito o un
    negativo sin sentido; la responsabilidad de explicarlo es de
    `application`/adapters, no de esta función pura)."""

    if monthly_differential <= 0:
        return None
    return total_cost / monthly_differential
