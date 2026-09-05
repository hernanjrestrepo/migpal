"""
Policy Engine — catálogo de rutas migratorias.

Cada entrada declara SU PROCEDENCIA: de qué fuente oficial sale la
información y cuándo se verificó por última vez. Esto reemplaza al catálogo
placeholder original, cuyo problema no era estar incompleto sino ser
indistinguible de datos reales: la auditoría independiente de Hito 3 lo
marcó como riesgo ("percepción de asesoría migratoria autoritativa donde no
la hay", ver docs/HITO_3_AUDIT.md, hallazgo menor 1).

Regla de este módulo, sin excepciones:

    NADA se escribe acá si no se leyó primero en la fuente oficial del
    organismo que administra esa vía migratoria. Si una fuente no pudo
    consultarse, la entrada queda con `verified_at=None` y el producto lo
    muestra como NO verificada -- nunca se completa "a ojo" ni con
    conocimiento general del modelo que escribe el código.

Estado de verificación al 2026-09-04:

  ✅ O-1A (Estados Unidos)  -- verificado contra uscis.gov (criterios
     probatorios del Policy Manual, Volume 2, Part M, Chapter 4).
  ✅ Express Entry (Canadá) -- verificado contra canada.ca (requisitos
     mínimos del Federal Skilled Worker Program).
  ⚠️ Subclass 189 (Australia) -- immi.homeaffairs.gov.au responde HTTP 403
     a consultas automatizadas; no se pudo verificar. Queda como NO
     verificada, con los datos mínimos que ya tenía.
  ⚠️ Trabajo por cuenta ajena (España) -- el portal de extranjería no fue
     accesible (404 / certificado no verificable). Queda como NO verificada.

`required_signals` usa el mismo vocabulario que
`decision_engine.infrastructure.scoring.SIGNAL_KEYWORDS`
(experience/education/destination/family/financial).

IMPORTANTE: esto sigue sin ser asesoría legal migratoria. Es un resumen
orientativo con su fuente citada para que el usuario pueda ir a leerla él
mismo. Los requisitos reales cambian y dependen del caso concreto.
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
    # — Procedencia (ver A-ADR-008) —
    source_name: str
    source_url: str
    verified_at: str | None  # ISO-8601 (YYYY-MM-DD); None = sin verificar


ROUTE_CATALOG: list[RouteCatalogEntry] = [
    {
        "visa_type": "O-1A",
        "country": "Estados Unidos",
        "required_signals": ["experience", "education"],
        # Los ocho criterios probatorios del O-1A: hay que satisfacer al
        # menos TRES (o un único premio internacional mayor, tipo Nobel).
        # Textual de USCIS Policy Manual Vol. 2, Part M, Ch. 4.
        "required_documents": [
            "Formulario I-129 presentado por un empleador o agente en EE.UU.",
            "Consulta escrita de un grupo de pares o experto en la materia",
            "Contrato de trabajo o resumen de los términos del acuerdo",
            "Evidencia de al menos 3 de los 8 criterios: premios reconocidos, "
            "membresías que exijan logros destacados, publicaciones sobre tu trabajo, "
            "haber sido jurado del trabajo de otros, contribuciones originales de "
            "importancia mayor, autoría de artículos académicos, empleo en capacidad "
            "crítica en organizaciones de reputación distinguida, o salario alto",
        ],
        "strengths_hint": (
            "Vía para quien puede documentar estar en el pequeño porcentaje que llegó "
            "a lo más alto de su campo (ciencias, educación, negocios o atletismo)."
        ),
        "risks_hint": (
            "No alcanza con experiencia general: USCIS exige evidencia de al menos 3 de "
            "8 criterios probatorios, y la petición la presenta un empleador o agente "
            "estadounidense, no vos directamente."
        ),
        "source_name": "USCIS — U.S. Citizenship and Immigration Services",
        "source_url": (
            "https://www.uscis.gov/working-in-the-united-states/temporary-workers/"
            "o-1-visa-individuals-with-extraordinary-ability-or-achievement"
        ),
        "verified_at": "2026-09-04",
    },
    {
        "visa_type": "Express Entry — Federal Skilled Worker",
        "country": "Canadá",
        "required_signals": ["experience"],
        # Requisitos mínimos del Federal Skilled Worker Program, textual de
        # canada.ca (IRCC).
        "required_documents": [
            "1 año de experiencia laboral continua en los últimos 10 años en tu ocupación principal",
            "Nivel de idioma CLB 7 acreditado con un test aprobado",
            "Educación secundaria completa como mínimo (los estudios superiores suman puntos)",
            "Evaluación de credenciales educativas (ECA) si estudiaste fuera de Canadá",
        ],
        "strengths_hint": (
            "Sistema por puntos que combina experiencia, educación e idioma; no requiere "
            "una oferta de trabajo previa para entrar al pool."
        ),
        "risks_hint": (
            "Entrar al pool no garantiza invitación: se compite contra el resto de "
            "candidatos y el puntaje de corte varía en cada ronda."
        ),
        "source_name": "IRCC — Immigration, Refugees and Citizenship Canada",
        "source_url": (
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/"
            "immigrate-canada/express-entry/eligibility.html"
        ),
        "verified_at": "2026-09-04",
    },
    {
        "visa_type": "Skilled Independent Visa (subclass 189)",
        "country": "Australia",
        "required_signals": ["education"],
        "required_documents": [
            "Evaluación de habilidades (skills assessment) de la autoridad de tu ocupación",
            "Resultados de test de inglés",
            "Expression of Interest (EOI) en SkillSelect",
        ],
        "strengths_hint": "Vía independiente por puntos: no requiere patrocinador ni empleador.",
        "risks_hint": (
            "Es por invitación y por puntaje. La evaluación de habilidades es específica "
            "por ocupación y puede llevar tiempo."
        ),
        "source_name": "Department of Home Affairs (Australia)",
        "source_url": (
            "https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing/skilled-independent-189"
        ),
        # El sitio devuelve HTTP 403 a consultas automatizadas: no se pudo
        # verificar el contenido. Se deja explícitamente sin verificar.
        "verified_at": None,
    },
    {
        "visa_type": "Residencia y trabajo por cuenta ajena",
        "country": "España",
        "required_signals": ["experience"],
        "required_documents": [
            "Oferta de trabajo de una empresa en España",
            "Titulación homologada o acreditación de la cualificación",
            "Pasaporte en vigor y antecedentes penales",
        ],
        "strengths_hint": "Vía directa cuando ya existe una oferta laboral concreta en el país.",
        "risks_hint": (
            "Depende de conseguir la oferta primero; la empresa suele tener que acreditar "
            "la situación nacional de empleo."
        ),
        "source_name": "Ministerio de Inclusión, Seguridad Social y Migraciones (España)",
        "source_url": "https://extranjeros.inclusion.gob.es/",
        # Portal no accesible automáticamente (404 / certificado no verificable).
        "verified_at": None,
    },
]


def is_verified(entry: RouteCatalogEntry) -> bool:
    """Una ruta está verificada si su contenido se leyó de la fuente oficial
    citada. El producto muestra esta distinción al usuario -- ver A-ADR-008."""
    return bool(entry.get("verified_at"))
