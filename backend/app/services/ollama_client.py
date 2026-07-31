"""
Cliente HTTP compartido hacia Ollama (estabilización, Hito 3).

Extraído de `ai_assessment.py`/`ai_recommendation.py` cuando el duplicado se
volvió real -- `ai_assessment.py` ya anticipaba esto explícitamente (A-ADR-006):
"se revisita cuando ai_recommendation.py exista y el duplicado sea real".
Comparte solo la plomería HTTP (timeout, reintento, logging); cada servicio
conserva su propio `system prompt` y su propio mensaje de fallback -- el
contrato de cada uno sigue sin compartirse, A-ADR-006 sigue vigente.

Motivo: en la sesión de cierre de Hito 3, `tests/integration/test_recommendation_narrative_real_llm.py`
falló una vez con timeout real bajo carga (60s fijo, sin margen ni
reintento) y pasó al re-ejecutarlo aislado -- comportamiento no
determinístico bajo carga, inaceptable para un componente de producto.
Corrección: timeout configurable (`OLLAMA_TIMEOUT_SECONDS`, antes 60s fijo
en cada archivo) + un reintento controlado (`OLLAMA_MAX_ATTEMPTS`) antes de
devolver `None` -- el caller decide su propio mensaje de fallback, la
Recommendation/Assessment nunca dejan de ser válidos por esto (ver
`FALLBACK_MESSAGE` en cada servicio).

Deliberadamente NO se implementa acá: circuit breaker, cola de ejecución,
worker asíncrono. Para un solo proveedor de IA local en un backend
monolítico, timeout+reintento cubre el modo de falla real observado (
latencia variable, no caídas sostenidas). Se registra como deuda técnica
futura si el patrón de carga cambia -- ver docs/HITO_3_PROGRESS.md.
"""

from __future__ import annotations

import asyncio
import logging
import os

import httpx

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
AI_MODEL = os.getenv("AI_MODEL", "migpal:latest")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "90"))
OLLAMA_MAX_ATTEMPTS = int(os.getenv("OLLAMA_MAX_ATTEMPTS", "2"))
OLLAMA_RETRY_BACKOFF_SECONDS = 1.5


async def call_ollama(
    *,
    system: str,
    prompt: str,
    temperature: float,
    num_predict: int,
    top_p: float = 0.85,
    repeat_penalty: float = 1.2,
) -> str | None:
    """Devuelve el texto de respuesta, o `None` si se agotaron los
    reintentos -- nunca lanza. El caller decide el fallback."""

    last_error: Exception | str | None = None
    for attempt in range(1, OLLAMA_MAX_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": AI_MODEL,
                        "system": system,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": num_predict,
                            "top_p": top_p,
                            "repeat_penalty": repeat_penalty,
                        },
                    },
                )
                if response.status_code == 200:
                    text = response.json().get("response", "").strip()
                    if text:
                        return text
                    last_error = "Ollama respondió 200 con texto vacío"
                else:
                    last_error = f"Ollama error: {response.status_code}"
        except Exception as exc:
            last_error = exc

        if attempt < OLLAMA_MAX_ATTEMPTS:
            logger.warning(f"Intento {attempt}/{OLLAMA_MAX_ATTEMPTS} falló ({last_error}); reintentando...")
            await asyncio.sleep(OLLAMA_RETRY_BACKOFF_SECONDS)

    logger.error(f"Ollama agotó {OLLAMA_MAX_ATTEMPTS} intento(s): {last_error}")
    return None
