"""
MigPAL AI Assessment -- resumen analítico de un perfil migratorio (A-ADR-006).

Caso de uso distinto al de `ai_brain.process_message`: acá no hay diálogo,
turnos, ni gestión de etapa -- es una sola pasada de texto a texto sobre el
perfil que ya escribió el usuario. No comparte contrato con `process_message`
a propósito (ver docs/adr/A-ADR-006-separar-casos-de-uso-llm.md).
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
AI_MODEL = os.getenv("AI_MODEL", "migpal:latest")

SYSTEM_PROMPT = (
    "Sos MigPAL, un analista migratorio. Tu única tarea es leer el perfil que te da "
    "el cliente y resumir en 3-4 líneas qué entendiste de su situación migratoria "
    "(experiencia, educación, destino, familia, finanzas). No saludes, no te "
    "presentes, no hagas preguntas -- el cliente ya escribió todo lo que sabés de él."
)

FALLBACK_MESSAGE = "No fue posible generar la reflexión del perfil en este momento."


async def summarize_profile(profile_text: str) -> str:
    """Reflexión cualitativa de un perfil migratorio -- sin estado, sin turnos."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": AI_MODEL,
                    "system": SYSTEM_PROMPT,
                    "prompt": f'Perfil del cliente: "{profile_text}"',
                    "stream": False,
                    "options": {
                        "temperature": 0.4,
                        "num_predict": 200,
                        "top_p": 0.85,
                        "repeat_penalty": 1.2,
                    },
                },
            )
            if response.status_code == 200:
                text = response.json().get("response", "").strip()
                if text:
                    return text
            else:
                logger.error(f"Ollama error en summarize_profile: {response.status_code}")
    except Exception as exc:
        logger.error(f"AI error en summarize_profile: {exc}")

    return FALLBACK_MESSAGE
