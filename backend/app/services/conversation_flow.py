"""
MigPAL Conversation Flow Engine - Motor de Flujo Conversacional
Sistema de state machine para guiar la conversación de manera empática y estructurada

FILOSOFÍA:
"La visa es el VEHÍCULO, no el DESTINO. Primero define el destino (plan de vida), luego el vehículo (visa)."

FLUJO:
1. DESCUBRIMIENTO - ¿Por qué migrar? ¿Familia? ¿Conexiones en USA?
2. PLAN DE VIDA - ¿Trabajo o negocio? ¿Industria? ¿Tipo de vida?
3. UBICACIÓN - Estado → Ciudad → Barrio (de lo general a lo particular)
4. VISA - Basado en el plan de vida, recomendar la visa adecuada
5. EJECUCIÓN - Diagnóstico, documentos, aplicación

PRINCIPIOS:
- UNA pregunta a la vez
- Respuestas cortas (3-5 líneas)
- Empatía genuina
- NUNCA repetir "¿Te quedó claro?"
- NUNCA mencionar abogados
"""

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Estados del flujo conversacional"""

    # FASE 0: BIENVENIDA
    WELCOME = auto()

    # FASE 1: DESCUBRIMIENTO
    DISCOVERY_WHY = auto()  # ¿Por qué quieres migrar?
    DISCOVERY_DREAM = auto()  # ¿Qué sueño tienes en USA?
    DISCOVERY_FAMILY = auto()  # ¿Tienes familia? ¿Migran contigo?
    DISCOVERY_USA_CONNECTIONS = auto()  # ¿Tienes familia/amigos en USA?
    DISCOVERY_NEAR_FAMILY = auto()  # ¿Quieres vivir cerca de ellos?

    # FASE 2: PLAN DE VIDA (TRABAJO/NEGOCIO PRIMERO)
    LIFE_WORK_OR_BUSINESS = auto()  # ¿Trabajo o negocio?
    LIFE_INDUSTRY = auto()  # ¿En qué industria?
    LIFE_BUSINESS_TYPE = auto()  # Si negocio: ¿Qué tipo?
    LIFE_BUSINESS_BUDGET = auto()  # Si negocio: ¿Presupuesto de inversión?
    LIFE_SALARY_EXPECTATION = auto()  # Si trabajo: ¿Expectativa salarial?
    LIFE_REMOTE_POSSIBLE = auto()  # ¿Trabajo remoto es opción?

    # FASE 3: PREFERENCIAS DE UBICACIÓN
    LOCATION_REGION = auto()  # ¿Qué región de USA?
    LOCATION_CLIMATE = auto()  # ¿Qué clima prefieres?
    LOCATION_CITY_SIZE = auto()  # ¿Ciudad grande, mediana, pequeña?
    LOCATION_PRIORITIES = auto()  # ¿Qué es más importante? (costo, seguridad, etc.)
    LOCATION_LATINO_COMMUNITY = auto()  # ¿Importa comunidad latina?

    # FASE 4: DEFINIR PESOS PARA SCORING
    SCORING_SETUP = auto()  # Explicar sistema de scoring
    SCORING_WEIGHTS = auto()  # Definir pesos de parámetros

    # FASE 5: RECOMENDACIÓN DE ESTADOS
    STATE_RECOMMENDATION = auto()  # Mostrar estados recomendados
    STATE_SELECTION = auto()  # Elegir estado

    # FASE 6: RECOMENDACIÓN DE CIUDADES
    CITY_RECOMMENDATION = auto()  # Mostrar ciudades del estado
    CITY_EXPLORATION = auto()  # Explorar ciudad (una por una)
    CITY_SELECTION = auto()  # Elegir ciudad

    # FASE 7: RECOMENDACIÓN DE BARRIOS
    NEIGHBORHOOD_RECOMMENDATION = auto()  # Mostrar barrios de la ciudad
    NEIGHBORHOOD_EXPLORATION = auto()  # Explorar barrio (uno por uno)
    NEIGHBORHOOD_SELECTION = auto()  # Elegir barrio

    # FASE 8: VIVIENDA
    HOUSING_PREFERENCES = auto()  # Preferencias de vivienda
    HOUSING_BUDGET = auto()  # Presupuesto
    HOUSING_SCORING_WEIGHTS = auto()  # Pesos para scoring de viviendas
    HOUSING_SEARCH = auto()  # Buscar viviendas
    HOUSING_EXPLORATION = auto()  # Ver viviendas una por una
    HOUSING_SELECTION = auto()  # Elegir vivienda favorita

    # FASE 9: TRABAJO/NEGOCIO ESPECÍFICO
    JOB_PREFERENCES = auto()  # Preferencias de trabajo
    JOB_SCORING_WEIGHTS = auto()  # Pesos para scoring de trabajos
    JOB_SEARCH = auto()  # Buscar trabajos
    JOB_EXPLORATION = auto()  # Ver trabajos uno por uno
    JOB_SELECTION = auto()  # Elegir trabajos favoritos

    # FASE 10: EDUCACIÓN (si tiene hijos)
    SCHOOL_PREFERENCES = auto()  # Preferencias de escuelas
    SCHOOL_SCORING_WEIGHTS = auto()  # Pesos para scoring de escuelas
    SCHOOL_SEARCH = auto()  # Buscar escuelas
    SCHOOL_EXPLORATION = auto()  # Ver escuelas una por una
    SCHOOL_SELECTION = auto()  # Elegir escuelas favoritas

    # FASE 11: VISA
    VISA_ANALYSIS = auto()  # Analizar perfil para visa
    VISA_RECOMMENDATION = auto()  # Recomendar visa basada en plan
    VISA_EXPLANATION = auto()  # Explicar requisitos
    VISA_PROBABILITY = auto()  # Dar probabilidad

    # FASE 12: RESUMEN Y DIAGNÓSTICO
    PLAN_SUMMARY = auto()  # Resumen del plan completo
    DIAGNOSIS_OFFER = auto()  # Ofrecer diagnóstico ($50)
    DIAGNOSIS_ACCEPTED = auto()  # Diagnóstico aceptado

    # FASE 13: EJECUCIÓN
    PROFILING = auto()  # Perfilamiento ($50)
    DOCUMENT_REVIEW = auto()  # Revisión documental ($200)
    MIGRATION_PLAN = auto()  # Plan de migración ($100)
    EXECUTION = auto()  # Ejecución final


@dataclass
class ScoringWeights:
    """Pesos personalizados para scoring"""

    # Pesos para ciudades/estados
    costo_vida: int = 15
    seguridad: int = 15
    oportunidades_laborales: int = 20
    educacion: int = 10
    salud: int = 10
    transporte: int = 5
    comunidad_latina: int = 10
    clima: int = 10
    calidad_vida: int = 5

    # Pesos para viviendas
    precio: int = 25
    ubicacion: int = 20
    tamano: int = 15
    amenidades: int = 10
    seguridad_barrio: int = 15
    cercania_trabajo: int = 10
    cercania_escuelas: int = 5

    # Pesos para trabajos
    salario: int = 25
    beneficios: int = 15
    crecimiento: int = 15
    cultura_empresa: int = 10
    ubicacion_trabajo: int = 10
    flexibilidad: int = 10
    visa_sponsorship: int = 15

    # Pesos para escuelas
    rating_academico: int = 25
    programas_especiales: int = 15
    ratio_estudiante_profesor: int = 15
    actividades_extra: int = 10
    diversidad: int = 10
    seguridad_escuela: int = 15
    distancia: int = 10


@dataclass
class ConversationContext:
    """Contexto completo de la conversación"""

    user_id: int
    current_state: ConversationState = ConversationState.WELCOME

    # Descubrimiento
    why_migrate: str = ""
    dream_in_usa: str = ""
    has_family: bool = False
    family_migrating: bool = False
    family_count: int = 0
    children_ages: list[int] = field(default_factory=list)
    has_usa_connections: bool = False
    usa_connections_location: str = ""
    wants_near_connections: bool = False

    # Plan de vida
    work_or_business: str = ""  # "trabajo", "negocio", "ambos", "remoto"
    industry: str = ""
    business_type: str = ""
    business_budget: int = 0
    salary_expectation: int = 0
    remote_possible: bool = False

    # Preferencias de ubicación
    preferred_regions: list[str] = field(default_factory=list)
    preferred_climates: list[str] = field(default_factory=list)
    city_size: str = ""
    priorities: list[str] = field(default_factory=list)
    latino_community_importance: str = ""

    # Scoring weights personalizados
    scoring_weights: ScoringWeights = field(default_factory=ScoringWeights)

    # Selecciones
    selected_state: str = ""
    selected_city: str = ""
    selected_neighborhood: str = ""
    selected_housing: dict = field(default_factory=dict)
    selected_jobs: list[dict] = field(default_factory=list)
    selected_schools: list[dict] = field(default_factory=list)

    # Visa
    recommended_visa: str = ""
    visa_probability: int = 0

    # Exploración actual (para mostrar uno por uno)
    current_exploration_index: int = 0
    exploration_items: list[dict] = field(default_factory=list)

    # Historial de estados visitados
    state_history: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convierte a diccionario para persistencia"""
        return {
            "user_id": self.user_id,
            "current_state": self.current_state.name,
            "why_migrate": self.why_migrate,
            "dream_in_usa": self.dream_in_usa,
            "has_family": self.has_family,
            "family_migrating": self.family_migrating,
            "family_count": self.family_count,
            "children_ages": self.children_ages,
            "has_usa_connections": self.has_usa_connections,
            "usa_connections_location": self.usa_connections_location,
            "wants_near_connections": self.wants_near_connections,
            "work_or_business": self.work_or_business,
            "industry": self.industry,
            "business_type": self.business_type,
            "business_budget": self.business_budget,
            "salary_expectation": self.salary_expectation,
            "remote_possible": self.remote_possible,
            "preferred_regions": self.preferred_regions,
            "preferred_climates": self.preferred_climates,
            "city_size": self.city_size,
            "priorities": self.priorities,
            "latino_community_importance": self.latino_community_importance,
            "selected_state": self.selected_state,
            "selected_city": self.selected_city,
            "selected_neighborhood": self.selected_neighborhood,
            "selected_housing": self.selected_housing,
            "selected_jobs": self.selected_jobs,
            "selected_schools": self.selected_schools,
            "recommended_visa": self.recommended_visa,
            "visa_probability": self.visa_probability,
            "current_exploration_index": self.current_exploration_index,
            "state_history": self.state_history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationContext":
        """Crea desde diccionario"""
        ctx = cls(user_id=data.get("user_id", 0))
        ctx.current_state = ConversationState[data.get("current_state", "WELCOME")]
        ctx.why_migrate = data.get("why_migrate", "")
        ctx.dream_in_usa = data.get("dream_in_usa", "")
        ctx.has_family = data.get("has_family", False)
        ctx.family_migrating = data.get("family_migrating", False)
        ctx.family_count = data.get("family_count", 0)
        ctx.children_ages = data.get("children_ages", [])
        ctx.has_usa_connections = data.get("has_usa_connections", False)
        ctx.usa_connections_location = data.get("usa_connections_location", "")
        ctx.wants_near_connections = data.get("wants_near_connections", False)
        ctx.work_or_business = data.get("work_or_business", "")
        ctx.industry = data.get("industry", "")
        ctx.business_type = data.get("business_type", "")
        ctx.business_budget = data.get("business_budget", 0)
        ctx.salary_expectation = data.get("salary_expectation", 0)
        ctx.remote_possible = data.get("remote_possible", False)
        ctx.preferred_regions = data.get("preferred_regions", [])
        ctx.preferred_climates = data.get("preferred_climates", [])
        ctx.city_size = data.get("city_size", "")
        ctx.priorities = data.get("priorities", [])
        ctx.latino_community_importance = data.get("latino_community_importance", "")
        ctx.selected_state = data.get("selected_state", "")
        ctx.selected_city = data.get("selected_city", "")
        ctx.selected_neighborhood = data.get("selected_neighborhood", "")
        ctx.selected_housing = data.get("selected_housing", {})
        ctx.selected_jobs = data.get("selected_jobs", [])
        ctx.selected_schools = data.get("selected_schools", [])
        ctx.recommended_visa = data.get("recommended_visa", "")
        ctx.visa_probability = data.get("visa_probability", 0)
        ctx.current_exploration_index = data.get("current_exploration_index", 0)
        ctx.state_history = data.get("state_history", [])
        return ctx


# ============== PREGUNTAS POR ESTADO ==============

STATE_QUESTIONS = {
    ConversationState.WELCOME: {
        "message": "¡Hola {name}! 👋 Soy MigPAL, tu consultor de migración.\n\nMi trabajo es ayudarte a construir tu nueva vida en USA, paso a paso.\n\n¿Listo para empezar?",
        "options": [
            ("si", "✅ ¡Sí, empecemos!"),
            ("info", "ℹ️ Primero cuéntame más sobre MigPAL"),
        ],
    },
    ConversationState.DISCOVERY_WHY: {
        "message": "Perfecto, {name}. Antes de hablar de visas o ciudades, quiero entenderte.\n\n¿Qué te motiva a migrar a USA? 🤔",
        "options": [
            ("calidad_vida", "🌟 Mejor calidad de vida"),
            ("oportunidades", "💼 Oportunidades laborales"),
            ("negocio", "🚀 Montar mi negocio"),
            ("familia", "👨‍👩‍👧‍👦 Reunirme con familia"),
            ("educacion", "🎓 Educación para mis hijos"),
            ("seguridad", "🛡️ Seguridad"),
            ("otro", "📝 Otro motivo"),
        ],
        "allow_text": True,
    },
    ConversationState.DISCOVERY_DREAM: {
        "message": "Entiendo, {why_migrate_text}.\n\n¿Cómo te imaginas tu vida en USA en 5 años? ¿Cuál es tu sueño? 💭",
        "allow_text": True,
        "examples": [
            "Tener mi casa propia y un negocio estable",
            "Trabajar en una empresa tech y darle buena educación a mis hijos",
            "Vivir tranquilo cerca de la playa con mi familia",
        ],
    },
    ConversationState.DISCOVERY_FAMILY: {
        "message": "Me encanta ese sueño, {name}. 🌟\n\n¿Tienes familia que migraría contigo?",
        "options": [
            ("solo", "👤 Voy solo/a"),
            ("pareja", "👫 Con mi pareja"),
            ("familia_hijos", "👨‍👩‍👧‍👦 Con pareja e hijos"),
            ("hijos_solo", "👨‍👧‍👦 Solo con mis hijos"),
        ],
    },
    ConversationState.DISCOVERY_USA_CONNECTIONS: {
        "message": "Perfecto. ¿Tienes familia o amigos cercanos viviendo en USA?",
        "options": [
            ("si_familia", "👨‍👩‍👧 Sí, familia directa"),
            ("si_amigos", "🤝 Sí, amigos cercanos"),
            ("si_ambos", "👥 Familia y amigos"),
            ("no", "❌ No tengo a nadie allá"),
        ],
    },
    ConversationState.DISCOVERY_NEAR_FAMILY: {
        "message": "¿En qué ciudad/estado viven? ¿Te gustaría vivir cerca de ellos?",
        "allow_text": True,
        "options": [
            ("si_cerca", "✅ Sí, quiero vivir cerca"),
            ("no_importa", "🔄 No necesariamente"),
            ("lejos", "📍 Prefiero otra zona"),
        ],
    },
    # PLAN DE VIDA - TRABAJO/NEGOCIO
    ConversationState.LIFE_WORK_OR_BUSINESS: {
        "message": "Ahora hablemos de lo más importante: tu sustento económico. 💰\n\nEsto determinará mucho sobre dónde vivir y qué visa necesitas.\n\n¿Qué planeas hacer en USA?",
        "options": [
            ("trabajo", "💼 Buscar empleo"),
            ("negocio", "🚀 Montar mi propio negocio"),
            ("remoto", "💻 Ya tengo trabajo remoto"),
            ("ambos", "🔄 Empleo + proyecto propio"),
        ],
    },
    ConversationState.LIFE_INDUSTRY: {
        "message": "¿En qué industria o sector te desempeñas?",
        "options": [
            ("tech", "💻 Tecnología / Software"),
            ("finanzas", "💰 Finanzas / Banca"),
            ("salud", "🏥 Salud / Medicina"),
            ("educacion", "📚 Educación"),
            ("construccion", "🏗️ Construcción"),
            ("comercio", "🛒 Comercio / Retail"),
            ("restaurantes", "🍽️ Restaurantes / Hospitalidad"),
            ("transporte", "🚚 Transporte / Logística"),
            ("legal", "⚖️ Legal"),
            ("marketing", "📢 Marketing / Publicidad"),
            ("otro", "📋 Otro"),
        ],
        "allow_text": True,
    },
    ConversationState.LIFE_BUSINESS_TYPE: {
        "message": "¡Excelente! Emprender en USA es una gran decisión. 🚀\n\n¿Qué tipo de negocio te interesa?",
        "options": [
            ("restaurante", "🍽️ Restaurante / Comida"),
            ("tienda", "🛒 Tienda / Retail"),
            ("servicios", "🛎️ Servicios profesionales"),
            ("tech", "💻 Startup tecnológica"),
            ("franquicia", "🏪 Franquicia"),
            ("importacion", "📦 Importación / Exportación"),
            ("bienes_raices", "🏠 Bienes raíces"),
            ("otro", "📋 Otro"),
        ],
        "allow_text": True,
    },
    ConversationState.LIFE_BUSINESS_BUDGET: {
        "message": "¿Cuánto capital tienes disponible para invertir en tu negocio?",
        "options": [
            ("50k", "💵 $50,000 - $100,000"),
            ("100k", "💵💵 $100,000 - $250,000"),
            ("250k", "💵💵💵 $250,000 - $500,000"),
            ("500k", "💎 $500,000+"),
            ("no_seguro", "🤔 No estoy seguro aún"),
        ],
    },
    ConversationState.LIFE_SALARY_EXPECTATION: {
        "message": "¿Cuál es tu expectativa salarial anual en USA?",
        "options": [
            ("50k", "💵 $50,000 - $75,000"),
            ("75k", "💵💵 $75,000 - $100,000"),
            ("100k", "💵💵💵 $100,000 - $150,000"),
            ("150k", "💎 $150,000+"),
            ("no_seguro", "🤔 No estoy seguro"),
        ],
    },
    # PREFERENCIAS DE UBICACIÓN
    ConversationState.LOCATION_REGION: {
        "message": "Ahora definamos dónde te gustaría vivir. 🗺️\n\n¿Qué regiones de USA te interesan?",
        "multi_select": True,
        "options": [
            ("costa_este", "🌅 Costa Este (Florida, NY, Boston)"),
            ("costa_oeste", "🌊 Costa Oeste (California, Seattle)"),
            ("sur", "🤠 Sur (Texas, Georgia, Carolina)"),
            ("midwest", "🌾 Midwest (Chicago, Denver)"),
            ("sin_preferencia", "🔄 Sin preferencia"),
        ],
    },
    ConversationState.LOCATION_CLIMATE: {
        "message": "¿Qué clima prefieres?",
        "multi_select": True,
        "options": [
            ("calido", "☀️ Cálido todo el año"),
            ("templado", "🌤️ Templado (4 estaciones suaves)"),
            ("frio", "❄️ Frío (con nieve)"),
            ("sin_preferencia", "🔄 Me adapto a cualquiera"),
        ],
    },
    ConversationState.LOCATION_CITY_SIZE: {
        "message": "¿Qué tamaño de ciudad prefieres?",
        "options": [
            ("grande", "🏙️ Ciudad grande (+1M habitantes)"),
            ("mediana", "🌆 Ciudad mediana (100K - 1M)"),
            ("pequena", "🏘️ Ciudad pequeña (<100K)"),
            ("suburbio", "🏡 Suburbio de ciudad grande"),
        ],
    },
    ConversationState.LOCATION_PRIORITIES: {
        "message": "¿Qué es MÁS IMPORTANTE para ti? (Elige hasta 3)",
        "multi_select": True,
        "max_select": 3,
        "options": [
            ("costo", "💰 Bajo costo de vida"),
            ("seguridad", "🛡️ Seguridad"),
            ("trabajo", "💼 Oportunidades laborales"),
            ("educacion", "🎓 Buenas escuelas"),
            ("salud", "🏥 Acceso a salud"),
            ("transporte", "🚇 Transporte público"),
            ("comunidad", "🤝 Comunidad latina"),
            ("clima", "☀️ Buen clima"),
        ],
    },
    ConversationState.LOCATION_LATINO_COMMUNITY: {
        "message": "¿Qué tan importante es tener comunidad latina cerca?",
        "options": [
            ("muy_importante", "⭐⭐⭐ Muy importante"),
            ("importante", "⭐⭐ Importante"),
            ("poco_importante", "⭐ Poco importante"),
            ("no_importa", "🔄 No me importa"),
        ],
    },
    # SCORING
    ConversationState.SCORING_SETUP: {
        "message": "Ahora vamos a personalizar tu búsqueda. 🎯\n\nTe mostraré opciones de estados, ciudades, barrios y viviendas.\n\nCada opción tendrá un SCORE calculado según TUS prioridades.\n\n¿Quieres ajustar los pesos de cada factor o usar los valores por defecto?",
        "options": [
            ("personalizar", "⚙️ Quiero personalizar los pesos"),
            ("default", "✅ Usar valores por defecto"),
        ],
    },
}


# ============== MOTOR DE FLUJO ==============


class ConversationFlowEngine:
    """Motor principal del flujo conversacional"""

    def __init__(self):
        self.contexts: dict[int, ConversationContext] = {}

    def get_context(self, user_id: int) -> ConversationContext:
        """Obtiene o crea el contexto de un usuario"""
        if user_id not in self.contexts:
            self.contexts[user_id] = ConversationContext(user_id=user_id)
        return self.contexts[user_id]

    def set_context(self, user_id: int, context: ConversationContext):
        """Establece el contexto de un usuario"""
        self.contexts[user_id] = context

    def get_current_question(self, user_id: int, user_name: str = "") -> dict[str, Any]:
        """Obtiene la pregunta actual para el usuario"""
        ctx = self.get_context(user_id)
        state = ctx.current_state

        if state not in STATE_QUESTIONS:
            return {
                "message": "Continuemos con tu plan de migración. ¿En qué puedo ayudarte?",
                "options": [],
                "allow_text": True,
            }

        question = STATE_QUESTIONS[state].copy()

        # Reemplazar variables en el mensaje
        message = question["message"]
        message = message.replace("{name}", user_name or "amigo")

        if "{why_migrate_text}" in message:
            why_text = self._get_why_migrate_text(ctx.why_migrate)
            message = message.replace("{why_migrate_text}", why_text)

        question["message"] = message
        question["state"] = state.name

        return question

    def _get_why_migrate_text(self, why: str) -> str:
        """Convierte el código de motivación a texto legible"""
        texts = {
            "calidad_vida": "buscas mejor calidad de vida",
            "oportunidades": "buscas mejores oportunidades laborales",
            "negocio": "quieres emprender tu propio negocio",
            "familia": "quieres reunirte con tu familia",
            "educacion": "buscas mejor educación para tus hijos",
            "seguridad": "buscas más seguridad",
        }
        return texts.get(why, why)

    def process_response(
        self, user_id: int, response: str, selected_options: list[str] = None
    ) -> tuple[ConversationState, str]:
        """
        Procesa la respuesta del usuario y avanza el estado

        Returns:
            Tuple[nuevo_estado, mensaje_de_transición]
        """
        ctx = self.get_context(user_id)
        current_state = ctx.current_state

        # Guardar en historial
        ctx.state_history.append(current_state.name)

        # Procesar según el estado actual
        next_state, transition_msg = self._process_state_response(
            ctx, current_state, response, selected_options
        )

        ctx.current_state = next_state
        self.set_context(user_id, ctx)

        return next_state, transition_msg

    def _process_state_response(
        self, ctx: ConversationContext, state: ConversationState, response: str, options: list[str] = None
    ) -> tuple[ConversationState, str]:
        """Procesa la respuesta según el estado actual"""

        # WELCOME
        if state == ConversationState.WELCOME:
            if response == "si" or "si" in (options or []):
                return ConversationState.DISCOVERY_WHY, ""
            else:
                return (
                    ConversationState.WELCOME,
                    "MigPAL es tu consultor de migración. Te ayudo a planificar tu nueva vida en USA paso a paso. ¿Empezamos?",
                )

        # DISCOVERY_WHY
        elif state == ConversationState.DISCOVERY_WHY:
            ctx.why_migrate = response if response else (options[0] if options else "")
            return ConversationState.DISCOVERY_DREAM, ""

        # DISCOVERY_DREAM
        elif state == ConversationState.DISCOVERY_DREAM:
            ctx.dream_in_usa = response
            return ConversationState.DISCOVERY_FAMILY, ""

        # DISCOVERY_FAMILY
        elif state == ConversationState.DISCOVERY_FAMILY:
            if response == "solo":
                ctx.has_family = False
                ctx.family_migrating = False
            else:
                ctx.has_family = True
                ctx.family_migrating = True
                if response == "pareja":
                    ctx.family_count = 2
                elif response in ["familia_hijos", "hijos_solo"]:
                    ctx.family_count = 3  # Se ajustará después
            return ConversationState.DISCOVERY_USA_CONNECTIONS, ""

        # DISCOVERY_USA_CONNECTIONS
        elif state == ConversationState.DISCOVERY_USA_CONNECTIONS:
            if response == "no":
                ctx.has_usa_connections = False
                return ConversationState.LIFE_WORK_OR_BUSINESS, ""
            else:
                ctx.has_usa_connections = True
                return ConversationState.DISCOVERY_NEAR_FAMILY, ""

        # DISCOVERY_NEAR_FAMILY
        elif state == ConversationState.DISCOVERY_NEAR_FAMILY:
            if options:
                ctx.wants_near_connections = "si_cerca" in options
            if response and not response.startswith(("si", "no")):
                ctx.usa_connections_location = response
            return ConversationState.LIFE_WORK_OR_BUSINESS, ""

        # LIFE_WORK_OR_BUSINESS
        elif state == ConversationState.LIFE_WORK_OR_BUSINESS:
            ctx.work_or_business = response
            if response == "negocio":
                return ConversationState.LIFE_BUSINESS_TYPE, ""
            else:
                return ConversationState.LIFE_INDUSTRY, ""

        # LIFE_INDUSTRY
        elif state == ConversationState.LIFE_INDUSTRY:
            ctx.industry = response
            if ctx.work_or_business == "trabajo":
                return ConversationState.LIFE_SALARY_EXPECTATION, ""
            else:
                return ConversationState.LOCATION_REGION, ""

        # LIFE_BUSINESS_TYPE
        elif state == ConversationState.LIFE_BUSINESS_TYPE:
            ctx.business_type = response
            return ConversationState.LIFE_BUSINESS_BUDGET, ""

        # LIFE_BUSINESS_BUDGET
        elif state == ConversationState.LIFE_BUSINESS_BUDGET:
            budget_map = {
                "50k": 75000,
                "100k": 175000,
                "250k": 375000,
                "500k": 500000,
            }
            ctx.business_budget = budget_map.get(response, 0)
            return ConversationState.LIFE_INDUSTRY, ""

        # LIFE_SALARY_EXPECTATION
        elif state == ConversationState.LIFE_SALARY_EXPECTATION:
            salary_map = {
                "50k": 62500,
                "75k": 87500,
                "100k": 125000,
                "150k": 150000,
            }
            ctx.salary_expectation = salary_map.get(response, 0)
            return ConversationState.LOCATION_REGION, ""

        # LOCATION_REGION
        elif state == ConversationState.LOCATION_REGION:
            ctx.preferred_regions = options if options else [response]
            return ConversationState.LOCATION_CLIMATE, ""

        # LOCATION_CLIMATE
        elif state == ConversationState.LOCATION_CLIMATE:
            ctx.preferred_climates = options if options else [response]
            return ConversationState.LOCATION_CITY_SIZE, ""

        # LOCATION_CITY_SIZE
        elif state == ConversationState.LOCATION_CITY_SIZE:
            ctx.city_size = response
            return ConversationState.LOCATION_PRIORITIES, ""

        # LOCATION_PRIORITIES
        elif state == ConversationState.LOCATION_PRIORITIES:
            ctx.priorities = options if options else [response]
            return ConversationState.LOCATION_LATINO_COMMUNITY, ""

        # LOCATION_LATINO_COMMUNITY
        elif state == ConversationState.LOCATION_LATINO_COMMUNITY:
            ctx.latino_community_importance = response
            return ConversationState.SCORING_SETUP, ""

        # SCORING_SETUP
        elif state == ConversationState.SCORING_SETUP:
            if response == "personalizar":
                return ConversationState.SCORING_WEIGHTS, ""
            else:
                return ConversationState.STATE_RECOMMENDATION, ""

        # Default: mantener estado actual
        return state, "No entendí tu respuesta. ¿Puedes intentar de nuevo?"

    def can_skip_to_state(self, user_id: int, target_state: ConversationState) -> bool:
        """Verifica si se puede saltar a un estado específico"""
        ctx = self.get_context(user_id)

        # Definir dependencias de estados
        dependencies = {
            ConversationState.STATE_RECOMMENDATION: [
                ConversationState.LIFE_WORK_OR_BUSINESS,
                ConversationState.LOCATION_REGION,
            ],
            ConversationState.CITY_RECOMMENDATION: [
                ConversationState.STATE_SELECTION,
            ],
            ConversationState.VISA_ANALYSIS: [
                ConversationState.LIFE_WORK_OR_BUSINESS,
            ],
        }

        required = dependencies.get(target_state, [])
        for req in required:
            if req.name not in ctx.state_history:
                return False

        return True

    def get_progress_percentage(self, user_id: int) -> int:
        """Calcula el porcentaje de progreso en el flujo"""
        ctx = self.get_context(user_id)

        # Estados totales aproximados hasta diagnóstico
        total_states = 20
        current_index = list(ConversationState).index(ctx.current_state)

        return min(100, int((current_index / total_states) * 100))

    def get_summary(self, user_id: int) -> dict[str, Any]:
        """Obtiene un resumen del contexto actual"""
        ctx = self.get_context(user_id)

        return {
            "estado_actual": ctx.current_state.name,
            "progreso": f"{self.get_progress_percentage(user_id)}%",
            "motivacion": ctx.why_migrate,
            "sueno": ctx.dream_in_usa,
            "familia": ctx.family_count if ctx.has_family else "Solo",
            "plan_laboral": ctx.work_or_business,
            "industria": ctx.industry,
            "regiones": ctx.preferred_regions,
            "estado_seleccionado": ctx.selected_state,
            "ciudad_seleccionada": ctx.selected_city,
            "visa_recomendada": ctx.recommended_visa,
        }


# Instancia global del motor
flow_engine = ConversationFlowEngine()
