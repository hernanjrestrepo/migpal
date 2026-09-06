"""
Marketplace — adapters: superficie Web API (Sprint 6, Hito 5).

`GET /v1/marketplace/categories` devuelve el catálogo fijo de categorías
(incluye CUIDADO_INFANTIL) junto con `LIABILITY_DISCLAIMER` -- el aviso de
que MigPAL es intermediario, no agencia, viaja con el catálogo mismo, no
depende de que el frontend se acuerde de mostrarlo.

- 404: listado o transacción inexistente (o transacción que no te pertenece).
- 409: invariante de Marketplace (listado inactivo, comprar tu propio
  listado, completar/cancelar una transacción que no está PENDING).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.auth import get_current_user
from app.db.session import get_session
from core.identity.domain.aggregates import User
from core.marketplace.application.commands import (
    CancelarTransaccionCommand,
    CompletarTransaccionCommand,
    CrearListingCommand,
    IniciarTransaccionCommand,
)
from core.marketplace.application.handlers import (
    handle_cancelar_transaccion,
    handle_completar_transaccion,
    handle_crear_listing,
    handle_iniciar_transaccion,
)
from core.marketplace.application.queries import (
    ListingView,
    TransactionView,
    build_listing_view,
    build_transaction_view,
)
from core.marketplace.domain.rules import (
    DEFAULT_COMMISSION_RATE,
    LIABILITY_DISCLAIMER,
    MarketplaceInvariantError,
)
from core.marketplace.domain.value_objects import ServiceCategory
from core.marketplace.infrastructure.repository import ListingRepository, TransactionRepository
from core.shared.exceptions import MarketplaceListingNotFound, MarketplaceTransactionNotFound

router = APIRouter(prefix="/v1/marketplace", tags=["marketplace"])


class CategoriesRead(BaseModel):
    categories: list[str]
    disclaimer: str


@router.get("/categories", response_model=CategoriesRead)
def listar_categorias():
    return CategoriesRead(categories=[c.value for c in ServiceCategory], disclaimer=LIABILITY_DISCLAIMER)


class CrearListingRequest(BaseModel):
    category: ServiceCategory
    title: str
    price_amount: float
    price_unit: str
    description: str | None = None
    city: str | None = None


class ListingRead(BaseModel):
    id: int
    provider_user_id: int
    category: str
    title: str
    description: str | None
    price_amount: float
    price_unit: str
    city: str | None
    active: bool
    disclaimer: str


def _to_listing_read(view: ListingView) -> ListingRead:
    return ListingRead(
        id=view.id, provider_user_id=view.provider_user_id, category=view.category.value, title=view.title,
        description=view.description, price_amount=view.price_amount, price_unit=view.price_unit,
        city=view.city, active=view.active, disclaimer=LIABILITY_DISCLAIMER,
    )


@router.post("/listings", response_model=ListingRead)
def crear_listing(
    body: CrearListingRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    listing = handle_crear_listing(
        CrearListingCommand(provider_user_id=current_user.id, **body.model_dump()), ListingRepository(session)
    )
    return _to_listing_read(build_listing_view(listing))


@router.get("/listings", response_model=list[ListingRead])
def listar_listings(
    category: ServiceCategory | None = None,
    city: str | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    listings = ListingRepository(session).list_active(category=category, city=city)
    return [_to_listing_read(build_listing_view(item)) for item in listings]


class IniciarTransaccionRequest(BaseModel):
    listing_id: int
    amount: float
    commission_rate: float = DEFAULT_COMMISSION_RATE


class TransactionRead(BaseModel):
    id: int
    listing_id: int
    buyer_user_id: int
    seller_user_id: int
    amount: float
    commission_rate: float
    commission_amount: float
    status: str
    created_at: str
    completed_at: str | None


def _to_transaction_read(view: TransactionView) -> TransactionRead:
    return TransactionRead(
        id=view.id, listing_id=view.listing_id, buyer_user_id=view.buyer_user_id, seller_user_id=view.seller_user_id,
        amount=view.amount, commission_rate=view.commission_rate, commission_amount=view.commission_amount,
        status=view.status.value, created_at=view.created_at, completed_at=view.completed_at,
    )


@router.post("/transactions", response_model=TransactionRead)
def iniciar_transaccion(
    body: IniciarTransaccionRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        transaction = handle_iniciar_transaccion(
            IniciarTransaccionCommand(buyer_user_id=current_user.id, **body.model_dump()),
            ListingRepository(session), TransactionRepository(session),
        )
    except MarketplaceListingNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MarketplaceInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_transaction_read(build_transaction_view(transaction))


@router.get("/transactions", response_model=list[TransactionRead])
def listar_mis_transacciones(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    transactions = TransactionRepository(session).list_for_user(current_user.id)
    return [_to_transaction_read(build_transaction_view(t)) for t in transactions]


@router.post("/transactions/{transaction_id}/complete", response_model=TransactionRead)
def completar_transaccion(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        transaction = handle_completar_transaccion(
            CompletarTransaccionCommand(transaction_id=transaction_id, user_id=current_user.id),
            TransactionRepository(session),
        )
    except MarketplaceTransactionNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MarketplaceInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_transaction_read(build_transaction_view(transaction))


@router.post("/transactions/{transaction_id}/cancel", response_model=TransactionRead)
def cancelar_transaccion(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        transaction = handle_cancelar_transaccion(
            CancelarTransaccionCommand(transaction_id=transaction_id, user_id=current_user.id),
            TransactionRepository(session),
        )
    except MarketplaceTransactionNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MarketplaceInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_transaction_read(build_transaction_view(transaction))
