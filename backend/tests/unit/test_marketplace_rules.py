"""Marketplace — domain rules (Sprint 6, Hito 5). Funciones puras, sin DB."""

import pytest

from core.marketplace.domain.aggregates import ServiceTransaction
from core.marketplace.domain.rules import (
    LIABILITY_DISCLAIMER,
    MarketplaceInvariantError,
    calculate_commission,
    cancel_transaction,
    complete_transaction,
    validate_can_start_transaction,
)
from core.marketplace.domain.value_objects import TransactionStatus


def test_calculate_commission_applies_rate():
    assert calculate_commission(amount=100, commission_rate=0.08) == pytest.approx(8.0)


def test_calculate_commission_raises_for_negative_amount():
    with pytest.raises(MarketplaceInvariantError):
        calculate_commission(amount=-1, commission_rate=0.08)


@pytest.mark.parametrize("rate", [-0.1, 1.1])
def test_calculate_commission_raises_for_rate_outside_zero_one(rate):
    with pytest.raises(MarketplaceInvariantError):
        calculate_commission(amount=100, commission_rate=rate)


def test_validate_can_start_transaction_raises_for_inactive_listing():
    with pytest.raises(MarketplaceInvariantError):
        validate_can_start_transaction(listing_active=False, listing_provider_user_id=1, buyer_user_id=2)


def test_validate_can_start_transaction_raises_for_self_purchase():
    with pytest.raises(MarketplaceInvariantError):
        validate_can_start_transaction(listing_active=True, listing_provider_user_id=1, buyer_user_id=1)


def test_validate_can_start_transaction_allows_valid_case():
    validate_can_start_transaction(listing_active=True, listing_provider_user_id=1, buyer_user_id=2)  # no debe lanzar


def _transaction(status=TransactionStatus.PENDING):
    return ServiceTransaction(
        listing_id=1, buyer_user_id=2, seller_user_id=1, amount=100, commission_rate=0.08,
        commission_amount=8.0, status=status,
    )


def test_complete_transaction_sets_completed_and_timestamp():
    transaction = _transaction()
    result = complete_transaction(transaction)
    assert result.status == TransactionStatus.COMPLETED
    assert result.completed_at is not None


def test_complete_transaction_raises_if_not_pending():
    with pytest.raises(MarketplaceInvariantError):
        complete_transaction(_transaction(status=TransactionStatus.CANCELLED))


def test_cancel_transaction_sets_cancelled():
    result = cancel_transaction(_transaction())
    assert result.status == TransactionStatus.CANCELLED


def test_cancel_transaction_raises_if_not_pending():
    with pytest.raises(MarketplaceInvariantError):
        cancel_transaction(_transaction(status=TransactionStatus.COMPLETED))


def test_liability_disclaimer_mentions_intermediary_not_agency():
    assert "intermediario" in LIABILITY_DISCLAIMER.lower()
    assert "agencia" in LIABILITY_DISCLAIMER.lower()
