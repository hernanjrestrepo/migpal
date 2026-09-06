"""
Budget — domain: cotizador de traslado (Sprint 3, Hito 5).

Mismo principio que `domain/rules.py`: los costos base de vuelo y de envío
de menaje NO se hardcodean acá -- varían por temporada, ruta y proveedor
mucho más rápido de lo que este código se actualizaría, así que serían
números inventados con apariencia de dato verificado. Quien llama aporta
esos costos base (hoy el usuario a mano, mañana podría ser una cotización
real de una API de vuelos/mudanzas); este módulo solo aplica la aritmética
determinística: escala por integrantes, aplica el factor de modo de envío,
y calcula el seguro como un rango sobre el subtotal.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from core.budget.domain.rules import BudgetInvariantError

INSURANCE_RATE_LOW = 0.06
INSURANCE_RATE_HIGH = 0.08


class RelocationMode(StrEnum):
    AEREO = "AEREO"
    MARITIMO = "MARITIMO"
    SIN_MENAJE = "SIN_MENAJE"


# Proporción del costo de envío de menaje que aplica según el modo elegido
# -- marítimo es más barato que aéreo, sin menaje no paga envío de carga.
CARGO_FACTOR_BY_MODE: dict[RelocationMode, float] = {
    RelocationMode.AEREO: 1.0,
    RelocationMode.MARITIMO: 0.55,
    RelocationMode.SIN_MENAJE: 0.0,
}


@dataclass(frozen=True)
class RelocationEstimate:
    flight_cost_low: float
    flight_cost_high: float
    cargo_cost_low: float
    cargo_cost_high: float
    insurance_low: float
    insurance_high: float

    @property
    def total_low(self) -> float:
        return self.flight_cost_low + self.cargo_cost_low + self.insurance_low

    @property
    def total_high(self) -> float:
        return self.flight_cost_high + self.cargo_cost_high + self.insurance_high


def estimate_relocation_cost(
    *,
    family_size: int,
    mode: RelocationMode,
    flight_cost_per_person_low: float,
    flight_cost_per_person_high: float,
    base_cargo_cost_low: float,
    base_cargo_cost_high: float,
) -> RelocationEstimate:
    if family_size < 1:
        raise BudgetInvariantError("El grupo familiar debe tener al menos 1 persona.")
    if flight_cost_per_person_low > flight_cost_per_person_high:
        raise BudgetInvariantError("flight_cost_per_person_low no puede ser mayor que flight_cost_per_person_high.")
    if base_cargo_cost_low > base_cargo_cost_high:
        raise BudgetInvariantError("base_cargo_cost_low no puede ser mayor que base_cargo_cost_high.")
    for label, value in (
        ("flight_cost_per_person_low", flight_cost_per_person_low),
        ("base_cargo_cost_low", base_cargo_cost_low),
    ):
        if value < 0:
            raise BudgetInvariantError(f"{label} no puede ser negativo.")

    flight_low = flight_cost_per_person_low * family_size
    flight_high = flight_cost_per_person_high * family_size

    factor = CARGO_FACTOR_BY_MODE[mode]
    cargo_low = base_cargo_cost_low * factor
    cargo_high = base_cargo_cost_high * factor

    insurance_low = (flight_low + cargo_low) * INSURANCE_RATE_LOW
    insurance_high = (flight_high + cargo_high) * INSURANCE_RATE_HIGH

    return RelocationEstimate(
        flight_cost_low=flight_low,
        flight_cost_high=flight_high,
        cargo_cost_low=cargo_low,
        cargo_cost_high=cargo_high,
        insurance_low=insurance_low,
        insurance_high=insurance_high,
    )
