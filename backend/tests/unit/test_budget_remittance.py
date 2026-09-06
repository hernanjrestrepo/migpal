"""Budget — comparación de remesas (Sprint 3, Hito 5). Funciones puras, sin DB."""

import pytest

from core.budget.domain.remittance import RemittanceQuote, compare_remittance_quotes, estimate_amount_received
from core.budget.domain.rules import BudgetInvariantError


def test_estimate_amount_received_subtracts_fee_then_applies_spread():
    received = estimate_amount_received(amount=500, fee=4.2, spread_percent=0)
    assert received == pytest.approx(495.8)


def test_estimate_amount_received_applies_spread_percent():
    received = estimate_amount_received(amount=500, fee=0, spread_percent=2)
    assert received == pytest.approx(490.0)


def test_estimate_amount_received_raises_if_fee_exceeds_amount():
    with pytest.raises(BudgetInvariantError):
        estimate_amount_received(amount=10, fee=20, spread_percent=0)


@pytest.mark.parametrize("field,value", [("amount", -1), ("fee", -1), ("spread_percent", -1)])
def test_estimate_amount_received_raises_for_negative_inputs(field, value):
    kwargs = {"amount": 500, "fee": 4, "spread_percent": 1}
    kwargs[field] = value
    with pytest.raises(BudgetInvariantError):
        estimate_amount_received(**kwargs)


def test_compare_remittance_quotes_sorts_best_first():
    quotes = [
        RemittanceQuote(provider_name="Western Union", fee=8.0, spread_percent=3.5),
        RemittanceQuote(provider_name="Wise", fee=4.2, spread_percent=0),
        RemittanceQuote(provider_name="Remitly", fee=2.99, spread_percent=1.8),
    ]

    results = compare_remittance_quotes(amount=500, quotes=quotes)

    assert [r.provider_name for r in results] == ["Wise", "Remitly", "Western Union"]
    assert results[0].amount_received > results[-1].amount_received


def test_compare_remittance_quotes_raises_for_empty_list():
    with pytest.raises(BudgetInvariantError):
        compare_remittance_quotes(amount=500, quotes=[])
