"""
Marketplace — domain (Sprint 6, Hito 5): listados de servicio y
transacciones.

Incluye `CUIDADO_INFANTIL` como categoría -- decisión explícita de Hernán
(6 sept 2026): MigPAL no es una agencia de contratación ni verifica
antecedentes; la verificación de referencias es responsabilidad de la
parte contratante, con aviso explícito en el producto (ver
`domain/rules.py::LIABILITY_DISCLAIMER`)."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel

from core.marketplace.domain.value_objects import ServiceCategory, TransactionStatus


class ServiceListing(SQLModel, table=True):
    __tablename__ = "marketplace_listings"

    id: int | None = Field(default=None, primary_key=True)
    provider_user_id: int = Field(foreign_key="user.id", index=True)
    category: ServiceCategory = Field(index=True)
    title: str
    description: str | None = Field(default=None)
    price_amount: float
    price_unit: str  # "hora", "servicio", "mudanza", etc.
    city: str | None = Field(default=None, index=True)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ServiceTransaction(SQLModel, table=True):
    __tablename__ = "marketplace_transactions"

    id: int | None = Field(default=None, primary_key=True)
    listing_id: int = Field(foreign_key="marketplace_listings.id", index=True)
    buyer_user_id: int = Field(foreign_key="user.id", index=True)
    seller_user_id: int = Field(foreign_key="user.id", index=True)

    amount: float
    commission_rate: float
    commission_amount: float

    status: TransactionStatus = Field(default=TransactionStatus.PENDING, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = Field(default=None)
