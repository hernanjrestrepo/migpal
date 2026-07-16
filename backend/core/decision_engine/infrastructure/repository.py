"""Decision Engine — infrastructure: persistencia de Assessment."""

from __future__ import annotations

from sqlmodel import Session, select

from core.decision_engine.domain.aggregates import Assessment
from core.shared.event_log import persist_event


class AssessmentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, assessment: Assessment) -> Assessment:
        self._session.add(assessment)
        self._session.commit()
        self._session.refresh(assessment)
        # Event Log persistido (Hito 2, regla 5).
        persist_event(
            self._session,
            name="AssessmentCompleted",
            payload={
                "case_id": assessment.case_id,
                "assessment_id": assessment.id,
                "score": assessment.score,
            },
        )
        return assessment

    def get_latest_for_case(self, case_id: int) -> Assessment | None:
        return self._session.exec(
            select(Assessment).where(Assessment.case_id == case_id).order_by(Assessment.id.desc())
        ).first()
