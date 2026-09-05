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

Estado de verificación al 2026-09-05:

  ✅ O-1A (Estados Unidos)  -- verificado contra uscis.gov (criterios
     probatorios del Policy Manual, Volume 2, Part M, Chapter 4).
  ✅ Express Entry (Canadá) -- verificado contra canada.ca (requisitos
     mínimos del Federal Skilled Worker Program).
  ✅ Subclass 189 (Australia) -- verificado contra immi.homeaffairs.gov.au
     (pestaña "Eligibility" de la corriente Points-tested). El sitio rechaza
     peticiones automatizadas con HTTP 403, así que se leyó abriéndolo en un
     navegador real.
  ✅ Residencia y trabajo por cuenta ajena (España) -- verificado contra la
     Hoja informativa 12 de inclusion.gob.es (base legal: LO 4/2000 y
     RD 1155/2024).

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
            # Cada documento se convierte en un paso del plan (ver
            # execution_plan/domain/rules.py::build_plan_steps), así que el
            # texto tiene que leerse como un paso accionable, no como un
            # párrafo. El detalle de los 8 criterios va en `risks_hint`.
            "Evidencia de al menos 3 de los 8 criterios probatorios de USCIS",
        ],
        "strengths_hint": (
            "Vía para quien puede documentar estar en el pequeño porcentaje que llegó "
            "a lo más alto de su campo (ciencias, educación, negocios o atletismo)."
        ),
        "risks_hint": (
            "No alcanza con experiencia general: USCIS exige evidencia de al menos 3 de 8 "
            "criterios probatorios — premios reconocidos, membresías que exijan logros "
            "destacados, publicaciones sobre tu trabajo, haber sido jurado del trabajo de "
            "otros, contribuciones originales de importancia mayor, autoría de artículos "
            "académicos, empleo en capacidad crítica en organizaciones de reputación "
            "distinguida, o salario alto. Además la petición la presenta un empleador o "
            "agente estadounidense, no vos directamente."
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
        # Criterios de elegibilidad textuales del Department of Home Affairs,
        # pestaña "Eligibility" de la corriente Points-tested.
        "required_documents": [
            "Ocupación incluida en la lista de ocupaciones calificadas vigente",
            "Evaluación de habilidades (skills assessment) favorable para esa ocupación",
            "Expression of Interest (EOI) en SkillSelect y recibir una invitación para postular",
            "Puntaje de 65 puntos o más en la prueba de puntos",
            "Acreditar inglés al menos en nivel «competent English»",
            "Cumplir los requisitos de salud y de carácter (health y character)",
        ],
        "strengths_hint": (
            "Residencia permanente sin patrocinador ni empleador: es una vía independiente "
            "por puntos, y permite vivir y trabajar en cualquier parte de Australia."
        ),
        "risks_hint": (
            "Es por invitación: sin 65 puntos no se recibe invitación para postular. Además "
            "hay que tener menos de 45 años al momento de la invitación, la evaluación de "
            "habilidades es específica por ocupación, y el costo parte de AUD 6.135."
        ),
        "source_name": "Department of Home Affairs (Australia)",
        "source_url": (
            "https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing/"
            "skilled-independent-189/points-tested"
        ),
        # El sitio rechaza peticiones automatizadas (HTTP 403); se verificó
        # abriéndolo en un navegador real.
        "verified_at": "2026-09-05",
    },
    {
        "visa_type": "Residencia temporal y trabajo por cuenta ajena",
        "country": "España",
        "required_signals": ["experience"],
        # Hoja informativa 12 del Ministerio de Inclusión (última
        # actualización oficial: mayo 2025). Base legal: LO 4/2000 (arts. 36,
        # 38 y 40) y RD 1155/2024 (arts. 72 a 79).
        "required_documents": [
            "Contrato de trabajo firmado por empleador y trabajador (lo solicita el empleador, no vos)",
            "Que la situación nacional de empleo permita la contratación: ocupación en el "
            "catálogo de difícil cobertura, o que la empresa acredite la dificultad de cubrir "
            "el puesto, o ser nacional de Chile o Perú por convenio",
            "Certificado de antecedentes penales de España y de los países de residencia "
            "de los últimos 5 años",
            "Pasaporte en vigor y pago de la tasa (modelo 790, código 052)",
        ],
        "strengths_hint": (
            "Vía directa cuando ya existe una oferta laboral concreta, y permite además "
            "trabajar por cuenta propia mientras la actividad principal siga siendo por "
            "cuenta ajena."
        ),
        "risks_hint": (
            "No la pedís vos: la solicita el empleador. El cuello de botella real es la "
            "situación nacional de empleo — si la ocupación no está en el catálogo de "
            "difícil cobertura, la empresa tiene que probar que no pudo cubrir el puesto "
            "en el mercado local. No aplica a ciudadanos de la UE, EEE ni Suiza."
        ),
        "source_name": "Ministerio de Inclusión, Seguridad Social y Migraciones (España)",
        "source_url": (
            "https://www.inclusion.gob.es/web/migraciones/w/"
            "autorizacion-inicial-de-residencia-temporal-y-trabajo-por-cuenta-ajena-hi-16-"
        ),
        "verified_at": "2026-09-05",
    },
]


def is_verified(entry: RouteCatalogEntry) -> bool:
    """Una ruta está verificada si su contenido se leyó de la fuente oficial
    citada. El producto muestra esta distinción al usuario -- ver A-ADR-008."""
    return bool(entry.get("verified_at"))
