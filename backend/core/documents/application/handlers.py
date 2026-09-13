"""
Documents — application: handlers (post-Hito 5).

`handle_submit_document` es el único lugar donde se orquestan las tres
piezas (storage, OCR, IA) -- `adapters/api.py` no conoce ninguna de las
tres directamente, solo llama a este handler y traduce el resultado/las
excepciones a HTTP."""

from __future__ import annotations

from core.documents.application.commands import SubmitDocumentCommand
from core.documents.domain.aggregates import DocumentSubmission
from core.documents.domain.rules import build_ocr_failed_submission, build_reviewed_submission
from core.documents.domain.value_objects import ReviewVerdict
from core.documents.infrastructure.ai_adapter import DocumentAIAdapter
from core.documents.infrastructure.ocr_adapter import OcrExtractionError, extract_text
from core.documents.infrastructure.repository import DocumentSubmissionRepository
from core.documents.infrastructure.storage import save_document_file


async def handle_submit_document(
    cmd: SubmitDocumentCommand,
    repo: DocumentSubmissionRepository,
    ai_adapter: DocumentAIAdapter,
) -> DocumentSubmission:
    file_path = save_document_file(case_id=cmd.case_id, filename=cmd.filename, content=cmd.content)

    try:
        extracted_text = extract_text(cmd.content)
    except OcrExtractionError:
        extracted_text = ""

    if not extracted_text:
        submission = build_ocr_failed_submission(
            case_id=cmd.case_id, document_type=cmd.document_type, file_path=file_path, mime_type=cmd.mime_type
        )
        return repo.add(submission)

    result = await ai_adapter.review(document_type=cmd.document_type, extracted_text=extracted_text)
    submission = build_reviewed_submission(
        case_id=cmd.case_id,
        document_type=cmd.document_type,
        file_path=file_path,
        mime_type=cmd.mime_type,
        extracted_text=extracted_text,
        verdict=ReviewVerdict(result["verdict"]),
        reasoning=result["reasoning"],
        concerns=result["concerns"],
    )
    return repo.add(submission)
