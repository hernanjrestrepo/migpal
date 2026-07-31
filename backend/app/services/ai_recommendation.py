"""
MigPAL AI Recommendation -- redacción narrativa de una Recommendation ya
decidida (Sprint 4, Hito 3).

Responsabilidad exclusiva: convertir una ruta ya elegida (por Decision
Engine + Policy Engine, determinístico) en una explicación en lenguaje
natural. Este servicio NO decide `primary_route`, NO modifica `fit_score`
ni `confidence` -- recibe el resultado ya calculado como texto y solo lo
redacta (mismo principio que `ai_assessment.summarize_profile`, ver
docs/adr/A-ADR-006-separar-casos-de-uso-llm.md y
docs/RECOMMENDATION_DESIGN.md §5).

Si Ollama falla, se devuelve `FALLBACK_MESSAGE` -- la Recommendation entera
sigue siendo válida (`primary_evaluation`/`rationale`/`next_step` no
dependen de esto), solo se degrada `narrative_summary`.
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
AI_MODEL = os.getenv("AI_MODEL", "migpal:latest")

SYSTEM_PROMPT = (
    "Sos MigPAL, un consultor migratorio. Ya se decidió cuál es la mejor ruta "
    "migratoria para el cliente y por qué -- tu única tarea es explicárselo en "
    "3-4 líneas, en un tono cercano y claro. NO propongas otra ruta, NO "
    "inventes requisitos ni datos que no te dieron, NO hagas preguntas -- "
    "solo redactá la decisión que ya se tomó."
)

FALLBACK_MESSAGE = "No fue posible generar la explicación narrativa en este momento."


async def generate_narrative_summary(recommendation_summary: str) -> str:
    """`recommendation_summary` ya viene armado por el caller (formateado a
    partir de la Recommendation determinística) -- este servicio no conoce
    la estructura del aggregate, solo redacta sobre el texto que recibe."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": AI_MODEL,
                    "system": SYSTEM_PROMPT,
                    "prompt": recommendation_summary,
                    "stream": False,
                    "options": {
                        "temperature": 0.5,
                        "num_predict": 220,
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
                logger.error(f"Ollama error en generate_narrative_summary: {response.status_code}")
    except Exception as exc:
        logger.error(f"AI error en generate_narrative_summary: {exc}")

    return FALLBACK_MESSAGE
