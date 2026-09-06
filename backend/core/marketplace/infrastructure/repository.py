"""Marketplace — infrastructure: persistencia (Sprint 6, Hito 5)."""

from __future__ import annotations

from sqlmodel import Session, select

from core.marketplace.domain.aggregates import ServiceListing, ServiceTransaction
from core.marketplace.domain.value_objects import ServiceCategory, TransactionStatus
from core.shared.event_log import persist_event


class ListingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, listing: ServiceListing) -> ServiceListing:
        self._session.add(listing)
        self._session.commit()
        self._session.refresh(listing)
        return listing

    def get_by_id(self, listing_id: int) -> ServiceListing | None:
        return self._session.get(ServiceListing, listing_id)

    def list_active(self, *, category: ServiceCategory | None = None, city: str | None = None) -> list[ServiceListing]:
        query = select(ServiceListing).where(ServiceListing.active.is_(True))
        if category is not None:
            query = query.where(ServiceListing.category == category)
        if city is not None:
            query = query.where(ServiceListing.city == city)
        return list(self._session.exec(query.order_by(ServiceListing.created_at.desc())))


class TransactionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, transaction: ServiceTransaction) -> ServiceTransaction:
        self._session.add(transaction)
        self._session.commit()
        self._session.refresh(transaction)
        return transaction

    def save(self, transaction: ServiceTransaction) -> ServiceTransaction:
        self._session.add(transaction)
        self._session.commit()
        self._session.refresh(transaction)

        if transaction.status == TransactionStatus.COMPLETED:
            persist_event(
                self._session,
                name="MarketplaceTransactionCompleted",
                payload={
                    "buyer_user_id": transaction.buyer_user_id,
                    "seller_user_id": transaction.seller_user_id,
                    "transaction_id": transaction.id,
                    "commission_amount": transaction.commission_amount,
                },
            )
        return transaction

    def get_by_id(self, transaction_id: int) -> ServiceTransaction | None:
        return self._session.get(ServiceTransaction, transaction_id)

    def list_for_user(self, user_id: int) -> list[ServiceTransaction]:
        return list(
            self._session.exec(
                select(ServiceTransaction).where(
                    (ServiceTransaction.buyer_user_id == user_id) | (ServiceTransaction.seller_user_id == user_id)
                )
            )
        )
