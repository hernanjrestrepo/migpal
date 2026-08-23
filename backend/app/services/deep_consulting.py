"""
MigPAL Deep Consulting - Consultoría Profunda de Migración
El mejor consultor de migración del universo

FILOSOFÍA:
- Los 2 años de dolor de los migrantes ocurren por falta de:
  * Preparación
  * Investigación
  * Información
  * Asesoría
  * Conocimiento

- MigPAL soluciona TODO esto con:
  * Información REAL de APIs y web scraping
  * Filtrado inteligente basado en preferencias
  * Recomendaciones personalizadas
  * Visualización clara con fotos, precios, datos
  * Acompañamiento continuo

SERVICIOS:
- Diagnóstico: $50 USD
- Perfilamiento: $50 USD
- Revisión Documental: $200 USD
- Plan de Migración: $100 USD (OPCIONAL)
- Due Diligence de Negocio: $100 USD

TOTAL: $400 USD (NO RETORNABLES)
"""

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from app.services.research_engine import (
    ClientProfile,
    get_deep_profiling_question,
    get_research_engine,
)

logger = logging.getLogger(__name__)

# ============== PRECIOS ==============

CONSULTING_PRICES = {
    "diagnostico": 50,
    "perfilamiento": 50,
    "revision_documental": 200,
    "plan_migracion": 100,
    "due_diligence_negocio": 100,
    "total_basico": 300,
    "total_completo": 400,
}

# ============== FASES DE CONSULTORÍA ==============


class ConsultingPhase:
    """Fases del proceso de consultoría"""

    INITIAL = "initial"  # Consulta inicial gratuita
    DEEP_PROFILING = "deep_profiling"  # Perfilamiento profundo
    DIAGNOSTIC = "diagnostic"  # Diagnóstico de viabilidad
    VISA_DEFINITION = "visa_definition"  # Definición de visa
    CITY_RESEARCH = "city_research"  # Investigación de ciudades
    HOUSING_SEARCH = "housing_search"  # Búsqueda de vivienda
    JOB_SEARCH = "job_search"  # Búsqueda de empleo
    SCHOOL_SEARCH = "school_search"  # Búsqueda de colegios
    BUSINESS_SEARCH = "business_search"  # Búsqueda de negocios
    DUE_DILIGENCE = "due_diligence"  # Due diligence de negocio
    DOCUMENT_REVIEW = "document_review"  # Revisión documental
    MIGRATION_PLAN = "migration_plan"  # Plan de migración completo
    COMPLETED = "completed"  # Proceso completado


# ============== ESTADO DE CONSULTORÍA ==============


@dataclass
class ConsultingState:
    """Estado completo de la consultoría del cliente"""

    user_id: int

    # Fase actual
    current_phase: str = ConsultingPhase.INITIAL

    # Perfil del cliente
    profile: dict = field(default_factory=dict)

    # Preguntas respondidas
    answered_questions: list[str] = field(default_factory=list)

    # Preferencias refinadas
    preferences: dict = field(default_factory=dict)

    # Ciudades investigadas
    researched_cities: list[str] = field(default_factory=list)
    city_scores: dict[str, float] = field(default_factory=dict)
    selected_city: str = ""

    # Resultados de investigación
    properties_found: list[dict] = field(default_factory=list)
    jobs_found: list[dict] = field(default_factory=list)
    schools_found: list[dict] = field(default_factory=list)
    businesses_found: list[dict] = field(default_factory=list)
    community_info: dict = field(default_factory=dict)

    # Selecciones del cliente
    favorite_properties: list[str] = field(default_factory=list)
    favorite_jobs: list[str] = field(default_factory=list)
    favorite_schools: list[str] = field(default_factory=list)
    favorite_businesses: list[str] = field(default_factory=list)

    # Due diligence
    due_diligence_requested: bool = False
    due_diligence_business_id: str = ""
    due_diligence_report: dict = field(default_factory=dict)

    # Diagnóstico
    viability_score: int = 0
    is_viable: bool = False
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    # Visa
    recommended_visa: str = ""
    visa_probability: int = 0
    visa_requirements: list[str] = field(default_factory=list)
    visa_timeline: str = ""

    # Pagos
    payments: list[dict] = field(default_factory=list)
    total_paid: float = 0

    # Timestamps
    started_at: str = ""
    diagnostic_at: str = ""
    profiling_at: str = ""
    docs_review_at: str = ""
    plan_completed_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ConsultingState":
        return cls(**data)


