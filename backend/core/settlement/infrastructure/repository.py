"""Settlement — infrastructure: persistencia (Sprint 2, Hito 5)."""

from __future__ import annotations

from sqlmodel import Session, select

from core.settlement.domain.aggregates import SettlementChecklist
from core.shared.event_log import persist_event


class SettlementRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, checklist: SettlementChecklist) -> SettlementChecklist:
        self._session.add(checklist)
        self._session.commit()
        self._session.refresh(checklist)

        persist_event(
            self._session,
            name="SettlementChecklistCreated",
            payload={"case_id": checklist.case_id, "checklist_id": checklist.id, "country": checklist.country},
        )
        return checklist

    def save(self, checklist: SettlementChecklist, *, updated_item_id: int | None = None) -> SettlementChecklist:
        self._session.add(checklist)
        self._session.commit()
        self._session.refresh(checklist)

        if updated_item_id is not None:
            persist_event(
                self._session,
                name="SettlementItemStatusUpdated",
                payload={"case_id": checklist.case_id, "checklist_id": checklist.id, "item_id": updated_item_id},
            )
        return checklist

    def get_for_case(self, case_id: int) -> SettlementChecklist | None:
        return self._session.exec(
            select(SettlementChecklist).where(SettlementChecklist.case_id == case_id)
        ).first()

    def get_by_id(self, checklist_id: int) -> SettlementChecklist | None:
        return self._session.get(SettlementChecklist, checklist_id)
