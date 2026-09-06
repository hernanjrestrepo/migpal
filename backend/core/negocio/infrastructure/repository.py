"""Negocio — infrastructure: persistencia (Sprint 10, Hito 5)."""

from __future__ import annotations

from sqlmodel import Session, select

from core.negocio.domain.aggregates import NegocioIntegration
from core.shared.event_log import persist_event


class NegocioIntegrationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, integration: NegocioIntegration) -> NegocioIntegration:
        self._session.add(integration)
        self._session.commit()
        self._session.refresh(integration)

        persist_event(
            self._session,
            name="NegocioIntegrationConnected",
            payload={"case_id": integration.case_id, "adan_company_id": integration.adan_company_id},
        )
        return integration

    def save(self, integration: NegocioIntegration) -> NegocioIntegration:
        self._session.add(integration)
        self._session.commit()
        self._session.refresh(integration)
        return integration

    def get_for_case(self, case_id: int) -> NegocioIntegration | None:
        return self._session.exec(
            select(NegocioIntegration).where(NegocioIntegration.case_id == case_id)
        ).first()
