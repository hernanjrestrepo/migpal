"""
Family Planning — adapters: superficie Web API (Sprint 4, Hito 5).

- 400: violación de la cascada geográfica (`FamilyPlanningInvariantError`)
  -- elegir un nivel sin haber elegido el anterior, dos respuestas del
  titular, respuesta sin `case_family_member_id` no siendo del titular.
- 404: `case_family_member_id` no pertenece al caso del usuario autenticado.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from app.auth import get_current_user
from app.db.session import get_session
from core.case_engine.application.queries import GetCaseForUserQuery, handle_get_case_for_user
from core.case_engine.infrastructure.repository import CaseRepository
from core.family_planning.application.commands import (
    AgregarOpcionCommand,
    ResponderEncuestaCommand,
    SeleccionarBarrioCommand,
    SeleccionarCiudadCommand,
    SeleccionarEstadoCommand,
    SeleccionarPaisCommand,
)
from core.family_planning.application.handlers import (
    handle_agregar_opcion,
    handle_responder_encuesta,
    handle_seleccionar_barrio,
    handle_seleccionar_ciudad,
    handle_seleccionar_estado,
    handle_seleccionar_pais,
)
from core.family_planning.application.queries import (
    ConsultarPlanificacionQuery,
    PlanificacionView,
    handle_consultar_planificacion,
)
from core.family_planning.domain.aggregates import GeographicSelection
from core.family_planning.domain.rules import FamilyPlanningInvariantError
from core.family_planning.domain.value_objects import PlaceOptionType
from core.family_planning.infrastructure.repository import (
    FamilySurveyRepository,
    GeographicSelectionRepository,
    PlaceOptionRepository,
)
from core.identity.domain.aggregates import User
from core.shared.exceptions import CaseNotFound

router = APIRouter(prefix="/v1/family-planning", tags=["family-planning"])


class GeographicSelectionRead(BaseModel):
    case_id: int
    country: str | None
    state: str | None
    city: str | None
    neighborhood: str | None


class SeleccionarPaisRequest(BaseModel):
    country: str


class SeleccionarEstadoRequest(BaseModel):
    state: str


class SeleccionarCiudadRequest(BaseModel):
    city: str


class SeleccionarBarrioRequest(BaseModel):
    neighborhood: str


class PlanificacionRead(BaseModel):
    country: str | None
    state: str | None
    city: str | None
    neighborhood: str | None
    survey_completed_count: int
    survey_total_count: int


class ResponderEncuestaRequest(BaseModel):
    case_family_member_id: int | None = None
    is_primary_applicant: bool = False
    climate_preference: str | None = None
    top_priority: str | None = None
    notes: str | None = None


class AgregarOpcionRequest(BaseModel):
    option_type: PlaceOptionType
    name: str
    website: str | None = None
    phone: str | None = None
    requirements: str | None = None
    cost_amount: float | None = None
    cost_period: str | None = None
    image_url: str | None = None


class PlaceOptionRead(BaseModel):
    id: int
    option_type: str
    name: str
    website: str | None
    phone: str | None
    requirements: str | None
    cost_amount: float | None
    cost_period: str | None
    image_url: str | None


def _to_selection_read(selection: GeographicSelection) -> GeographicSelectionRead:
    return GeographicSelectionRead(
        case_id=selection.case_id,
        country=selection.country,
        state=selection.state,
        city=selection.city,
        neighborhood=selection.neighborhood,
    )


def _to_planificacion_read(view: PlanificacionView) -> PlanificacionRead:
    return PlanificacionRead(
        country=view.country,
        state=view.state,
        city=view.city,
        neighborhood=view.neighborhood,
        survey_completed_count=view.survey_completed_count,
        survey_total_count=view.survey_total_count,
    )


def _get_case_or_404(current_user: User, session: Session):
    case_repo = CaseRepository(session)
    try:
        return handle_get_case_for_user(GetCaseForUserQuery(user_id=current_user.id), case_repo)
    except CaseNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("", response_model=PlanificacionRead)
def get_mi_planificacion(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    view = handle_consultar_planificacion(
        ConsultarPlanificacionQuery(case_id=case.id, total_family_members=len(case.family_members)),
        GeographicSelectionRepository(session),
        FamilySurveyRepository(session),
    )
    return _to_planificacion_read(view)


@router.post("/geography/country", response_model=GeographicSelectionRead)
def seleccionar_pais(
    body: SeleccionarPaisRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    selection = handle_seleccionar_pais(
        SeleccionarPaisCommand(case_id=case.id, country=body.country), GeographicSelectionRepository(session)
    )
    return _to_selection_read(selection)


@router.post("/geography/state", response_model=GeographicSelectionRead)
def seleccionar_estado(
    body: SeleccionarEstadoRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    try:
        selection = handle_seleccionar_estado(
            SeleccionarEstadoCommand(case_id=case.id, state=body.state), GeographicSelectionRepository(session)
        )
    except FamilyPlanningInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_selection_read(selection)


@router.post("/geography/city", response_model=GeographicSelectionRead)
def seleccionar_ciudad(
    body: SeleccionarCiudadRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    try:
        selection = handle_seleccionar_ciudad(
            SeleccionarCiudadCommand(case_id=case.id, city=body.city), GeographicSelectionRepository(session)
        )
    except FamilyPlanningInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_selection_read(selection)


@router.post("/geography/neighborhood", response_model=GeographicSelectionRead)
def seleccionar_barrio(
    body: SeleccionarBarrioRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    try:
        selection = handle_seleccionar_barrio(
            SeleccionarBarrioCommand(case_id=case.id, neighborhood=body.neighborhood),
            GeographicSelectionRepository(session),
        )
    except FamilyPlanningInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_selection_read(selection)


@router.post("/survey", response_model=PlanificacionRead)
def responder_encuesta(
    body: ResponderEncuestaRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)

    if body.case_family_member_id is not None and body.case_family_member_id not in {
        m.id for m in case.family_members
    }:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El caso no tiene ningún integrante con id {body.case_family_member_id}.",
        )

    try:
        handle_responder_encuesta(
            ResponderEncuestaCommand(case_id=case.id, **body.model_dump()), FamilySurveyRepository(session)
        )
    except FamilyPlanningInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    view = handle_consultar_planificacion(
        ConsultarPlanificacionQuery(case_id=case.id, total_family_members=len(case.family_members)),
        GeographicSelectionRepository(session),
        FamilySurveyRepository(session),
    )
    return _to_planificacion_read(view)


@router.post("/options", response_model=PlaceOptionRead)
def agregar_opcion(
    body: AgregarOpcionRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    option = handle_agregar_opcion(
        AgregarOpcionCommand(case_id=case.id, **body.model_dump()), PlaceOptionRepository(session)
    )
    return PlaceOptionRead(
        id=option.id, option_type=option.option_type.value, name=option.name, website=option.website,
        phone=option.phone, requirements=option.requirements, cost_amount=option.cost_amount,
        cost_period=option.cost_period, image_url=option.image_url,
    )


@router.get("/options", response_model=list[PlaceOptionRead])
def listar_opciones(
    option_type: PlaceOptionType | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    options = PlaceOptionRepository(session).list_for_case(case.id, option_type)
    return [
        PlaceOptionRead(
            id=o.id, option_type=o.option_type.value, name=o.name, website=o.website, phone=o.phone,
            requirements=o.requirements, cost_amount=o.cost_amount, cost_period=o.cost_period,
            image_url=o.image_url,
        )
        for o in options
    ]
