"""
Documents — domain: construcción de una revisión de documento (post-Hito 5,
validación de documentos por OCR + IA).

Excepción deliberada y acotada a la regla "el LLM nunca decide" (Handbook,
heredada explícitamente por Decision Engine/Policy Engine/Recommendation
-- ver docs/RECOMMENDATION_DESIGN.md §5). Ahí la regla existe porque SÍ hay
una alternativa determinística (reglas explícitas de matching perfil↔visa).
Acá no la hay: decidir si un párrafo de texto OCR "parece" un contrato de
trabajo o un certificado de antecedentes es un juicio sobre contenido no
estructurado que ninguna regla determinística razonable puede reemplazar
-- instrucción explícita de Hernán (7 sept 2026): "para validación de
documentos bajate una librería de OCR y ya", aceptando el LLM como la pieza
de juicio, no como redactor de una decisión ya tomada.

Esto NO se maneja como una excepción silenciosa. Tres límites duros, todos
reflejados en el modelo y expuestos al usuario, nunca solo en el prompt:

1. El veredicto se llama `ReviewVerdict` (LIKELY_MATCH/LIKELY_MISMATCH/
   UNCERTAIN), nunca "aprobado"/"rechazado" -- es una revisión asistida,
   no una validación legal (Principio 4 del Blueprint: ningún componente
   de IA se hace pasar por un profesional habilitado).
2. `reasoning` nunca puede faltar -- ni siquiera cuando el LLM falla
   (Principio 1: la IA explica, nunca oculta el "por qué"). Un veredicto
   sin razón visible es exactamente el "68/100 sin explicación" que el
   Blueprint nombra como el problema original a evitar.
3. Un fallo del LLM (timeout, respuesta no parseable) degrada a UNCERTAIN
   con una razón visible -- nunca bloquea que el documento quede guardado,
   nunca se disfraza de LIKELY_MATCH ni de LIKELY_MISMATCH por defecto.

Funciones puras -- reciben el resultado ya calculado (OCR determinístico,
veredicto de IA no determinístico) y solo arman el aggregate. La decisión
de qué hacer si el OCR falla vive en application/handlers.py, no acá."""

from __future__ import annotations

from datetime import UTC, datetime

from core.documents.domain.aggregates import DocumentSubmission
from core.documents.domain.value_objects import DocumentReviewStatus, ReviewVerdict

OCR_FAILED_REASONING = (
    "No pudimos leer texto en esta imagen -- probá con una foto más clara, "
    "con mejor luz y sin recortar el documento."
)


class DocumentInvariantError(ValueError):
    """Entrada inválida para registrar una revisión de documento."""


def _require_document_type(document_type: str) -> str:
    cleaned = document_type.strip()
    if not cleaned:
        raise DocumentInvariantError("document_type no puede estar vacío.")
    return cleaned


def build_ocr_failed_submission(
    *, case_id: int, document_type: str, file_path: str, mime_type: str
) -> DocumentSubmission:
    """El OCR no encontró texto legible -- invariante 3 (nunca bloquear el
    guardado): el documento queda registrado igual, con su propia razón
    visible, para que el usuario sepa que tiene que volver a intentarlo."""

    return DocumentSubmission(
        case_id=case_id,
        document_type=_require_document_type(document_type),
        file_path=file_path,
        mime_type=mime_type,
        status=DocumentReviewStatus.OCR_FAILED,
        extracted_text="",
        reasoning=OCR_FAILED_REASONING,
        reviewed_at=datetime.now(UTC),
    )


def build_reviewed_submission(
    *,
    case_id: int,
    document_type: str,
    file_path: str,
    mime_type: str,
    extracted_text: str,
    verdict: ReviewVerdict,
    reasoning: str,
    concerns: list[str],
) -> DocumentSubmission:
    if not reasoning.strip():
        raise DocumentInvariantError("reasoning no puede estar vacío (invariante 2).")

    return DocumentSubmission(
        case_id=case_id,
        document_type=_require_document_type(document_type),
        file_path=file_path,
        mime_type=mime_type,
        status=DocumentReviewStatus.REVIEWED,
        extracted_text=extracted_text,
        verdict=verdict,
        reasoning=reasoning,
        concerns=list(concerns),
        reviewed_at=datetime.now(UTC),
    )
