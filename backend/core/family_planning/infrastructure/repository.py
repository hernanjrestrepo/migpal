"""Family Planning — infrastructure: persistencia (Sprint 4, Hito 5)."""

from __future__ import annotations

from sqlmodel import Session, select

from core.family_planning.domain.aggregates import FamilySurveyResponse, GeographicSelection, PlaceOption
from core.family_planning.domain.value_objects import PlaceOptionType
from core.shared.event_log import persist_event


class GeographicSelectionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_or_create(self, case_id: int) -> GeographicSelection:
        existing = self.get_for_case(case_id)
        if existing is not None:
            return existing
        selection = GeographicSelection(case_id=case_id)
        self._session.add(selection)
        self._session.commit()
        self._session.refresh(selection)
        return selection

    def save(self, selection: GeographicSelection) -> GeographicSelection:
        self._session.add(selection)
        self._session.commit()
        self._session.refresh(selection)

        persist_event(
            self._session,
            name="GeographicSelectionUpdated",
            payload={
                "case_id": selection.case_id,
                "country": selection.country,
                "state": selection.state,
                "city": selection.city,
                "neighborhood": selection.neighborhood,
            },
        )
        return selection

    def get_for_case(self, case_id: int) -> GeographicSelection | None:
        return self._session.exec(
            select(GeographicSelection).where(GeographicSelection.case_id == case_id)
        ).first()


class FamilySurveyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, response: FamilySurveyResponse) -> FamilySurveyResponse:
        self._session.add(response)
        self._session.commit()
        self._session.refresh(response)

        persist_event(
            self._session,
            name="FamilySurveyResponseSubmitted",
            payload={"case_id": response.case_id, "response_id": response.id},
        )
        return response

    def get_primary_response_for_case(self, case_id: int) -> FamilySurveyResponse | None:
        return self._session.exec(
            select(FamilySurveyResponse).where(
                FamilySurveyResponse.case_id == case_id,
                FamilySurveyResponse.is_primary_applicant.is_(True),
            )
        ).first()

    def list_for_case(self, case_id: int) -> list[FamilySurveyResponse]:
        return list(
            self._session.exec(select(FamilySurveyResponse).where(FamilySurveyResponse.case_id == case_id))
        )


class PlaceOptionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, option: PlaceOption) -> PlaceOption:
        self._session.add(option)
        self._session.commit()
        self._session.refresh(option)
        return option

    def list_for_case(self, case_id: int, option_type: PlaceOptionType | None = None) -> list[PlaceOption]:
        query = select(PlaceOption).where(PlaceOption.case_id == case_id)
        if option_type is not None:
            query = query.where(PlaceOption.option_type == option_type)
        return list(self._session.exec(query))
