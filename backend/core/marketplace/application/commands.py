"""Marketplace — application: comandos (Sprint 6, Hito 5)."""

from dataclasses import dataclass

from core.marketplace.domain.rules import DEFAULT_COMMISSION_RATE
from core.marketplace.domain.value_objects import ServiceCategory


@dataclass(frozen=True)
class CrearListingCommand:
    provider_user_id: int
    category: ServiceCategory
    title: str
    price_amount: float
    price_unit: str
    description: str | None = None
    city: str | None = None


@dataclass(frozen=True)
class IniciarTransaccionCommand:
    listing_id: int
    buyer_user_id: int
    amount: float
    commission_rate: float = DEFAULT_COMMISSION_RATE


@dataclass(frozen=True)
class CompletarTransaccionCommand:
    transaction_id: int
    user_id: int


@dataclass(frozen=True)
class CancelarTransaccionCommand:
    transaction_id: int
    user_id: int
