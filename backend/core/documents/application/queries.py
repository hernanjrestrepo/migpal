"""Documents — application: consultas (post-Hito 5)."""

from __future__ import annotations

from dataclasses import dataclass

from core.documents.domain.aggregates import DocumentSubmission
from core.documents.infrastructure.repository import DocumentSubmissionRepository


@dataclass(frozen=True)
class ListDocumentsQuery:
    case_id: int


def handle_list_documents(query: ListDocumentsQuery, repo: DocumentSubmissionRepository) -> list[DocumentSubmission]:
    return repo.list_for_case(query.case_id)
