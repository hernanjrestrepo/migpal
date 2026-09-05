"""
Cliente LLM compartido, agnóstico de proveedor.

Reemplaza el acoplamiento directo a Ollama local (`ollama_client.py`, que
sigue existiendo como proveedor alternativo). El proveedor se elige con
`AI_PROVIDER`:

- `kimi` (default): API de Moonshot/Kimi, compatible con el formato de
  OpenAI (`POST {KIMI_BASE_URL}/chat/completions`). Ver
  https://platform.kimi.ai/docs/api/chat
- `ollama`: instancia local, delega en `ollama_client.call_ollama`.

Motivo del cambio (2026-09): el proveedor local era el cuello de botella
real del proyecto -- bajo contención de CPU en la máquina de desarrollo,
`tests/integration/test_recommendation_narrative_real_llm.py` fallaba de
forma intermitente y la suite completa llegó a tardar más de dos horas sin
terminar (ver docs/HITO_4_FINAL_CLOSE.md §6). Con Kimi, la misma llamada
responde en ~4s de forma estable.

Particularidades reales de la API de Kimi, verificadas contra el endpoint
en vivo antes de escribir este cliente (no asumidas de la documentación):

1. `kimi-k2.6` y `kimi-k3` son modelos de razonamiento: por defecto gastan
   el presupuesto de tokens en `reasoning_content` y devuelven `content`
   vacío con `finish_reason="length"`. Para redactar texto de producto
   (que es todo lo que MigPAL necesita del LLM) se desactiva el
   razonamiento con `thinking={"type": "disabled"}` -- soportado por
   `kimi-k2.6`, no por `kimi-k3`.
2. `temperature` está restringido por modelo y por modo: con razonamiento
   activo solo acepta `1`, con razonamiento desactivado solo acepta `0.6`,
   y cualquier otro valor devuelve HTTP 400. Por eso este cliente
   deliberadamente NO envía `temperature` -- deja el default del
   proveedor. La firma acepta el parámetro para no romper a los callers,
   pero solo lo reenvía al proveedor que sí lo admite (Ollama).
3. `thinking` y `reasoning_effort` son mutuamente excluyentes: enviar
   ambos devuelve HTTP 400.

Contrato idéntico al de `call_ollama`: devuelve el texto, o `None` si se
agotaron los reintentos. Nunca lanza -- el caller decide su propio mensaje
de fallback (A-ADR-006: cada caso de uso conserva su prompt y su fallback).
"""

from __future__ import annotations

import asyncio
import logging
import os

import httpx

from app.services.ollama_client import call_ollama

logger = logging.getLogger(__name__)

AI_PROVIDER = os.getenv("AI_PROVIDER", "kimi").strip().lower()
AI_MODEL = os.getenv("AI_MODEL", "kimi-k2.6")

KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.moonshot.ai/v1").rstrip("/")

LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
LLM_MAX_ATTEMPTS = int(os.getenv("LLM_MAX_ATTEMPTS", "2"))
LLM_RETRY_BACKOFF_SECONDS = 1.5

# Modelos que aceptan `thinking={"type":"disabled"}`. `kimi-k3` razona
# siempre (solo admite `reasoning_effort`), así que si se elige ese modelo
# hay que darle presupuesto de tokens suficiente para razonar Y responder.
_THINKING_TOGGLEABLE_MODELS = ("kimi-k2.6", "kimi-k2.5")


def _supports_disabling_thinking(model: str) -> bool:
    return any(model.startswith(prefix) for prefix in _THINKING_TOGGLEABLE_MODELS)


async def _call_kimi(*, system: str, prompt: str, max_tokens: int) -> str | None:
    if not KIMI_API_KEY:
        logger.error("AI_PROVIDER=kimi pero KIMI_API_KEY está vacío -- no se puede llamar al LLM.")
        return None

    payload: dict = {
        "model": AI_MODEL,
        "max_completion_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    if _supports_disabling_thinking(AI_MODEL):
        payload["thinking"] = {"type": "disabled"}

    last_error: Exception | str | None = None
    for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(timeout=LLM_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{KIMI_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {KIMI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if response.status_code == 200:
                    body = response.json()
                    choice = (body.get("choices") or [{}])[0]
                    text = (choice.get("message", {}).get("content") or "").strip()
                    if text:
                        return text
                    # Modelo de razonamiento que agotó el presupuesto pensando:
                    # no es un error de red, reintentar con el mismo presupuesto
                    # daría lo mismo -- se reporta claro para poder corregir la
                    # configuración (subir max_tokens o cambiar de modelo).
                    last_error = (
                        f"{AI_MODEL} devolvió content vacío "
                        f"(finish_reason={choice.get('finish_reason')}); "
                        "si es un modelo de razonamiento, aumentar max_tokens o usar kimi-k2.6"
                    )
                else:
                    last_error = f"Kimi HTTP {response.status_code}: {response.text[:200]}"
        except Exception as exc:  # noqa: BLE001 -- el contrato es no propagar nunca
            last_error = exc

        if attempt < LLM_MAX_ATTEMPTS:
            logger.warning(f"LLM intento {attempt}/{LLM_MAX_ATTEMPTS} falló ({last_error}); reintentando...")
            await asyncio.sleep(LLM_RETRY_BACKOFF_SECONDS)

    logger.error(f"Kimi agotó {LLM_MAX_ATTEMPTS} intento(s): {last_error}")
    return None


async def call_llm(
    *,
    system: str,
    prompt: str,
    max_tokens: int,
    temperature: float = 0.5,
) -> str | None:
    """Devuelve el texto generado, o `None` si el proveedor no respondió
    tras los reintentos configurados. Nunca lanza.

    `temperature` solo se reenvía al proveedor que lo admite (Ollama); la
    API de Kimi lo restringe por modo y devuelve 400 ante cualquier valor
    que no sea el permitido, así que allí se usa el default del proveedor
    (ver docstring del módulo, punto 2)."""

    if AI_PROVIDER == "ollama":
        return await call_ollama(
            system=system,
            prompt=prompt,
            temperature=temperature,
            num_predict=max_tokens,
        )
    return await _call_kimi(system=system, prompt=prompt, max_tokens=max_tokens)