# ============== MOTOR DE CONSULTORÍA ==============


class MigPALConsultingEngine:
    """
    Motor de consultoría profunda de MigPAL
    Integra investigación, filtrado y recomendaciones personalizadas
    """

    def __init__(self):
        self._states: dict[int, ConsultingState] = {}
        self._research = get_research_engine()

    def get_state(self, user_id: int) -> ConsultingState:
        """Obtiene o crea el estado de consultoría"""
        if user_id not in self._states:
            self._states[user_id] = ConsultingState(user_id=user_id, started_at=datetime.now().isoformat())
        return self._states[user_id]

    def save_state(self, user_id: int, state: ConsultingState):
        """Guarda el estado"""
        self._states[user_id] = state

    # ============== PERFILAMIENTO PROFUNDO ==============

    def get_next_profiling_question(self, user_id: int) -> dict | None:
        """Obtiene la siguiente pregunta de perfilamiento"""
        state = self.get_state(user_id)

        # Preguntas prioritarias basadas en lo que ya sabemos
        priority_questions = self._get_priority_questions(state)

        for q_id in priority_questions:
            if q_id not in state.answered_questions:
                q_data = get_deep_profiling_question(q_id)
                if q_data:
                    return {"id": q_id, **q_data}

        return None

    def _get_priority_questions(self, state: ConsultingState) -> list[str]:
        """Determina las preguntas prioritarias basadas en el perfil"""
        questions = []

        # Siempre preguntar sobre familia en USA primero
        questions.append("family_in_usa")

        # Si tiene familia en USA, preguntar ubicación y cercanía
        if state.preferences.get("family_in_usa") == "si":
            questions.extend(["family_location", "near_family"])

        # Preguntas de comunidad
        questions.extend(["church_important", "spanish_services"])

        # Preguntas de trabajo
        questions.extend(["work_mode", "salary_expectation"])

        # Si está interesado en negocio
        if state.preferences.get("work_preference") in ["negocio", "ambos"]:
            questions.extend(["business_experience", "business_type_interest", "business_budget"])

        # Si tiene hijos
        if state.profile.get("children"):
            questions.extend(["school_priority", "school_budget"])

        # Preguntas de vivienda
        questions.extend(["housing_priority", "yard_important", "pets"])

        # Transporte
        questions.extend(["car_situation", "commute_tolerance"])

        # Estilo de vida
        questions.extend(["lifestyle", "social_life"])

        return questions

    def answer_profiling_question(self, user_id: int, question_id: str, answer: Any) -> dict:
        """Registra respuesta a pregunta de perfilamiento"""
        state = self.get_state(user_id)

        state.answered_questions.append(question_id)
        state.preferences[question_id] = answer

        # Procesar respuestas especiales
        if question_id == "family_in_usa" and answer == "si":
            # Marcar que tiene familia en USA
            state.profile["has_family_in_usa"] = True

        if question_id == "family_location":
            state.profile["family_in_usa_location"] = answer

        if question_id == "near_family":
            state.profile["want_near_family"] = answer == "muy_importante"

        self.save_state(user_id, state)

        # Obtener siguiente pregunta
        next_q = self.get_next_profiling_question(user_id)

        return {
            "success": True,
            "next_question": next_q,
            "profiling_complete": next_q is None,
            "questions_answered": len(state.answered_questions),
        }

    # ============== DIAGNÓSTICO ==============

    async def run_diagnostic(self, user_id: int) -> dict:
        """
        Ejecuta diagnóstico completo de viabilidad
        Costo: $50 USD
        """
        state = self.get_state(user_id)
        profile = state.profile

        # Calcular score de viabilidad
        score = 0
        strengths = []
        weaknesses = []
        recommendations = []

        # Educación (20 puntos)
        education = profile.get("education", {})
        edu_level = education.get("level", "")
        if edu_level in ["maestria", "doctorado"]:
            score += 20
            strengths.append("✅ Nivel educativo alto (Maestría/Doctorado)")
        elif edu_level in ["universidad", "licenciatura"]:
            score += 15
            strengths.append("✅ Título universitario")
        elif edu_level == "tecnico":
            score += 10
            weaknesses.append("⚠️ Nivel técnico - considera especialización")
            recommendations.append("📚 Considera obtener certificaciones adicionales")
        else:
            score += 5
            weaknesses.append("❌ Nivel educativo bajo")
            recommendations.append("📚 Considera completar estudios superiores")

        # Experiencia laboral (25 puntos)
        work = profile.get("work", {})
        experience = work.get("experience", "")
        if ">15" in experience or ">10" in experience:
            score += 25
            strengths.append("✅ Amplia experiencia laboral (+10 años)")
        elif ">5" in experience:
            score += 20
            strengths.append("✅ Buena experiencia laboral (5-10 años)")
        elif ">2" in experience:
            score += 12
            weaknesses.append("⚠️ Experiencia moderada (2-5 años)")
        else:
            score += 5
            weaknesses.append("❌ Poca experiencia laboral")
            recommendations.append("💼 Acumula más experiencia en tu campo")

        # Inglés (15 puntos)
        languages = profile.get("languages", {})
        english = languages.get("english", "")
        if english in ["nativo", "avanzado", "fluido"]:
            score += 15
            strengths.append("✅ Inglés avanzado/fluido")
        elif english in ["intermedio", "b2"]:
            score += 10
            weaknesses.append("⚠️ Inglés intermedio")
            recommendations.append("🗣️ Mejora tu inglés a nivel avanzado")
        else:
            score += 3
            weaknesses.append("❌ Inglés básico o nulo")
            recommendations.append("🗣️ URGENTE: Aprende inglés antes de migrar")

        # Situación financiera (15 puntos)
        financial = profile.get("financial", {})
        savings = financial.get("savings", "")
        if ">50000" in savings or ">100000" in savings:
            score += 15
            strengths.append("✅ Excelente situación financiera")
        elif ">20000" in savings or ">30000" in savings:
            score += 12
            strengths.append("✅ Buena situación financiera")
        elif ">10000" in savings:
            score += 8
            weaknesses.append("⚠️ Ahorros moderados")
            recommendations.append("💰 Aumenta tus ahorros antes de migrar")
        else:
            score += 3
            weaknesses.append("❌ Ahorros insuficientes")
            recommendations.append("💰 URGENTE: Necesitas mínimo $20,000 USD")

        # Historial migratorio (10 puntos)
        history = profile.get("history", {})
        if history.get("rejections"):
            score -= 5
            weaknesses.append("❌ Tienes rechazos de visa previos")
            recommendations.append("📋 Prepara explicación para rechazos anteriores")
        else:
            score += 10
            strengths.append("✅ Sin rechazos de visa previos")

        if history.get("criminal") and history["criminal"] != "no":
            score -= 10
            weaknesses.append("❌ Antecedentes penales")
            recommendations.append("⚖️ Consulta opciones con antecedentes")
        else:
            score += 5
            strengths.append("✅ Sin antecedentes penales")

        # Logros y reconocimientos (10 puntos)
        achievements = profile.get("achievements", [])
        if len(achievements) >= 3:
            score += 10
            strengths.append("✅ Múltiples logros y reconocimientos")
        elif len(achievements) >= 1:
            score += 5
            weaknesses.append("⚠️ Pocos logros documentados")
            recommendations.append("🏆 Documenta más logros profesionales")
        else:
            weaknesses.append("❌ Sin logros documentados")
            recommendations.append("🏆 Necesitas documentar logros para visa O-1")

        # Determinar viabilidad
        is_viable = score >= 60

        # Guardar resultados
        state.viability_score = score
        state.is_viable = is_viable
        state.strengths = strengths
        state.weaknesses = weaknesses
        state.recommendations = recommendations
        state.diagnostic_at = datetime.now().isoformat()
        state.current_phase = ConsultingPhase.DIAGNOSTIC

        self.save_state(user_id, state)

        return {
            "score": score,
            "is_viable": is_viable,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "summary": self._generate_diagnostic_summary(score, is_viable, strengths, weaknesses),
        }

    def _generate_diagnostic_summary(
        self, score: int, is_viable: bool, strengths: list[str], weaknesses: list[str]
    ) -> str:
        """Genera resumen del diagnóstico"""

        if score >= 80:
            emoji = "🌟"
            status = "EXCELENTE"
            message = "Tienes un perfil muy fuerte para migrar a USA."
        elif score >= 70:
            emoji = "✅"
            status = "MUY BUENO"
            message = "Tienes buenas probabilidades de éxito."
        elif score >= 60:
            emoji = "👍"
            status = "VIABLE"
            message = "Puedes proceder con el proceso migratorio."
        elif score >= 50:
            emoji = "⚠️"
            status = "NECESITA MEJORAS"
            message = "Debes trabajar en algunas áreas antes de aplicar."
        else:
            emoji = "❌"
            status = "NO VIABLE AÚN"
            message = "Necesitas prepararte más antes de migrar."

        summary = f"""
{emoji} *DIAGNÓSTICO DE VIABILIDAD*

📊 *Score: {score}/100*
📋 *Estado: {status}*

{message}

*FORTALEZAS ({len(strengths)}):*
{chr(10).join(strengths) if strengths else "Ninguna identificada"}

*ÁREAS DE MEJORA ({len(weaknesses)}):*
{chr(10).join(weaknesses) if weaknesses else "Ninguna identificada"}
"""
        return summary

    # ============== DEFINICIÓN DE VISA ==============

    def define_visa(self, user_id: int) -> dict:
        """
        Define el tipo de visa recomendada basado en el perfil
        Incluido en Perfilamiento ($50 USD)
        """
        state = self.get_state(user_id)
        profile = state.profile

        # Analizar perfil para recomendar visa
        work = profile.get("work", {})
        education = profile.get("education", {})
        achievements = profile.get("achievements", [])
        financial = profile.get("financial", {})

        visa_options = []

        # O-1: Habilidades Extraordinarias
        if len(achievements) >= 3 or state.viability_score >= 75:
            visa_options.append(
                {
                    "type": "O-1",
                    "name": "Visa O-1 (Habilidades Extraordinarias)",
                    "probability": min(85, state.viability_score + 10),
                    "description": "Para personas con habilidades extraordinarias en ciencias, artes, educación, negocios o deportes.",
                    "requirements": [
                        "Premios o reconocimientos nacionales/internacionales",
                        "Membresía en asociaciones de élite",
                        "Publicaciones o artículos sobre tu trabajo",
                        "Contribuciones originales significativas",
                        "Salario alto comparado con otros en tu campo",
                    ],
                    "timeline": "3-6 meses",
                    "pros": ["No requiere empleador", "Renovable indefinidamente", "Camino a Green Card"],
                    "cons": ["Requiere evidencia fuerte", "Proceso de documentación extenso"],
                }
            )

        # EB-2 NIW: Green Card por Mérito
        if education.get("level") in ["maestria", "doctorado"] or (">10" in work.get("experience", "")):
            visa_options.append(
                {
                    "type": "EB-2 NIW",
                    "name": "EB-2 NIW (Green Card por Mérito)",
                    "probability": min(75, state.viability_score),
                    "description": "Green Card para profesionales con grado avanzado o habilidad excepcional.",
                    "requirements": [
                        "Maestría o superior, O 5+ años de experiencia progresiva",
                        "Demostrar que tu trabajo beneficia a USA",
                        "Demostrar que es mejor que no requieras oferta de empleo",
                    ],
                    "timeline": "12-24 meses",
                    "pros": ["Green Card directa", "No requiere empleador", "Para toda la familia"],
                    "cons": ["Proceso largo", "Requiere evidencia sustancial"],
                }
            )

        # E-2: Inversionista
        savings = financial.get("savings", "")
        if ">100000" in savings or ">50000" in savings:
            visa_options.append(
                {
                    "type": "E-2",
                    "name": "Visa E-2 (Inversionista)",
                    "probability": 80,
                    "description": "Para inversionistas que invierten capital sustancial en un negocio en USA.",
                    "requirements": [
                        "Inversión sustancial (típicamente $100,000+)",
                        "Negocio real y operativo",
                        "Demostrar que no es marginal",
                        "Tratado de comercio con tu país",
                    ],
                    "timeline": "2-4 meses",
                    "pros": ["Proceso rápido", "Renovable indefinidamente", "Puedes manejar tu negocio"],
                    "cons": ["Requiere inversión significativa", "No es camino directo a Green Card"],
                }
            )

        # H-1B: Trabajo Especializado
        if education.get("level") in ["universidad", "licenciatura", "maestria", "doctorado"]:
            visa_options.append(
                {
                    "type": "H-1B",
                    "name": "Visa H-1B (Trabajo Especializado)",
                    "probability": 65,
                    "description": "Para profesionales con oferta de trabajo en ocupación especializada.",
                    "requirements": [
                        "Título universitario relacionado con el trabajo",
                        "Oferta de trabajo de empleador en USA",
                        "El empleador debe patrocinar la visa",
                        "Ganar lotería anual (si aplica)",
                    ],
                    "timeline": "6-12 meses",
                    "pros": ["Camino a Green Card", "Empleador paga costos"],
                    "cons": ["Depende de empleador", "Lotería anual", "Cupo limitado"],
                }
            )

        # Seleccionar la mejor opción
        if visa_options:
            best_visa = max(visa_options, key=lambda x: x["probability"])

            state.recommended_visa = best_visa["type"]
            state.visa_probability = best_visa["probability"]
            state.visa_requirements = best_visa["requirements"]
            state.visa_timeline = best_visa["timeline"]
            state.current_phase = ConsultingPhase.VISA_DEFINITION
            state.profiling_at = datetime.now().isoformat()

            self.save_state(user_id, state)

            return {
                "recommended": best_visa,
                "alternatives": [v for v in visa_options if v["type"] != best_visa["type"]],
                "summary": self._generate_visa_summary(best_visa),
            }

        return {
            "recommended": None,
            "alternatives": [],
            "summary": "No se encontró una visa adecuada para tu perfil actual. Necesitas mejorar tu perfil.",
        }

    def _generate_visa_summary(self, visa: dict) -> str:
        """Genera resumen de la visa recomendada"""
        return f"""
🛂 *VISA RECOMENDADA*

🎯 *{visa['name']}*
📊 Probabilidad de aprobación: *{visa['probability']}%*
⏱️ Tiempo estimado: *{visa['timeline']}*

📝 *Descripción:*
{visa['description']}

✅ *Requisitos:*
{chr(10).join(['• ' + r for r in visa['requirements']])}

👍 *Ventajas:*
{chr(10).join(['• ' + p for p in visa['pros']])}

⚠️ *Consideraciones:*
{chr(10).join(['• ' + c for c in visa['cons']])}
"""

    # ============== INVESTIGACIÓN DE CIUDAD ==============

    async def research_city(self, user_id: int, city: str, state_code: str) -> dict:
        """
        Realiza investigación completa de una ciudad
        Incluido en Plan de Migración ($100 USD)
        """
        consulting_state = self.get_state(user_id)

        # Construir perfil para investigación
        profile = ClientProfile(
            user_id=user_id,
            name=consulting_state.profile.get("personal", {}).get("name", ""),
            profession=consulting_state.profile.get("work", {}).get("profession", ""),
            children=(
                [{"name": "hijo", "age": 10}]
                if consulting_state.profile.get("preferences", {}).get("family_status") == "con_familia"
                else []
            ),
            max_rent=consulting_state.preferences.get("max_rent", 2500),
            bedrooms_needed=consulting_state.preferences.get("bedrooms", 2),
            work_preference=consulting_state.preferences.get("work_preference", "empleo"),
            business_budget=consulting_state.preferences.get("business_budget", 150000),
            desired_salary_min=consulting_state.preferences.get("salary_min", 60000),
        )

        # Ejecutar investigación completa
        results = await self._research.full_research(profile, city, state_code)

        # Guardar resultados
        consulting_state.researched_cities.append(f"{city}, {state_code}")
        consulting_state.properties_found = results.get("properties", [])
        consulting_state.jobs_found = results.get("jobs", [])
        consulting_state.schools_found = results.get("schools", [])
        consulting_state.businesses_found = results.get("businesses", [])
        consulting_state.community_info = results.get("community", {})
        consulting_state.current_phase = ConsultingPhase.CITY_RESEARCH

        self.save_state(user_id, consulting_state)

        return {
            "city": city,
            "state": state_code,
            "properties": results.get("properties", []),
            "jobs": results.get("jobs", []),
            "schools": results.get("schools", []),
            "businesses": results.get("businesses", []),
            "community": results.get("community", {}),
            "summary": self._generate_city_summary(city, state_code, results),
        }

    def _generate_city_summary(self, city: str, state: str, results: dict) -> str:
        """Genera resumen de la investigación de ciudad"""
        community = results.get("community", {})

        return f"""
🏙️ *INVESTIGACIÓN: {city}, {state}*

👥 *COMUNIDAD:*
• Población latina: {community.get('latino_population_pct', 0):.1f}%
• Ingreso medio: ${community.get('median_income', 0):,}/año
• Alquiler medio: ${community.get('median_rent', 0):,}/mes
• Índice de seguridad: {100 - community.get('crime_index', 50)}/100

🏠 *VIVIENDAS ENCONTRADAS:* {len(results.get('properties', []))}
💼 *EMPLEOS ENCONTRADOS:* {len(results.get('jobs', []))}
🎓 *COLEGIOS ENCONTRADOS:* {len(results.get('schools', []))}
🏪 *NEGOCIOS EN VENTA:* {len(results.get('businesses', []))}

_Usa los comandos para ver detalles de cada categoría._
"""

    # ============== DUE DILIGENCE DE NEGOCIO ==============

    async def run_due_diligence(self, user_id: int, business_id: str) -> dict:
        """
        Ejecuta due diligence de un negocio
        Costo: $100 USD
        """
        state = self.get_state(user_id)

        # Buscar el negocio
        business = None
        for biz in state.businesses_found:
            if biz.get("business_id") == business_id:
                business = biz
                break

        if not business:
            return {"error": "Negocio no encontrado"}

        # Generar reporte de due diligence
        report = {
            "business": business,
            "financial_analysis": {
                "asking_price": business.get("asking_price", 0),
                "annual_revenue": business.get("annual_revenue", 0),
                "annual_profit": business.get("annual_profit", 0),
                "roi": (business.get("annual_profit", 0) / business.get("asking_price", 1)) * 100,
                "payback_years": business.get("asking_price", 0) / max(business.get("annual_profit", 1), 1),
                "revenue_multiple": business.get("asking_price", 0)
                / max(business.get("annual_revenue", 1), 1),
            },
            "risk_assessment": {
                "market_risk": "Medio",
                "operational_risk": "Bajo" if business.get("years_established", 0) > 5 else "Medio",
                "financial_risk": "Bajo" if business.get("annual_profit", 0) > 50000 else "Medio",
                "location_risk": "Bajo",
            },
            "recommendations": [
                "✅ Verificar estados financieros de los últimos 3 años",
                "✅ Revisar contratos con proveedores y clientes",
                "✅ Inspeccionar equipos e inventario",
                "✅ Verificar licencias y permisos",
                "✅ Hablar con empleados actuales",
                "✅ Analizar competencia en la zona",
                "✅ Revisar historial de impuestos",
                "✅ Verificar razón real de venta",
            ],
            "visa_compatibility": {
                "e2_eligible": business.get("asking_price", 0) >= 100000,
                "investment_sufficient": True,
                "job_creation": business.get("employees", 0) >= 2,
            },
            "verdict": (
                "RECOMENDADO"
                if business.get("annual_profit", 0) / max(business.get("asking_price", 1), 1) > 0.2
                else "REVISAR CON CUIDADO"
            ),
        }

        state.due_diligence_requested = True
        state.due_diligence_business_id = business_id
        state.due_diligence_report = report
        state.current_phase = ConsultingPhase.DUE_DILIGENCE

        self.save_state(user_id, state)

        return {
            "report": report,
            "summary": self._generate_due_diligence_summary(report),
        }

    def _generate_due_diligence_summary(self, report: dict) -> str:
        """Genera resumen del due diligence"""
        biz = report["business"]
        fin = report["financial_analysis"]
        risk = report["risk_assessment"]
        visa = report["visa_compatibility"]

        return f"""
📊 *DUE DILIGENCE: {biz.get('name', 'Negocio')}*

💰 *ANÁLISIS FINANCIERO:*
• Precio: ${fin['asking_price']:,}
• Ingresos anuales: ${fin['annual_revenue']:,}
• Ganancia anual: ${fin['annual_profit']:,}
• ROI: {fin['roi']:.1f}%
• Recuperación: {fin['payback_years']:.1f} años
• Múltiplo de ingresos: {fin['revenue_multiple']:.2f}x

⚠️ *EVALUACIÓN DE RIESGOS:*
• Riesgo de mercado: {risk['market_risk']}
• Riesgo operacional: {risk['operational_risk']}
• Riesgo financiero: {risk['financial_risk']}

🛂 *COMPATIBILIDAD CON VISA E-2:*
• Inversión suficiente: {'✅ Sí' if visa['e2_eligible'] else '❌ No'}
• Creación de empleos: {'✅ Sí' if visa['job_creation'] else '❌ No'}

📋 *RECOMENDACIONES:*
{chr(10).join(report['recommendations'][:5])}

🎯 *VEREDICTO: {report['verdict']}*
"""

    # ============== PLAN DE MIGRACIÓN COMPLETO ==============

    async def generate_migration_plan(self, user_id: int) -> dict:
        """
        Genera plan de migración completo
        Costo: $100 USD (OPCIONAL)
        """
        state = self.get_state(user_id)

        plan = {
            "user_id": user_id,
            "generated_at": datetime.now().isoformat(),
            # Resumen del perfil
            "profile_summary": {
                "name": state.profile.get("personal", {}).get("name", ""),
                "visa": state.recommended_visa,
                "probability": state.visa_probability,
                "city": state.selected_city
                or (state.researched_cities[0] if state.researched_cities else ""),
            },
            # Vivienda recomendada
            "housing": {
                "recommendations": state.properties_found[:3],
                "budget": state.preferences.get("max_rent", 2500),
                "type": state.preferences.get("housing_type", "apartamento"),
            },
            # Empleo
            "employment": {
                "recommendations": state.jobs_found[:3],
                "expected_salary": state.preferences.get("salary_expectation", "70k"),
            },
            # Educación (si tiene hijos)
            "education": {
                "recommendations": state.schools_found[:3],
            },
            # Negocio (si aplica)
            "business": {
                "recommendations": (
                    state.businesses_found[:3]
                    if state.preferences.get("work_preference") in ["negocio", "ambos"]
                    else []
                ),
            },
            # Comunidad
            "community": state.community_info,
            # Presupuesto
            "budget": self._calculate_budget(state),
            # Timeline
            "timeline": self._generate_timeline(state),
            # Checklist
            "checklist": self._generate_checklist(state),
        }

        state.current_phase = ConsultingPhase.MIGRATION_PLAN
        state.plan_completed_at = datetime.now().isoformat()

        self.save_state(user_id, state)

        return plan

    def _calculate_budget(self, state: ConsultingState) -> dict:
        """Calcula presupuesto detallado"""
        community = state.community_info
        rent = community.get("median_rent", 2000) if community else 2000

        return {
            "monthly": {
                "rent": rent,
                "utilities": 150,
                "groceries": 400,
                "transportation": 200,
                "health_insurance": 450,
                "phone_internet": 100,
                "entertainment": 200,
                "savings": 300,
                "total": rent + 1800,
            },
            "initial": {
                "flights": 2000,
                "deposit": rent * 2,
                "furniture": 3000,
                "car": 15000,
                "emergency_fund": (rent + 1800) * 3,
                "visa_fees": 2000,
                "total": 2000 + (rent * 2) + 3000 + 15000 + ((rent + 1800) * 3) + 2000,
            },
        }

    def _generate_timeline(self, state: ConsultingState) -> list[dict]:
        """Genera timeline del proceso"""
        return [
            {
                "month": 1,
                "phase": "Preparación",
                "tasks": ["Reunir documentos", "Preparar evidencia", "Traducciones"],
            },
            {"month": 2, "phase": "Aplicación", "tasks": ["Enviar aplicación de visa", "Pagar fees"]},
            {"month": 3, "phase": "Espera", "tasks": ["Seguimiento de caso", "Preparar entrevista"]},
            {"month": 4, "phase": "Entrevista", "tasks": ["Entrevista consular", "Esperar decisión"]},
            {"month": 5, "phase": "Aprobación", "tasks": ["Recibir visa", "Planificar mudanza"]},
            {"month": 6, "phase": "Mudanza", "tasks": ["Viajar a USA", "Instalarse", "Primeros trámites"]},
        ]

    def _generate_checklist(self, state: ConsultingState) -> list[dict]:
        """Genera checklist de tareas"""
        return [
            {
                "category": "Documentos",
                "items": [
                    "Pasaporte vigente (mínimo 6 meses)",
                    "Acta de nacimiento apostillada",
                    "Títulos académicos apostillados",
                    "Certificados laborales",
                    "Antecedentes penales",
                    "Examen médico",
                ],
            },
            {
                "category": "Financiero",
                "items": [
                    "Estados de cuenta bancarios",
                    "Declaraciones de impuestos",
                    "Carta de empleo actual",
                    "Prueba de ahorros",
                ],
            },
            {
                "category": "Visa",
                "items": [
                    "Formulario DS-160",
                    "Foto tipo visa",
                    "Carta de petición",
                    "Evidencia de calificaciones",
                ],
            },
            {
                "category": "Llegada",
                "items": [
                    "Reservar alojamiento temporal",
                    "Abrir cuenta bancaria",
                    "Obtener SSN",
                    "Sacar licencia de conducir",
                    "Contratar seguro de salud",
                ],
            },
        ]


