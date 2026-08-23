from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.service_provider import ServiceProvider, ServiceProviderRead

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/lawyers", response_model=list[ServiceProviderRead])
def list_lawyers(
    country: str | None = Query(None),
    city: str | None = Query(None),
    verified_only: bool = Query(False),
    session: Session = Depends(get_session),
):
    """
    List immigration lawyers
    """
    query = select(ServiceProvider).where(ServiceProvider.type == "lawyer")

    if country:
        query = query.where(ServiceProvider.country == country)

    if city:
        query = query.where(ServiceProvider.city == city)

    if verified_only:
        query = query.where(ServiceProvider.verified is True)

    # Order by rating
    query = query.order_by(ServiceProvider.rating.desc())

    lawyers = session.exec(query).all()
    return lawyers


@router.get("/housing", response_model=list[ServiceProviderRead])
def list_housing(
    country: str | None = Query(None), city: str | None = Query(None), session: Session = Depends(get_session)
):
    """
    List housing services
    """
    query = select(ServiceProvider).where(ServiceProvider.type == "housing")

    if country:
        query = query.where(ServiceProvider.country == country)

    if city:
        query = query.where(ServiceProvider.city == city)

    query = query.order_by(ServiceProvider.rating.desc())

    housing = session.exec(query).all()
    return housing


@router.get("/employment", response_model=list[ServiceProviderRead])
def list_employment(
    country: str | None = Query(None), city: str | None = Query(None), session: Session = Depends(get_session)
):
    """
    List employment services and job portals
    """
    query = select(ServiceProvider).where(ServiceProvider.type == "employment")

    if country:
        query = query.where(ServiceProvider.country == country)

    if city:
        query = query.where(ServiceProvider.city == city)

    query = query.order_by(ServiceProvider.rating.desc())

    employment = session.exec(query).all()
    return employment


@router.get("/education", response_model=list[ServiceProviderRead])
def list_education(
    country: str | None = Query(None), city: str | None = Query(None), session: Session = Depends(get_session)
):
    """
    List educational institutions and services
    """
    query = select(ServiceProvider).where(ServiceProvider.type == "education")

    if country:
        query = query.where(ServiceProvider.country == country)

    if city:
        query = query.where(ServiceProvider.city == city)

    query = query.order_by(ServiceProvider.rating.desc())

    education = session.exec(query).all()
    return education


@router.get("/{service_id}", response_model=ServiceProviderRead)
def get_service_provider(service_id: int, session: Session = Depends(get_session)):
    """
    Get detailed information about a specific service provider
    """
    service = session.get(ServiceProvider, service_id)

    if not service:
        raise HTTPException(status_code=404, detail="Service provider not found")

    return service


@router.get("/", response_model=list[ServiceProviderRead])
def list_all_services(
    type: str | None = Query(None),
    country: str | None = Query(None),
    city: str | None = Query(None),
    verified_only: bool = Query(False),
    session: Session = Depends(get_session),
):
    """
    List all service providers with optional filters
    """
    query = select(ServiceProvider)

    if type:
        query = query.where(ServiceProvider.type == type)

    if country:
        query = query.where(ServiceProvider.country == country)

    if city:
        query = query.where(ServiceProvider.city == city)

    if verified_only:
        query = query.where(ServiceProvider.verified is True)

    query = query.order_by(ServiceProvider.rating.desc())

    services = session.exec(query).all()
    return services
