"""Family Planning — domain rules (Sprint 4, Hito 5). Funciones puras, sin DB."""

import pytest

from core.family_planning.domain.aggregates import GeographicSelection
from core.family_planning.domain.rules import (
    FamilyPlanningInvariantError,
    set_city,
    set_country,
    set_neighborhood,
    set_state,
    submit_survey_response,
)

# ---- cascada geográfica ----


def test_set_country_on_empty_selection():
    selection = GeographicSelection(case_id=5)
    set_country(selection, "Estados Unidos")
    assert selection.country == "Estados Unidos"
    assert selection.state is None


def test_set_country_resets_lower_levels():
    selection = GeographicSelection(case_id=5, country="Estados Unidos", state="Texas", city="Austin")
    set_country(selection, "Canadá")
    assert selection.country == "Canadá"
    assert selection.state is None
    assert selection.city is None
    assert selection.neighborhood is None


def test_set_state_requires_country_first():
    selection = GeographicSelection(case_id=5)
    with pytest.raises(FamilyPlanningInvariantError):
        set_state(selection, "Texas")


def test_set_state_resets_city_and_neighborhood():
    selection = GeographicSelection(case_id=5, country="Estados Unidos", city="Austin", neighborhood="North Austin")
    set_state(selection, "Texas")
    assert selection.state == "Texas"
    assert selection.city is None
    assert selection.neighborhood is None


def test_set_city_requires_state_first():
    selection = GeographicSelection(case_id=5, country="Estados Unidos")
    with pytest.raises(FamilyPlanningInvariantError):
        set_city(selection, "Austin")


def test_set_neighborhood_requires_city_first():
    selection = GeographicSelection(case_id=5, country="Estados Unidos", state="Texas")
    with pytest.raises(FamilyPlanningInvariantError):
        set_neighborhood(selection, "North Austin")


def test_full_cascade_end_to_end():
    selection = GeographicSelection(case_id=5)
    set_country(selection, "Estados Unidos")
    set_state(selection, "Texas")
    set_city(selection, "Austin")
    set_neighborhood(selection, "North Austin")
    assert (selection.country, selection.state, selection.city, selection.neighborhood) == (
        "Estados Unidos", "Texas", "Austin", "North Austin",
    )


# ---- encuesta familiar ----


def test_submit_survey_response_for_primary_applicant():
    response = submit_survey_response(
        case_id=5, case_family_member_id=None, is_primary_applicant=True,
        climate_preference="cálido", top_priority="empleo", notes=None,
        existing_primary_response=None,
    )
    assert response.completed is True
    assert response.submitted_at is not None


def test_submit_survey_response_raises_if_primary_already_responded():
    existing = submit_survey_response(
        case_id=5, case_family_member_id=None, is_primary_applicant=True,
        climate_preference=None, top_priority=None, notes=None, existing_primary_response=None,
    )
    with pytest.raises(FamilyPlanningInvariantError):
        submit_survey_response(
            case_id=5, case_family_member_id=None, is_primary_applicant=True,
            climate_preference=None, top_priority=None, notes=None, existing_primary_response=existing,
        )


def test_submit_survey_response_raises_if_not_primary_and_no_member_id():
    with pytest.raises(FamilyPlanningInvariantError):
        submit_survey_response(
            case_id=5, case_family_member_id=None, is_primary_applicant=False,
            climate_preference=None, top_priority=None, notes=None, existing_primary_response=None,
        )


def test_submit_survey_response_for_family_member():
    response = submit_survey_response(
        case_id=5, case_family_member_id=42, is_primary_applicant=False,
        climate_preference="cálido", top_priority="colegio", notes="le gusta el fútbol",
        existing_primary_response=None,
    )
    assert response.case_family_member_id == 42
    assert response.completed is True
