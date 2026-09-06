"""Marketplace — application: handlers (Sprint 6, Hito 5)."""

from __future__ import annotations

from core.marketplace.application.commands import (
    CancelarTransaccionCommand,
    CompletarTransaccionCommand,
    CrearListingCommand,
    IniciarTransaccionCommand,
)
from core.marketplace.domain.aggregates import ServiceListing, ServiceTransaction
from core.marketplace.domain.rules import (
    calculate_commission,
    cancel_transaction,
    complete_transaction,
    validate_can_start_transaction,
)
from core.marketplace.infrastructure.repository import ListingRepository, TransactionRepository
from core.shared.exceptions import MarketplaceListingNotFound, MarketplaceTransactionNotFound


def handle_crear_listing(cmd: CrearListingCommand, repo: ListingRepository) -> ServiceListing:
    listing = ServiceListing(
        provider_user_id=cmd.provider_user_id, category=cmd.category, title=cmd.title,
        description=cmd.description, price_amount=cmd.price_amount, price_unit=cmd.price_unit, city=cmd.city,
    )
    return repo.add(listing)


def _get_listing_or_404(listing_id: int, repo: ListingRepository) -> ServiceListing:
    listing = repo.get_by_id(listing_id)
    if listing is None:
        raise MarketplaceListingNotFound(f"No existe el listado {listing_id}.")
    return listing


def handle_iniciar_transaccion(
    cmd: IniciarTransaccionCommand, listing_repo: ListingRepository, transaction_repo: TransactionRepository
) -> ServiceTransaction:
    listing = _get_listing_or_404(cmd.listing_id, listing_repo)
    validate_can_start_transaction(
        listing_active=listing.active, listing_provider_user_id=listing.provider_user_id, buyer_user_id=cmd.buyer_user_id
    )
    commission_amount = calculate_commission(amount=cmd.amount, commission_rate=cmd.commission_rate)

    transaction = ServiceTransaction(
        listing_id=listing.id, buyer_user_id=cmd.buyer_user_id, seller_user_id=listing.provider_user_id,
        amount=cmd.amount, commission_rate=cmd.commission_rate, commission_amount=commission_amount,
    )
    return transaction_repo.add(transaction)


def _get_owned_transaction(transaction_id: int, user_id: int, repo: TransactionRepository) -> ServiceTransaction:
    transaction = repo.get_by_id(transaction_id)
    if transaction is None:
        raise MarketplaceTransactionNotFound(f"No existe la transacción {transaction_id}.")
    if user_id not in (transaction.buyer_user_id, transaction.seller_user_id):
        raise MarketplaceTransactionNotFound(f"La transacción {transaction_id} no te pertenece.")
    return transaction


def handle_completar_transaccion(cmd: CompletarTransaccionCommand, repo: TransactionRepository) -> ServiceTransaction:
    transaction = _get_owned_transaction(cmd.transaction_id, cmd.user_id, repo)
    transaction = complete_transaction(transaction)
    return repo.save(transaction)


def handle_cancelar_transaccion(cmd: CancelarTransaccionCommand, repo: TransactionRepository) -> ServiceTransaction:
    transaction = _get_owned_transaction(cmd.transaction_id, cmd.user_id, repo)
    transaction = cancel_transaction(transaction)
    return repo.save(transaction)
