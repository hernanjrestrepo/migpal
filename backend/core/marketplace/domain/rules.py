"""
Marketplace — domain: invariantes y comisión (Sprint 6, Hito 5).

`DEFAULT_COMMISSION_RATE` es un valor de partida, no una cifra ya validada
por el negocio -- a diferencia de la tarifa de MigPAL en `core/budget`
(que sí quedó fijada explícitamente en $1.000 + $200/persona), Hernán
nunca confirmó un porcentaje concreto para el Mercado. Queda como
constante fácil de cambiar en un solo lugar, no hardcodeada en el adapter.

`LIABILITY_DISCLAIMER` traduce a texto de producto la decisión de negocio
del 6 sept 2026: MigPAL es intermediario, no agencia; no verifica
antecedentes ni referencias; la verificación es responsabilidad de quien
contrata. Vive acá (no en el frontend a mano) para que sea imposible
exponer una transacción del Mercado sin que este aviso viaje con ella."""

from __future__ import annotations

from datetime import UTC, datetime

from core.marketplace.domain.aggregates import ServiceTransaction
from core.marketplace.domain.value_objects import TransactionStatus

DEFAULT_COMMISSION_RATE = 0.08

LIABILITY_DISCLAIMER = (
    "MigPAL es un intermediario, no una agencia de contratación. No verificamos "
    "antecedentes ni referencias de quienes ofrecen o contratan un servicio -- esa "
    "verificación es responsabilidad de la parte contratante. El acuerdo y su "
    "cumplimiento son exclusivamente entre las partes."
)


class MarketplaceInvariantError(ValueError):
    """Se violó una invariante de Marketplace."""


def calculate_commission(*, amount: float, commission_rate: float = DEFAULT_COMMISSION_RATE) -> float:
    if amount < 0:
        raise MarketplaceInvariantError("amount no puede ser negativo.")
    if not (0 <= commission_rate <= 1):
        raise MarketplaceInvariantError("commission_rate debe estar entre 0 y 1.")
    return amount * commission_rate


def validate_can_start_transaction(*, listing_active: bool, listing_provider_user_id: int, buyer_user_id: int) -> None:
    if not listing_active:
        raise MarketplaceInvariantError("Este listado ya no está activo.")
    if buyer_user_id == listing_provider_user_id:
        raise MarketplaceInvariantError("No podés iniciar una transacción sobre tu propio listado.")


def complete_transaction(transaction: ServiceTransaction) -> ServiceTransaction:
    if transaction.status != TransactionStatus.PENDING:
        raise MarketplaceInvariantError(f"La transacción ya está {transaction.status.value}, no PENDING.")

    transaction.status = TransactionStatus.COMPLETED
    transaction.completed_at = datetime.now(UTC)
    return transaction


def cancel_transaction(transaction: ServiceTransaction) -> ServiceTransaction:
    if transaction.status != TransactionStatus.PENDING:
        raise MarketplaceInvariantError(f"La transacción ya está {transaction.status.value}, no PENDING.")

    transaction.status = TransactionStatus.CANCELLED
    return transaction