# ============== SINGLETON ==============

_consulting_engine: MigPALConsultingEngine | None = None


def get_consulting_engine() -> MigPALConsultingEngine:
    """Obtiene instancia del motor de consultoría"""
    global _consulting_engine
    if _consulting_engine is None:
        _consulting_engine = MigPALConsultingEngine()
    return _consulting_engine


# ============== HELPERS ==============


def format_property_list(properties: list[dict], limit: int = 5) -> str:
    """Formatea lista de propiedades para mostrar"""
    if not properties:
        return "No se encontraron propiedades."

    lines = ["🏠 *OPCIONES DE VIVIENDA*\n"]

    for i, prop in enumerate(properties[:limit], 1):
        price = prop.get("price", 0)
        listing_type = prop.get("listing_type", "rent")
        price_str = f"${price:,}/mes" if listing_type == "rent" else f"${price:,}"

        lines.append(
            f"""
*{i}. {prop.get('address', 'Dirección')}*
📍 {prop.get('city', '')}, {prop.get('state', '')}
💰 {price_str}
🛏️ {prop.get('bedrooms', 0)} hab | 🚿 {prop.get('bathrooms', 0)} baños | 📐 {prop.get('sqft', 0):,} sqft
🔗 [Ver en Zillow]({prop.get('zillow_url', '#')})
"""
        )

    return "\n".join(lines)


