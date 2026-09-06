"""Budget — cotizador de traslado (Sprint 3, Hito 5). Funciones puras, sin DB."""

import pytest

from core.budget.domain.relocation import RelocationMode, estimate_relocation_cost
from core.budget.domain.rules import BudgetInvariantError


def _estimate(**overrides):
    base = dict(
        family_size=3,
        mode=RelocationMode.AEREO,
        flight_cost_per_person_low=1000,
        flight_cost_per_person_high=1300,
        base_cargo_cost_low=2800,
        base_cargo_cost_high=5500,
    )
    base.update(overrides)
    return estimate_relocation_cost(**base)


def test_flight_cost_scales_with_family_size():
    estimate = _estimate(family_size=3, flight_cost_per_person_low=1000, flight_cost_per_person_high=1300)
    assert estimate.flight_cost_low == 3000
    assert estimate.flight_cost_high == 3900


def test_maritimo_applies_reduced_cargo_factor():
    aereo = _estimate(mode=RelocationMode.AEREO)
    maritimo = _estimate(mode=RelocationMode.MARITIMO)
    assert maritimo.cargo_cost_low == pytest.approx(aereo.cargo_cost_low * 0.55)
    assert maritimo.cargo_cost_high == pytest.approx(aereo.cargo_cost_high * 0.55)


def test_sin_menaje_has_zero_cargo_cost():
    estimate = _estimate(mode=RelocationMode.SIN_MENAJE)
    assert estimate.cargo_cost_low == 0
    assert estimate.cargo_cost_high == 0


def test_insurance_is_a_percentage_of_flight_plus_cargo():
    estimate = _estimate()
    subtotal_low = estimate.flight_cost_low + estimate.cargo_cost_low
    subtotal_high = estimate.flight_cost_high + estimate.cargo_cost_high
    assert estimate.insurance_low == pytest.approx(subtotal_low * 0.06)
    assert estimate.insurance_high == pytest.approx(subtotal_high * 0.08)


def test_total_sums_flight_cargo_and_insurance():
    estimate = _estimate()
    assert estimate.total_low == pytest.approx(
        estimate.flight_cost_low + estimate.cargo_cost_low + estimate.insurance_low
    )
    assert estimate.total_high == pytest.approx(
        estimate.flight_cost_high + estimate.cargo_cost_high + estimate.insurance_high
    )


def test_raises_for_family_size_below_one():
    with pytest.raises(BudgetInvariantError):
        _estimate(family_size=0)


def test_raises_for_inverted_flight_cost_range():
    with pytest.raises(BudgetInvariantError):
        _estimate(flight_cost_per_person_low=2000, flight_cost_per_person_high=100)


def test_raises_for_inverted_cargo_cost_range():
    with pytest.raises(BudgetInvariantError):
        _estimate(base_cargo_cost_low=9000, base_cargo_cost_high=100)
