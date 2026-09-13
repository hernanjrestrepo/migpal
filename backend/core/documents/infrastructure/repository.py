"""Documents — infrastructure: persistencia (post-Hito 5)."""

from __future__ import annotations

from sqlmodel import Session, select

from core.documents.domain.aggregates import DocumentSubmission


class DocumentSubmissionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, submission: DocumentSubmission) -> DocumentSubmission:
        self._session.add(submission)
        self._session.commit()
        self._session.refresh(submission)
        return submission

    def get_by_id(self, submission_id: int) -> DocumentSubmission | None:
        return self._session.get(DocumentSubmission, submission_id)

    def list_for_case(self, case_id: int) -> list[DocumentSubmission]:
        return list(
            self._session.exec(
                select(DocumentSubmission)
                .where(DocumentSubmission.case_id == case_id)
                .order_by(DocumentSubmission.created_at.desc())
            )
        )
