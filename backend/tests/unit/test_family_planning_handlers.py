"""
Family Planning — application handlers (Sprint 4, Hito 5).

Repositorios en memoria, mismo criterio que
tests/unit/test_execution_plan_handlers.py -- sin DB.
"""

import pytest

from core.family_planning.application.commands import (
    ResponderEncuestaCommand,
    SeleccionarCiudadCommand,
    SeleccionarEstadoCommand,
    SeleccionarPaisCommand,
)
from core.family_planning.application.handlers import (
    handle_responder_encuesta,
    handle_seleccionar_ciudad,
    handle_seleccionar_estado,
    handle_seleccionar_pais,
)
from core.family_planning.application.queries import (
    ConsultarPlanificacionQuery,
    handle_consultar_planificacion,
)
from core.family_planning.domain.aggregates import GeographicSelection
from core.family_planning.domain.rules import FamilyPlanningInvariantError


class _InMemoryGeoRepository:
    def __init__(self):
        self._by_case = {}
        self._next_id = 1

    def get_or_create(self, case_id):
        if case_id not in self._by_case:
            selection = GeographicSelection(case_id=case_id)
            selection.id = self._next_id
            self._next_id += 1
            self._by_case[case_id] = selection
        return self._by_case[case_id]

    def save(self, selection):
        self._by_case[selection.case_id] = selection
        return selection

    def get_for_case(self, case_id):
        return self._by_case.get(case_id)


class _InMemorySurveyRepository:
    def __init__(self):
        self._responses = []
        self._next_id = 1

    def add(self, response):
        response.id = self._next_id
        self._next_id += 1
        self._responses.append(response)
        return response

    def get_primary_response_for_case(self, case_id):
        return next(
            (r for r in self._responses if r.case_id == case_id and r.is_primary_applicant), None
        )

    def list_for_case(self, case_id):
        return [r for r in self._responses if r.case_id == case_id]


def test_handle_seleccionar_pais_creates_selection():
    repo = _InMemoryGeoRepository()
    selection = handle_seleccionar_pais(SeleccionarPaisCommand(case_id=5, country="Canadá"), repo)
    assert selection.country == "Canadá"


def test_handle_seleccionar_estado_raises_without_country():
    repo = _InMemoryGeoRepository()
    with pytest.raises(FamilyPlanningInvariantError):
        handle_seleccionar_estado(SeleccionarEstadoCommand(case_id=5, state="Ontario"), repo)


def test_handle_seleccionar_ciudad_after_country_and_state():
    repo = _InMemoryGeoRepository()
    handle_seleccionar_pais(SeleccionarPaisCommand(case_id=5, country="Canadá"), repo)
    handle_seleccionar_estado(SeleccionarEstadoCommand(case_id=5, state="Ontario"), repo)
    selection = handle_seleccionar_ciudad(SeleccionarCiudadCommand(case_id=5, city="Toronto"), repo)
    assert selection.city == "Toronto"


def test_handle_responder_encuesta_and_consultar_planificacion_tracks_completion():
    geo_repo = _InMemoryGeoRepository()
    survey_repo = _InMemorySurveyRepository()
    handle_seleccionar_pais(SeleccionarPaisCommand(case_id=5, country="Canadá"), geo_repo)

    handle_responder_encuesta(
        ResponderEncuestaCommand(case_id=5, case_family_member_id=None, is_primary_applicant=True), survey_repo
    )
    handle_responder_encuesta(
        ResponderEncuestaCommand(case_id=5, case_family_member_id=7, is_primary_applicant=False), survey_repo
    )

    view = handle_consultar_planificacion(
        ConsultarPlanificacionQuery(case_id=5, total_family_members=2), geo_repo, survey_repo
    )

    assert view.country == "Canadá"
    assert view.survey_completed_count == 2
    assert view.survey_total_count == 3  # 2 family members + el titular


def test_handle_responder_encuesta_raises_for_second_primary_response():
    survey_repo = _InMemorySurveyRepository()
    handle_responder_encuesta(
        ResponderEncuestaCommand(case_id=5, case_family_member_id=None, is_primary_applicant=True), survey_repo
    )
    with pytest.raises(FamilyPlanningInvariantError):
        handle_responder_encuesta(
            ResponderEncuestaCommand(case_id=5, case_family_member_id=None, is_primary_applicant=True), survey_repo
        )
