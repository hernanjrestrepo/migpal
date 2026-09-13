"""
MigPAL AI Documents -- veredicto asistido por IA sobre un documento
migratorio subido por el usuario (post-Hito 5, validación de documentos
por OCR + IA).

A diferencia de `ai_recommendation.py` (el LLM solo redacta una decisión
ya tomada por reglas determinísticas), acá el LLM SÍ es quien juzga si el
texto extraído por OCR es consistente con el tipo de documento declarado
-- una excepción deliberada y acotada, ver docstring de
`core/documents/domain/rules.py` para el razonamiento completo y sus tres
límites duros.

Kimi no siempre devuelve JSON limpio pese a la instrucción (mismo hallazgo
que ADAN con su modelo local, ver core/negocio/infrastructure/adan_client.py)
-- `_parse_verdict` nunca lanza, siempre degrada a UNCERTAIN con una razón
visible si la respuesta no se puede interpretar."""

from __future__ import annotations

import json
import logging

from app.services.llm_client import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Sos un asistente de revisión documental para trámites migratorios. Te "
    "dan el tipo de documento que el usuario dice haber subido y el texto "
    "que un OCR extrajo de la imagen. Tu única tarea es evaluar si el "
    "contenido es razonablemente consistente con ese tipo de documento -- "
    "NO sos un abogado, NO certificás validez legal, NO inventés requisitos "
    "que no estén en el texto ni asumás datos que no aparecen. "
    'Respondé EXCLUSIVAMENTE con un JSON de esta forma exacta, sin texto '
    'antes ni después: {"verdict": "LIKELY_MATCH" o "LIKELY_MISMATCH", '
    '"reasoning": "una frase en español explicando por qué", "concerns": '
    '["lista corta y concreta de lo que falta o no cuadra -- puede ir vacía"]}'
)

FALLBACK_REASONING = (
    "No fue posible completar la revisión asistida por IA en este momento "
    "-- el documento quedó guardado, un humano puede revisarlo."
)

NO_TEXT_REASONING = (
    "El OCR no pudo extraer texto legible de esta imagen -- probá con una "
    "foto más clara, con mejor luz y sin recortar el documento."
)

_VALID_VERDICTS = ("LIKELY_MATCH", "LIKELY_MISMATCH")


def _parse_verdict(raw: str | None) -> dict:
    if not raw:
        return {"verdict": "UNCERTAIN", "reasoning": FALLBACK_REASONING, "concerns": []}

    # Kimi a veces envuelve el JSON en fences de markdown pese a la
    # instrucción de no hacerlo -- se despoja antes de parsear.
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        verdict = data.get("verdict")
        if verdict not in _VALID_VERDICTS:
            verdict = "UNCERTAIN"
        reasoning = str(data.get("reasoning") or "").strip() or FALLBACK_REASONING
        concerns_raw = data.get("concerns") or []
        concerns = [str(c) for c in concerns_raw] if isinstance(concerns_raw, list) else []
        return {"verdict": verdict, "reasoning": reasoning, "concerns": concerns}
    except (json.JSONDecodeError, AttributeError, TypeError) as exc:
        logger.warning(f"Veredicto de documento no interpretable como JSON: {exc}. Texto crudo: {raw[:200]!r}")
        return {"verdict": "UNCERTAIN", "reasoning": FALLBACK_REASONING, "concerns": []}


async def generate_document_verdict(*, document_type: str, extracted_text: str) -> dict:
    """Devuelve `{"verdict": ..., "reasoning": ..., "concerns": [...]}`.
    Nunca lanza (mismo contrato que `generate_narrative_summary`): un LLM
    caído o una respuesta no parseable degrada a UNCERTAIN, nunca bloquea
    que el documento quede guardado."""

    if not extracted_text.strip():
        return {"verdict": "UNCERTAIN", "reasoning": NO_TEXT_REASONING, "concerns": []}

    prompt = (
        f"Tipo de documento declarado por el usuario: {document_type}\n\n"
        f"Texto extraído por OCR:\n{extracted_text[:4000]}"
    )
    raw = await call_llm(system=SYSTEM_PROMPT, prompt=prompt, max_tokens=400)
    return _parse_verdict(raw)
