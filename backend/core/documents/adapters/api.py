"""
Documents — adapters: superficie Web API (post-Hito 5, validación de
documentos por OCR + IA).

- 404: caso inexistente, o sin Recommendation ACCEPTED (el checklist de
  documentos requeridos depende de la ruta aceptada -- mismo criterio que
  core/settlement).
- 400: tipo de archivo no soportado (solo imágenes en esta versión --
  PDF queda fuera de alcance, ver docstring de infrastructure/ocr_adapter.py),
  archivo más grande que el límite, o `document_type` vacío.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlmodel import Session

from app.auth import get_current_user
from app.db.session import get_session
from core.case_engine.application.queries import GetCaseForUserQuery, handle_get_case_for_user
from core.case_engine.infrastructure.repository import CaseRepository
from core.documents.application.commands import SubmitDocumentCommand
from core.documents.application.handlers import handle_submit_document
from core.documents.application.queries import ListDocumentsQuery, handle_list_documents
from core.documents.domain.aggregates import DocumentSubmission
from core.documents.domain.rules import DocumentInvariantError
from core.documents.infrastructure.ai_adapter import DocumentAIAdapter
from core.documents.infrastructure.repository import DocumentSubmissionRepository
from core.identity.domain.aggregates import User
from core.recommendation.infrastructure.repository import RecommendationRepository
from core.shared.exceptions import CaseNotFound

router = APIRouter(prefix="/v1/documents", tags=["documents"])

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


class DocumentSubmissionRead(BaseModel):
    id: int
    case_id: int
    document_type: str
    mime_type: str
    status: str
    extracted_text: str
    verdict: str | None
    reasoning: str
    concerns: list[str]
    created_at: str
    reviewed_at: str | None


def _to_read(s: DocumentSubmission) -> DocumentSubmissionRead:
    return DocumentSubmissionRead(
        id=s.id,
        case_id=s.case_id,
        document_type=s.document_type,
        mime_type=s.mime_type,
        status=s.status.value,
        extracted_text=s.extracted_text,
        verdict=s.verdict.value if s.verdict else None,
        reasoning=s.reasoning,
        concerns=s.concerns,
        created_at=s.created_at.isoformat(),
        reviewed_at=s.reviewed_at.isoformat() if s.reviewed_at else None,
    )


def _get_case_or_404(current_user: User, session: Session):
    case_repo = CaseRepository(session)
    try:
        return handle_get_case_for_user(GetCaseForUserQuery(user_id=current_user.id), case_repo)
    except CaseNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=DocumentSubmissionRead)
async def submit_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)

    recommendation = RecommendationRepository(session).get_accepted_for_case(case.id)
    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Necesitas aceptar una ruta antes de subir documentos -- los documentos requeridos dependen de la ruta.",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no soportado ({file.content_type}). Por ahora solo imágenes: JPEG, PNG o WEBP.",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo supera los 10 MB permitidos."
        )

    try:
        submission = await handle_submit_document(
            SubmitDocumentCommand(
                case_id=case.id,
                document_type=document_type,
                filename=file.filename or "documento",
                mime_type=file.content_type,
                content=content,
            ),
            DocumentSubmissionRepository(session),
            DocumentAIAdapter(),
        )
    except DocumentInvariantError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _to_read(submission)


@router.get("", response_model=list[DocumentSubmissionRead])
def list_documents(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    case = _get_case_or_404(current_user, session)
    submissions = handle_list_documents(ListDocumentsQuery(case_id=case.id), DocumentSubmissionRepository(session))
    return [_to_read(s) for s in submissions]
