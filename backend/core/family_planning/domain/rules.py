"""
Family Planning — domain: invariantes (Sprint 4, Hito 5).

La cascada país -> estado -> ciudad -> barrio es la traducción a reglas de
negocio del pedido explícito de Hernán: "en la medida en que vayan
seleccionando un país, limita las imágenes a ese país, después al estado,
después a la ciudad, después al barrio". Acá no hay imágenes (eso es
frontend/producción, ver docstring de `domain/aggregates.py`), pero la
regla de negocio real -- no podés elegir un nivel sin haber elegido el
anterior, y cambiar un nivel invalida todo lo que dependía de él -- sí vive
acá."""

from __future__ import annotations

from datetime import UTC, datetime

from core.family_planning.domain.aggregates import FamilySurveyResponse, GeographicSelection


class FamilyPlanningInvariantError(ValueError):
    """Se violó una invariante de planificación familiar."""


def set_country(selection: GeographicSelection, country: str) -> GeographicSelection:
    """Cambiar de país invalida todo lo elegido debajo -- un estado, ciudad
    o barrio de otro país no tiene sentido de mantener."""

    selection.country = country
    selection.state = None
    selection.city = None
    selection.neighborhood = None
    selection.updated_at = datetime.now(UTC)
    return selection


def set_state(selection: GeographicSelection, state: str) -> GeographicSelection:
    if selection.country is None:
        raise FamilyPlanningInvariantError("No podés elegir un estado sin haber elegido antes el país.")

    selection.state = state
    selection.city = None
    selection.neighborhood = None
    selection.updated_at = datetime.now(UTC)
    return selection


def set_city(selection: GeographicSelection, city: str) -> GeographicSelection:
    if selection.state is None:
        raise FamilyPlanningInvariantError("No podés elegir una ciudad sin haber elegido antes el estado.")

    selection.city = city
    selection.neighborhood = None
    selection.updated_at = datetime.now(UTC)
    return selection


def set_neighborhood(selection: GeographicSelection, neighborhood: str) -> GeographicSelection:
    if selection.city is None:
        raise FamilyPlanningInvariantError("No podés elegir un barrio sin haber elegido antes la ciudad.")

    selection.neighborhood = neighborhood
    selection.updated_at = datetime.now(UTC)
    return selection


def submit_survey_response(
    *,
    case_id: int,
    case_family_member_id: int | None,
    is_primary_applicant: bool,
    climate_preference: str | None,
    top_priority: str | None,
    notes: str | None,
    existing_primary_response: FamilySurveyResponse | None,
) -> FamilySurveyResponse:
    """Invariante: como máximo una respuesta del titular por caso (el
    titular no es un CaseFamilyMember, así que no hay una FK que lo impida
    por construcción -- ver docstring de domain/aggregates.py)."""

    if is_primary_applicant and existing_primary_response is not None:
        raise FamilyPlanningInvariantError(f"El caso {case_id} ya tiene una respuesta del titular.")
    if not is_primary_applicant and case_family_member_id is None:
        raise FamilyPlanningInvariantError(
            "Una respuesta que no es del titular necesita un case_family_member_id."
        )

    return FamilySurveyResponse(
        case_id=case_id,
        case_family_member_id=case_family_member_id,
        is_primary_applicant=is_primary_applicant,
        climate_preference=climate_preference,
        top_priority=top_priority,
        notes=notes,
        completed=True,
        submitted_at=datetime.now(UTC),
    )
