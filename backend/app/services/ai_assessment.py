"""
MigPAL AI Assessment -- resumen analítico de un perfil migratorio (A-ADR-006).

Caso de uso distinto al de `ai_brain.process_message`: acá no hay diálogo,
turnos, ni gestión de etapa -- es una sola pasada de texto a texto sobre el
perfil que ya escribió el usuario. No comparte contrato con `process_message`
a propósito (ver docs/adr/A-ADR-006-separar-casos-de-uso-llm.md).

La plomería HTTP (timeout, reintento, elección de proveedor) vive en
`llm_client.py` -- este archivo solo define su propio `system prompt` y su
propio mensaje de fallback.
"""

from __future__ import annotations

from app.services.llm_client import call_llm

SYSTEM_PROMPT = (
    "Sos MigPAL, un analista migratorio. Tu única tarea es leer el perfil que te da "
    "el cliente y resumir en 3-4 líneas qué entendiste de su situación migratoria "
    "(experiencia, educación, destino, familia, finanzas). No saludes, no te "
    "presentes, no hagas preguntas -- el cliente ya escribió todo lo que sabés de él."
)

FALLBACK_MESSAGE = "No fue posible generar la reflexión del perfil en este momento."


async def summarize_profile(profile_text: str) -> str:
    """Reflexión cualitativa de un perfil migratorio -- sin estado, sin turnos."""
    text = await call_llm(
        system=SYSTEM_PROMPT,
        prompt=f'Perfil del cliente: "{profile_text}"',
        temperature=0.4,
        max_tokens=400,
    )
    return text or FALLBACK_MESSAGE
