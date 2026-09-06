"""Marketplace — application: consultas (Sprint 6, Hito 5)."""

from __future__ import annotations

from dataclasses import dataclass

from core.marketplace.domain.aggregates import ServiceListing, ServiceTransaction
from core.marketplace.domain.value_objects import ServiceCategory, TransactionStatus


@dataclass(frozen=True)
class ListingView:
    id: int
    provider_user_id: int
    category: ServiceCategory
    title: str
    description: str | None
    price_amount: float
    price_unit: str
    city: str | None
    active: bool


def build_listing_view(listing: ServiceListing) -> ListingView:
    return ListingView(
        id=listing.id, provider_user_id=listing.provider_user_id, category=listing.category, title=listing.title,
        description=listing.description, price_amount=listing.price_amount, price_unit=listing.price_unit,
        city=listing.city, active=listing.active,
    )


@dataclass(frozen=True)
class TransactionView:
    id: int
    listing_id: int
    buyer_user_id: int
    seller_user_id: int
    amount: float
    commission_rate: float
    commission_amount: float
    status: TransactionStatus
    created_at: str
    completed_at: str | None


def build_transaction_view(transaction: ServiceTransaction) -> TransactionView:
    return TransactionView(
        id=transaction.id, listing_id=transaction.listing_id, buyer_user_id=transaction.buyer_user_id,
        seller_user_id=transaction.seller_user_id, amount=transaction.amount,
        commission_rate=transaction.commission_rate, commission_amount=transaction.commission_amount,
        status=transaction.status, created_at=transaction.created_at.isoformat(),
        completed_at=transaction.completed_at.isoformat() if transaction.completed_at else None,
    )
