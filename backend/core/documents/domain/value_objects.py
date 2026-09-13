"""
Documents — domain: estados y veredicto (post-Hito 5, validación de
documentos por OCR).
"""

from __future__ import annotations

from enum import StrEnum


class DocumentReviewStatus(StrEnum):
    """El pipeline completo (guardar -> OCR -> veredicto de IA) corre de
    forma sincrónica en una sola llamada -- no hay un estado "pendiente"
    persistido, solo el resultado final de esa corrida."""

    OCR_FAILED = "OCR_FAILED"
    REVIEWED = "REVIEWED"


class ReviewVerdict(StrEnum):
    """Deliberadamente NO se llama "APPROVED"/"REJECTED" -- ver docstring
    de domain/rules.py: esto es una revisión asistida por IA, no una
    validación legal. UNCERTAIN cubre tanto "el LLM no respondió" como
    "el LLM respondió pero de forma inutilizable"."""

    LIKELY_MATCH = "LIKELY_MATCH"
    LIKELY_MISMATCH = "LIKELY_MISMATCH"
    UNCERTAIN = "UNCERTAIN"
