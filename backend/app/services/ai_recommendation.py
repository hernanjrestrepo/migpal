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

La plomería HTTP (timeout, reintento, elección de proveedor) vive en
`llm_client.py`. Si el proveedor no responde tras los reintentos
configurados, se devuelve `FALLBACK_MESSAGE` -- la Recommendation entera
sigue siendo válida (`primary_evaluation`/`rationale`/`next_step` no
dependen de esto), solo se degrada `narrative_summary`.
"""

from __future__ import annotations

from app.services.llm_client import call_llm

SYSTEM_PROMPT = (
    "Sos MigPAL, un consultor migratorio. Ya se decidió cuál es la mejor ruta "
    "migratoria para el cliente y por qué -- tu única tarea es explicárselo en "
    "3-4 líneas, en un tono cercano y claro. NO propongas otra ruta, NO "
    "inventes requisitos ni datos que no te dieron, NO hagas preguntas al "
    "cliente, NO cierres con una pregunta -- solo redactá la decisión que ya "
    "se tomó y terminá."
)

FALLBACK_MESSAGE = "No fue posible generar la explicación narrativa en este momento."


async def generate_narrative_summary(recommendation_summary: str) -> str:
    """`recommendation_summary` ya viene armado por el caller (formateado a
    partir de la Recommendation determinística) -- este servicio no conoce
    la estructura del aggregate, solo redacta sobre el texto que recibe."""
    text = await call_llm(
        system=SYSTEM_PROMPT,
        prompt=recommendation_summary,
        temperature=0.5,
        max_tokens=450,
    )
    return text or FALLBACK_MESSAGE
