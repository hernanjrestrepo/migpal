"""Empleo — infrastructure: persistencia (Sprint 10b, Hito 5)."""

from __future__ import annotations

from sqlmodel import Session, select

from core.empleo.domain.aggregates import EmpleoIntegration
from core.shared.event_log import persist_event


class EmpleoIntegrationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, integration: EmpleoIntegration) -> EmpleoIntegration:
        self._session.add(integration)
        self._session.commit()
        self._session.refresh(integration)

        persist_event(
            self._session,
            name="EmpleoIntegrationConnected",
            payload={"case_id": integration.case_id, "jobxeeker_user_id": integration.jobxeeker_user_id},
        )
        return integration

    def save(self, integration: EmpleoIntegration) -> EmpleoIntegration:
        self._session.add(integration)
        self._session.commit()
        self._session.refresh(integration)
        return integration

    def get_for_case(self, case_id: int) -> EmpleoIntegration | None:
        return self._session.exec(select(EmpleoIntegration).where(EmpleoIntegration.case_id == case_id)).first()
