"""Budget — domain rules (Sprint 1, Hito 5). Funciones puras, sin DB."""

import pytest

from core.budget.domain.rules import (
    BASE_FEE_GROUP_SIZE,
    BASE_SERVICE_FEE_USD,
    EXTRA_PERSON_FEE_USD,
    BudgetInvariantError,
    breakeven_months,
    build_cost_breakdown,
    monthly_income_differential,
    service_fee_for_family_size,
)

# ---- service_fee_for_family_size ----


@pytest.mark.parametrize("family_size", [1, 3, BASE_FEE_GROUP_SIZE])
def test_service_fee_flat_up_to_base_group_size(family_size):
    assert service_fee_for_family_size(family_size) == BASE_SERVICE_FEE_USD


def test_service_fee_adds_per_extra_person_beyond_base_group_size():
    extra_people = 2
    expected = BASE_SERVICE_FEE_USD + extra_people * EXTRA_PERSON_FEE_USD
    assert service_fee_for_family_size(BASE_FEE_GROUP_SIZE + extra_people) == expected


def test_service_fee_raises_for_family_size_below_one():
    with pytest.raises(BudgetInvariantError):
        service_fee_for_family_size(0)


# ---- build_cost_breakdown ----


def test_build_cost_breakdown_totals_include_migpal_fee_and_all_estimates():
    breakdown = build_cost_breakdown(
        family_size=3,
        government_fee=715,
        relocation_cost_low=6450,
        relocation_cost_high=10300,
        settlement_cost=31700,
        legal_fee_low=2500,
        legal_fee_high=5000,
    )

    assert breakdown.migpal_service_fee == BASE_SERVICE_FEE_USD
    assert breakdown.total_low == pytest.approx(1000 + 715 + 6450 + 31700 + 2500)
    assert breakdown.total_high == pytest.approx(1000 + 715 + 10300 + 31700 + 5000)


def test_build_cost_breakdown_defaults_legal_fee_to_zero():
    breakdown = build_cost_breakdown(
        family_size=1,
        government_fee=100,
        relocation_cost_low=500,
        relocation_cost_high=800,
        settlement_cost=1000,
    )
    assert breakdown.legal_fee_low == 0.0
    assert breakdown.legal_fee_high == 0.0


def test_build_cost_breakdown_raises_if_relocation_range_inverted():
    with pytest.raises(BudgetInvariantError):
        build_cost_breakdown(
            family_size=1,
            government_fee=100,
            relocation_cost_low=900,
            relocation_cost_high=500,
            settlement_cost=1000,
        )


def test_build_cost_breakdown_raises_if_legal_fee_range_inverted():
    with pytest.raises(BudgetInvariantError):
        build_cost_breakdown(
            family_size=1,
            government_fee=100,
            relocation_cost_low=500,
            relocation_cost_high=800,
            settlement_cost=1000,
            legal_fee_low=5000,
            legal_fee_high=2500,
        )


def test_build_cost_breakdown_raises_for_negative_values():
    with pytest.raises(BudgetInvariantError):
        build_cost_breakdown(
            family_size=1,
            government_fee=-1,
            relocation_cost_low=500,
            relocation_cost_high=800,
            settlement_cost=1000,
        )


# ---- monthly_income_differential / breakeven_months ----


def test_monthly_income_differential_can_be_positive_or_negative():
    assert monthly_income_differential(origin_monthly_income=2200, destination_monthly_income=8700) == 6500
    assert monthly_income_differential(origin_monthly_income=8700, destination_monthly_income=2200) == -6500


def test_breakeven_months_divides_total_cost_by_positive_differential():
    assert breakeven_months(total_cost=45500, monthly_differential=6500) == pytest.approx(7.0, abs=0.01)


def test_breakeven_months_is_none_when_differential_is_zero_or_negative():
    assert breakeven_months(total_cost=45500, monthly_differential=0) is None
    assert breakeven_months(total_cost=45500, monthly_differential=-100) is None
