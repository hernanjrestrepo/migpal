"""
Documents — domain: Aggregate Root DocumentSubmission (post-Hito 5).

Mismo criterio que el resto del proyecto: la clase de dominio y el mapeo
ORM son la misma clase. `concerns` se guarda como JSON crudo (lista de
strings), mismo patrón que `Assessment.findings`."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import JSON as SQLModelJSON
from sqlmodel import Column, Field, SQLModel

from core.documents.domain.value_objects import DocumentReviewStatus, ReviewVerdict


class DocumentSubmission(SQLModel, table=True):
    __tablename__ = "document_submissions"

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="migration_cases.id", index=True)

    document_type: str
    file_path: str
    mime_type: str

    status: DocumentReviewStatus = Field(index=True)
    extracted_text: str = Field(default="")

    verdict: ReviewVerdict | None = Field(default=None)
    reasoning: str = Field(default="")
    concerns: list[str] = Field(default_factory=list, sa_column=Column(SQLModelJSON))

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reviewed_at: datetime | None = Field(default=None)
