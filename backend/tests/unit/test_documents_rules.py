"""
Documents — dominio (post-Hito 5, validación de documentos por OCR + IA).

Sin red, sin OCR real, sin base de datos -- `build_ocr_failed_submission`/
`build_reviewed_submission` son funciones puras. Mismo espíritu que
test_recommendation_domain.py."""

import pytest

from core.documents.domain.rules import (
    OCR_FAILED_REASONING,
    DocumentInvariantError,
    build_ocr_failed_submission,
    build_reviewed_submission,
)
from core.documents.domain.value_objects import DocumentReviewStatus, ReviewVerdict


def test_build_ocr_failed_submission_has_visible_reasoning():
    """Invariante 2 (ver docstring del módulo): un veredicto -- o en este
    caso, la ausencia de uno -- nunca puede faltar su razón visible."""
    submission = build_ocr_failed_submission(
        case_id=5, document_type="Pasaporte", file_path="/data/x.jpg", mime_type="image/jpeg"
    )

    assert submission.status == DocumentReviewStatus.OCR_FAILED
    assert submission.extracted_text == ""
    assert submission.verdict is None
    assert submission.reasoning == OCR_FAILED_REASONING
    assert submission.reviewed_at is not None


def test_build_ocr_failed_submission_requires_document_type():
    with pytest.raises(DocumentInvariantError):
        build_ocr_failed_submission(case_id=5, document_type="   ", file_path="/data/x.jpg", mime_type="image/jpeg")


def test_build_ocr_failed_submission_strips_document_type():
    submission = build_ocr_failed_submission(
        case_id=5, document_type="  Pasaporte  ", file_path="/data/x.jpg", mime_type="image/jpeg"
    )
    assert submission.document_type == "Pasaporte"


def test_build_reviewed_submission_succeeds_with_valid_inputs():
    submission = build_reviewed_submission(
        case_id=5,
        document_type="Contrato de trabajo",
        file_path="/data/x.jpg",
        mime_type="image/jpeg",
        extracted_text="CONTRATO DE TRABAJO entre las partes...",
        verdict=ReviewVerdict.LIKELY_MATCH,
        reasoning="El texto menciona explícitamente un contrato de trabajo.",
        concerns=[],
    )

    assert submission.status == DocumentReviewStatus.REVIEWED
    assert submission.verdict == ReviewVerdict.LIKELY_MATCH
    assert submission.extracted_text.startswith("CONTRATO")
    assert submission.concerns == []
    assert submission.reviewed_at is not None


def test_build_reviewed_submission_requires_document_type():
    with pytest.raises(DocumentInvariantError):
        build_reviewed_submission(
            case_id=5, document_type="", file_path="/data/x.jpg", mime_type="image/jpeg",
            extracted_text="texto", verdict=ReviewVerdict.UNCERTAIN, reasoning="razón", concerns=[],
        )


def test_build_reviewed_submission_requires_non_empty_reasoning():
    """Invariante 2 -- ni siquiera un veredicto UNCERTAIN puede faltar su
    razón visible."""
    with pytest.raises(DocumentInvariantError):
        build_reviewed_submission(
            case_id=5, document_type="Pasaporte", file_path="/data/x.jpg", mime_type="image/jpeg",
            extracted_text="texto", verdict=ReviewVerdict.UNCERTAIN, reasoning="   ", concerns=[],
        )


def test_build_reviewed_submission_preserves_concerns_list():
    submission = build_reviewed_submission(
        case_id=5, document_type="Pasaporte", file_path="/data/x.jpg", mime_type="image/jpeg",
        extracted_text="texto", verdict=ReviewVerdict.LIKELY_MISMATCH,
        reasoning="No parece un pasaporte.", concerns=["No se ve número de documento", "No hay foto"],
    )
    assert submission.concerns == ["No se ve número de documento", "No hay foto"]
