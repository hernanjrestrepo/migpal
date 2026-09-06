"""
Budget — infrastructure: persistencia (Sprint 1, Hito 5).

Historial append-only -- `add()` siempre inserta una fila nueva, nunca hay
`save()`/update (ver docstring de `domain/aggregates.py::BudgetEstimate`).
"""

from __future__ import annotations

from sqlmodel import Session, select

from core.budget.domain.aggregates import BudgetEstimate
from core.shared.event_log import persist_event


class BudgetRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, estimate: BudgetEstimate) -> BudgetEstimate:
        self._session.add(estimate)
        self._session.commit()
        self._session.refresh(estimate)

        persist_event(
            self._session,
            name="BudgetEstimateCalculated",
            payload={"case_id": estimate.case_id, "budget_estimate_id": estimate.id},
        )
        return estimate

    def get_latest_for_case(self, case_id: int) -> BudgetEstimate | None:
        return self._session.exec(
            select(BudgetEstimate).where(BudgetEstimate.case_id == case_id).order_by(BudgetEstimate.id.desc())
        ).first()
