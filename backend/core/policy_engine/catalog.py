"""
Policy Engine — catálogo de rutas migratorias (Sprint 3, Hito 3).

Placeholder deliberadamente simple, mismo criterio que
`SIGNAL_KEYWORDS`/`BASE_SCORE` en `decision_engine/infrastructure/scoring.py`:
un puñado de rutas hardcodeadas, no una base de conocimiento real. NO es
asesoría migratoria -- los `required_documents`/`strengths_hint`/`risks_hint`
son genéricos, no verificados contra requisitos legales reales de ningún
país. El diseño (docs/RECOMMENDATION_DESIGN.md §3) ya anticipa que esto se
reemplaza por la Knowledge Base real (RAG, docs/RAG_PIPELINE.md) sin cambiar
el contrato de `evaluate_candidate_routes` -- ver policy_engine/rules.py.

`required_signals` usa el mismo vocabulario que
`decision_engine.infrastructure.scoring.SIGNAL_KEYWORDS`
(experience/education/destination/family/financial).
"""

from __future__ import annotations

from typing import TypedDict


class RouteCatalogEntry(TypedDict):
    visa_type: str
    country: str
    required_signals: list[str]
    required_documents: list[str]
    strengths_hint: str
    risks_hint: str


ROUTE_CATALOG: list[RouteCatalogEntry] = [
    {
        "visa_type": "O-1",
        "country": "Estados Unidos",
        "required_signals": ["experience", "education"],
        "required_documents": ["CV detallado", "Cartas de recomendación", "Evidencia de logros documentados"],
        "strengths_hint": "Perfil con trayectoria y formación documentable.",
        "risks_hint": "Requiere evidencia de logros extraordinarios, no solo experiencia general.",
    },
    {
        "visa_type": "Express Entry",
        "country": "Canadá",
        "required_signals": ["experience"],
        "required_documents": ["CV", "Certificado de idioma", "Evaluación de credenciales educativas"],
        "strengths_hint": "Sistema por puntos que valora experiencia y educación combinadas.",
        "risks_hint": "El resultado depende del puntaje relativo frente a otros candidatos del sistema.",
    },
    {
        "visa_type": "Visado de Trabajador Cualificado",
        "country": "España",
        "required_signals": ["experience"],
        "required_documents": ["CV", "Oferta de trabajo", "Título homologado"],
        "strengths_hint": "Vía directa si ya existe una oferta laboral en el país.",
        "risks_hint": "Depende de conseguir una oferta de trabajo previa, no solo del perfil.",
    },
    {
        "visa_type": "Skilled Independent Visa (subclass 189)",
        "country": "Australia",
        "required_signals": ["education"],
        "required_documents": ["CV", "Evaluación de habilidades", "Certificado de idioma"],
        "strengths_hint": "No requiere patrocinador -- vía independiente basada en el perfil.",
        "risks_hint": "Proceso de evaluación de habilidades puede ser largo y específico por ocupación.",
    },
]