def format_job_list(jobs: list[dict], limit: int = 5) -> str:
    """Formatea lista de empleos para mostrar"""
    if not jobs:
        return "No se encontraron empleos."

    lines = ["💼 *OFERTAS DE EMPLEO*\n"]

    for i, job in enumerate(jobs[:limit], 1):
        salary_min = job.get("salary_min", 0)
        salary_max = job.get("salary_max", 0)
        salary_str = f"${salary_min:,} - ${salary_max:,}/año" if salary_min else "Salario no especificado"
        remote_str = "🏠 Remoto" if job.get("remote") else "🏢 Presencial"
        visa_str = "✅ Patrocina visa" if job.get("visa_sponsorship") else ""

        lines.append(
            f"""
*{i}. {job.get('title', 'Puesto')}*
🏢 {job.get('company', 'Empresa')}
📍 {job.get('location', '')} {remote_str}
💰 {salary_str}
{visa_str}
🔗 [Aplicar]({job.get('apply_url', '#')})
"""
        )

    return "\n".join(lines)


def format_school_list(schools: list[dict], limit: int = 5) -> str:
    """Formatea lista de colegios para mostrar"""
    if not schools:
        return "No se encontraron colegios."

    lines = ["🎓 *OPCIONES DE COLEGIOS*\n"]

    for i, school in enumerate(schools[:limit], 1):
        rating = school.get("rating", 0)
        stars = "⭐" * int(rating / 2)
        type_emoji = {"public": "🏫", "private": "🎒", "charter": "📚"}.get(
            school.get("school_type", ""), "🏫"
        )

        lines.append(
            f"""
*{i}. {type_emoji} {school.get('name', 'Colegio')}*
📍 {school.get('address', '')}
📊 Rating: {rating}/10 {stars}
📚 Grados: {school.get('grade_range', '')}
👨‍🎓 {school.get('student_count', 0):,} estudiantes
🌟 {', '.join(school.get('programs', [])[:3])}
🔗 [Sitio web]({school.get('website', '#')})
"""
        )

    return "\n".join(lines)


def format_business_list(businesses: list[dict], limit: int = 5) -> str:
    """Formatea lista de negocios para mostrar"""
    if not businesses:
        return "No se encontraron negocios en venta."

    lines = ["🏪 *NEGOCIOS EN VENTA*\n"]
    lines.append("_Due diligence disponible por $100 USD_\n")

    for i, biz in enumerate(businesses[:limit], 1):
        price = biz.get("asking_price", 0)
        revenue = biz.get("annual_revenue", 0)
        profit = biz.get("annual_profit", 0)
        roi = (profit / price * 100) if price > 0 else 0

        lines.append(
            f"""
*{i}. {biz.get('name', 'Negocio')}*
📍 {biz.get('location', '')}
💰 Precio: ${price:,}
📈 Ingresos: ${revenue:,}/año
💵 Ganancia: ${profit:,}/año
📊 ROI: {roi:.1f}%
👥 {biz.get('employees', 0)} empleados | 📅 {biz.get('years_established', 0)} años
🔗 [Ver detalles]({biz.get('listing_url', '#')})
"""
        )

    return "\n".join(lines)
