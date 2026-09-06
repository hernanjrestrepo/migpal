"""Family Planning — application: handlers (Sprint 4, Hito 5)."""

from __future__ import annotations

from core.family_planning.application.commands import (
    AgregarOpcionCommand,
    ResponderEncuestaCommand,
    SeleccionarBarrioCommand,
    SeleccionarCiudadCommand,
    SeleccionarEstadoCommand,
    SeleccionarPaisCommand,
)
from core.family_planning.domain.aggregates import GeographicSelection, PlaceOption
from core.family_planning.domain.rules import (
    set_city,
    set_country,
    set_neighborhood,
    set_state,
    submit_survey_response,
)
from core.family_planning.infrastructure.repository import (
    FamilySurveyRepository,
    GeographicSelectionRepository,
    PlaceOptionRepository,
)


def handle_seleccionar_pais(cmd: SeleccionarPaisCommand, repo: GeographicSelectionRepository) -> GeographicSelection:
    selection = repo.get_or_create(cmd.case_id)
    selection = set_country(selection, cmd.country)
    return repo.save(selection)


def handle_seleccionar_estado(cmd: SeleccionarEstadoCommand, repo: GeographicSelectionRepository) -> GeographicSelection:
    selection = repo.get_or_create(cmd.case_id)
    selection = set_state(selection, cmd.state)
    return repo.save(selection)


def handle_seleccionar_ciudad(cmd: SeleccionarCiudadCommand, repo: GeographicSelectionRepository) -> GeographicSelection:
    selection = repo.get_or_create(cmd.case_id)
    selection = set_city(selection, cmd.city)
    return repo.save(selection)


def handle_seleccionar_barrio(
    cmd: SeleccionarBarrioCommand, repo: GeographicSelectionRepository
) -> GeographicSelection:
    selection = repo.get_or_create(cmd.case_id)
    selection = set_neighborhood(selection, cmd.neighborhood)
    return repo.save(selection)


def handle_responder_encuesta(cmd: ResponderEncuestaCommand, repo: FamilySurveyRepository):
    existing_primary = repo.get_primary_response_for_case(cmd.case_id) if cmd.is_primary_applicant else None

    response = submit_survey_response(
        case_id=cmd.case_id,
        case_family_member_id=cmd.case_family_member_id,
        is_primary_applicant=cmd.is_primary_applicant,
        climate_preference=cmd.climate_preference,
        top_priority=cmd.top_priority,
        notes=cmd.notes,
        existing_primary_response=existing_primary,
    )
    return repo.add(response)


def handle_agregar_opcion(cmd: AgregarOpcionCommand, repo: PlaceOptionRepository) -> PlaceOption:
    """Sin invariantes propias -- agregar un colegio o una vivienda sugerida
    no compite con nada existente (a diferencia de la encuesta del titular,
    acá se puede sumar cuantas opciones se quiera)."""

    option = PlaceOption(
        case_id=cmd.case_id,
        option_type=cmd.option_type,
        name=cmd.name,
        website=cmd.website,
        phone=cmd.phone,
        requirements=cmd.requirements,
        cost_amount=cmd.cost_amount,
        cost_period=cmd.cost_period,
        image_url=cmd.image_url,
    )
    return repo.add(option)
