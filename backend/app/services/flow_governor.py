"""
MigPAL Flow Governor - SEGMENTO 2/3: GOBIERNO DEL FLUJO (ANTI-BOT)
===================================================================
La conversación manda, no los formularios ni los states.

REGLAS DURAS:
1. Formularios solo si son necesarios y máx 1 cada 5 interacciones
2. Si el usuario escribe algo fuera del prompt, se interpreta, NO se ignora
3. UNDERSTANDING es gatekeeper global: sin confirmación, no se avanza
4. Prohibido recomendar visas sin: quién migra + edades + familia + motivo + restricciones
5. States sirven al diálogo, no lo controlan
6. El modelo decide qué preguntar, el sistema solo bloquea errores graves
7. MigPAL debe sentirse humano, no secuencial

Este módulo implementa:
- FormThrottler: Limita formularios a 1 cada 5 interacciones
- InputInterpreter: Interpreta CUALQUIER input del usuario
- UnderstandingGatekeeper: Valida comprensión antes de avanzar
- VisaRecommendationGuard: Bloquea recomendaciones sin datos mínimos
- ConversationDirector: El modelo decide, el sistema solo valida
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ============== CONFIGURACIÓN ==============

# Máximo de formularios por cada N interacciones
MAX_FORMS_PER_INTERACTIONS = 1
INTERACTIONS_WINDOW = 5

# Tiempo mínimo entre formularios (segundos)
MIN_TIME_BETWEEN_FORMS = 30

# Datos mínimos requeridos para recomendar visa
VISA_REQUIRED_DATA = {
    "who_migrates": ["name", "age", "nationality"],
    "family": ["has_family", "family_count", "children_ages"],
    "motive": ["migration_reason", "dream_in_usa"],
    "restrictions": ["visa_history", "criminal_record", "health_conditions"],
}


# ============== FORM THROTTLER ==============


class FormThrottler:
    """
    Limita la frecuencia de formularios para mantener la conversación natural.
    Regla: Máximo 1 formulario cada 5 interacciones.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._user_interactions = {}
            cls._instance._user_forms = {}
            cls._instance._last_form_time = {}
        return cls._instance

    def record_interaction(self, user_id: int, is_form: bool = False):
        """Registra una interacción del usuario"""
        now = datetime.now()

        if user_id not in self._user_interactions:
            self._user_interactions[user_id] = []
            self._user_forms[user_id] = []

        self._user_interactions[user_id].append(now)

        if is_form:
            self._user_forms[user_id].append(now)
            self._last_form_time[user_id] = now

        # Limpiar interacciones antiguas (más de 1 hora)
        cutoff = now - timedelta(hours=1)
        self._user_interactions[user_id] = [t for t in self._user_interactions[user_id] if t > cutoff]
        self._user_forms[user_id] = [t for t in self._user_forms[user_id] if t > cutoff]

    def can_show_form(self, user_id: int) -> tuple[bool, str]:
        """
        Verifica si se puede mostrar un formulario.
        Returns: (can_show, reason)
        """
        now = datetime.now()

        # Si no hay historial, permitir
        if user_id not in self._user_interactions:
            return True, "first_interaction"

        # Contar interacciones recientes
        recent_interactions = len(self._user_interactions[user_id])
        recent_forms = len(self._user_forms[user_id])

        # Verificar ratio de formularios
        if recent_interactions >= INTERACTIONS_WINDOW:
            if recent_forms >= MAX_FORMS_PER_INTERACTIONS:
                return False, f"too_many_forms: {recent_forms} forms in {recent_interactions} interactions"

        # Verificar tiempo desde último formulario
        if user_id in self._last_form_time:
            time_since_form = (now - self._last_form_time[user_id]).total_seconds()
            if time_since_form < MIN_TIME_BETWEEN_FORMS:
                return False, f"too_soon: {time_since_form:.0f}s since last form"

        return True, "allowed"

    def get_alternative_approach(self, user_id: int, form_type: str, lang: str = "es") -> str:
        """
        Cuando no se puede mostrar formulario, sugiere enfoque conversacional.
        """
        alternatives = {
            "es": {
                "name": "Cuéntame, ¿cómo te llamas?",
                "birth_date": "¿En qué año naciste?",
                "nationality": "¿De qué país eres?",
                "profession": "¿A qué te dedicas?",
                "education": "Cuéntame sobre tu formación académica.",
                "family": "¿Viajas solo o con familia?",
                "visa_history": "¿Has tenido visas antes?",
                "default": "Cuéntame más sobre ti.",
            },
            "en": {
                "name": "Tell me, what's your name?",
                "birth_date": "What year were you born?",
                "nationality": "What country are you from?",
                "profession": "What do you do for work?",
                "education": "Tell me about your education.",
                "family": "Are you traveling alone or with family?",
                "visa_history": "Have you had visas before?",
                "default": "Tell me more about yourself.",
            },
        }

        lang_alternatives = alternatives.get(lang, alternatives["es"])
        return lang_alternatives.get(form_type, lang_alternatives["default"])


# ============== INPUT INTERPRETER ==============


class InputType(Enum):
    """Tipos de input del usuario"""

    DIRECT_ANSWER = "direct_answer"  # Respuesta directa al prompt
    QUESTION = "question"  # Pregunta del usuario
    CORRECTION = "correction"  # Corrección de dato anterior
    CONCERN = "concern"  # Preocupación o duda
    OFF_TOPIC = "off_topic"  # Fuera de tema pero válido
    PERSONAL_INFO = "personal_info"  # Información personal espontánea
    CONFIRMATION = "confirmation"  # Confirmación (sí, ok, etc.)
    REJECTION = "rejection"  # Rechazo (no, después, etc.)
    GREETING = "greeting"  # Saludo
    GRATITUDE = "gratitude"  # Agradecimiento
    FRUSTRATION = "frustration"  # Frustración
    UNKNOWN = "unknown"  # No clasificado


@dataclass
class InterpretedInput:
    """Resultado de interpretar el input del usuario"""

    input_type: InputType
    confidence: float
    extracted_data: dict[str, Any] = field(default_factory=dict)
    suggested_response: str = ""
    should_advance: bool = False
    requires_clarification: bool = False
    original_text: str = ""


class InputInterpreter:
    """
    Interpreta CUALQUIER input del usuario, no solo respuestas directas.
    Regla: Si el usuario escribe algo fuera del prompt, se interpreta, NO se ignora.
    """

    # Patrones para detectar tipos de input
    PATTERNS = {
        InputType.QUESTION: [
            r"\?$",
            r"^¿",
            r"^qué ",
            r"^que ",
            r"^cómo ",
            r"^como ",
            r"^cuál ",
            r"^cual ",
            r"^dónde ",
            r"^donde ",
            r"^cuándo ",
            r"^cuando ",
            r"^por qué ",
            r"^por que ",
            r"^what ",
            r"^how ",
            r"^where ",
            r"^when ",
            r"^why ",
            r"^which ",
            r"^can i ",
            r"^could you ",
            r"^puedo ",
            r"^podrías ",
            r"^podrias ",
        ],
        InputType.CORRECTION: [
            r"corrijo",
            r"corrección",
            r"correccion",
            r"me equivoqué",
            r"me equivoque",
            r"quise decir",
            r"en realidad",
            r"no es",
            r"correction",
            r"i meant",
            r"actually",
            r"sorry.*wrong",
            r"perdón.*mal",
            r"perdon.*mal",
        ],
        InputType.CONCERN: [
            r"me preocupa",
            r"tengo miedo",
            r"me da miedo",
            r"no estoy seguro",
            r"no estoy segura",
            r"worried",
            r"scared",
            r"afraid",
            r"nervous",
            r"anxious",
            r"no sé si",
            r"no se si",
            r"duda",
            r"incertidumbre",
        ],
        InputType.CONFIRMATION: [
            r"^sí$",
            r"^si$",
            r"^yes$",
            r"^ok$",
            r"^okay$",
            r"^vale$",
            r"^claro$",
            r"^correcto$",
            r"^exacto$",
            r"^así es$",
            r"^eso es$",
            r"^de acuerdo$",
            r"^perfecto$",
            r"^bien$",
            r"^sure$",
            r"^right$",
            r"^that's right$",
            r"^exactly$",
        ],
        InputType.REJECTION: [
            r"^no$",
            r"^nope$",
            r"^nah$",
            r"^después$",
            r"^despues$",
            r"^luego$",
            r"^ahora no$",
            r"^not now$",
            r"^later$",
            r"^maybe later$",
            r"^no gracias$",
            r"^no thanks$",
        ],
        InputType.GREETING: [
            r"^hola",
            r"^hello",
            r"^hi$",
            r"^hey",
            r"^buenos días",
            r"^buenas tardes",
            r"^buenas noches",
            r"^good morning",
            r"^good afternoon",
            r"^good evening",
        ],
        InputType.GRATITUDE: [r"gracias", r"thank", r"thanks", r"te agradezco", r"muy amable", r"appreciate"],
        InputType.FRUSTRATION: [
            r"no entiendo",
            r"no comprendo",
            r"estoy confundido",
            r"confusa",
            r"ya te dije",
            r"otra vez",
            r"de nuevo",
            r"don't understand",
            r"confused",
            r"already told you",
            r"again",
        ],
        InputType.PERSONAL_INFO: [
            r"me llamo",
            r"mi nombre es",
            r"soy de",
            r"tengo \d+ años",
            r"trabajo como",
            r"trabajo en",
            r"mi profesión",
            r"mi profesion",
            r"my name is",
            r"i'm from",
            r"i am from",
            r"i'm \d+ years",
            r"i work as",
            r"i work at",
        ],
    }

    # Patrones para extraer datos
    DATA_EXTRACTORS = {
        "name": [
            r"me llamo (\w+)",
            r"mi nombre es (\w+)",
            r"soy (\w+)",
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"i am (\w+)",
        ],
        "age": [r"tengo (\d+) años", r"(\d+) años", r"i'm (\d+)", r"i am (\d+)", r"(\d+) years old"],
        "profession": [
            r"trabajo como (\w+)",
            r"soy (\w+) de profesión",
            r"mi profesión es (\w+)",
            r"i work as (?:a |an )?(\w+)",
            r"i'm (?:a |an )?(\w+)",
        ],
        "country": [
            r"soy de (\w+)",
            r"vengo de (\w+)",
            r"i'm from (\w+)",
            r"i am from (\w+)",
            r"i come from (\w+)",
        ],
        "family_count": [
            r"(\d+) hijos",
            r"(\d+) niños",
            r"familia de (\d+)",
            r"(\d+) children",
            r"(\d+) kids",
            r"family of (\d+)",
        ],
    }

    @staticmethod
    def interpret(text: str, current_state: str = "", expected_type: str = "") -> InterpretedInput:
        """
        Interpreta el input del usuario.
        NUNCA ignora - siempre encuentra significado.
        """
        text_lower = text.lower().strip()
        result = InterpretedInput(input_type=InputType.UNKNOWN, confidence=0.0, original_text=text)

        # Detectar tipo de input
        for input_type, patterns in InputInterpreter.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    result.input_type = input_type
                    result.confidence = 0.8
                    break
            if result.confidence > 0:
                break

        # Extraer datos si es información personal
        for data_type, patterns in InputInterpreter.DATA_EXTRACTORS.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    result.extracted_data[data_type] = match.group(1)
                    if result.input_type == InputType.UNKNOWN:
                        result.input_type = InputType.PERSONAL_INFO
                        result.confidence = 0.7

        # Si no se detectó tipo pero hay texto, es respuesta directa
        if result.input_type == InputType.UNKNOWN and len(text_lower) > 2:
            result.input_type = InputType.DIRECT_ANSWER
            result.confidence = 0.5

        # Determinar si debe avanzar
        result.should_advance = result.input_type in [
            InputType.DIRECT_ANSWER,
            InputType.CONFIRMATION,
            InputType.PERSONAL_INFO,
        ]

        # Determinar si requiere clarificación
        result.requires_clarification = result.input_type in [
            InputType.QUESTION,
            InputType.CONCERN,
            InputType.FRUSTRATION,
        ]

        return result

    @staticmethod
    def get_contextual_response(interpreted: InterpretedInput, lang: str = "es") -> str:
        """
        Genera respuesta contextual basada en la interpretación.
        """
        responses = {
            "es": {
                InputType.QUESTION: "Buena pregunta. Déjame responderte...",
                InputType.CORRECTION: "Entendido, actualizo esa información. ✏️",
                InputType.CONCERN: "Entiendo tu preocupación. Vamos paso a paso. 🤝",
                InputType.CONFIRMATION: "¡Perfecto! Continuemos. ✅",
                InputType.REJECTION: "Sin problema, lo dejamos para después. 👍",
                InputType.GREETING: "¡Hola! ¿En qué te puedo ayudar hoy? 😊",
                InputType.GRATITUDE: "¡De nada! Estoy aquí para ayudarte. 🌟",
                InputType.FRUSTRATION: "Perdona si no fui claro. Déjame explicarte mejor. 🙏",
                InputType.PERSONAL_INFO: "Gracias por compartir eso. 📝",
                InputType.DIRECT_ANSWER: "Entendido. ✅",
                InputType.UNKNOWN: "Cuéntame más sobre eso. 🤔",
            },
            "en": {
                InputType.QUESTION: "Good question. Let me answer that...",
                InputType.CORRECTION: "Got it, I'll update that information. ✏️",
                InputType.CONCERN: "I understand your concern. Let's take it step by step. 🤝",
                InputType.CONFIRMATION: "Perfect! Let's continue. ✅",
                InputType.REJECTION: "No problem, we can do that later. 👍",
                InputType.GREETING: "Hello! How can I help you today? 😊",
                InputType.GRATITUDE: "You're welcome! I'm here to help. 🌟",
                InputType.FRUSTRATION: "Sorry if I wasn't clear. Let me explain better. 🙏",
                InputType.PERSONAL_INFO: "Thanks for sharing that. 📝",
                InputType.DIRECT_ANSWER: "Got it. ✅",
                InputType.UNKNOWN: "Tell me more about that. 🤔",
            },
        }

        lang_responses = responses.get(lang, responses["es"])
        return lang_responses.get(interpreted.input_type, lang_responses[InputType.UNKNOWN])


# ============== UNDERSTANDING GATEKEEPER ==============


class UnderstandingLevel(Enum):
    """Niveles de comprensión del usuario"""

    NOT_CONFIRMED = "not_confirmed"
    PARTIALLY_CONFIRMED = "partially_confirmed"
    FULLY_CONFIRMED = "fully_confirmed"


@dataclass
class UnderstandingStatus:
    """Estado de comprensión del usuario"""

    level: UnderstandingLevel
    confirmed_topics: list[str] = field(default_factory=list)
    pending_topics: list[str] = field(default_factory=list)
    last_confirmation: datetime | None = None


class UnderstandingGatekeeper:
    """
    Valida que el usuario entiende antes de avanzar.
    Regla: Sin confirmación de comprensión, no se avanza a decisiones importantes.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._user_understanding = {}
        return cls._instance

    # Temas que requieren confirmación antes de avanzar
    CRITICAL_TOPICS = {
        "visa_recommendation": ["visa_types", "requirements", "costs", "timeline"],
        "city_selection": ["cost_of_living", "job_market", "safety"],
        "payment": ["price", "what_includes", "refund_policy"],
    }

    def get_status(self, user_id: int) -> UnderstandingStatus:
        """Obtiene el estado de comprensión del usuario"""
        if user_id not in self._user_understanding:
            self._user_understanding[user_id] = UnderstandingStatus(level=UnderstandingLevel.NOT_CONFIRMED)
        return self._user_understanding[user_id]

    def confirm_topic(self, user_id: int, topic: str):
        """Marca un tema como confirmado/entendido"""
        status = self.get_status(user_id)
        if topic not in status.confirmed_topics:
            status.confirmed_topics.append(topic)
        if topic in status.pending_topics:
            status.pending_topics.remove(topic)
        status.last_confirmation = datetime.now()

        # Actualizar nivel
        if len(status.confirmed_topics) >= 3:
            status.level = UnderstandingLevel.FULLY_CONFIRMED
        elif len(status.confirmed_topics) >= 1:
            status.level = UnderstandingLevel.PARTIALLY_CONFIRMED

    def can_advance_to(self, user_id: int, target_action: str) -> tuple[bool, str, list[str]]:
        """
        Verifica si el usuario puede avanzar a una acción.
        Returns: (can_advance, reason, missing_confirmations)
        """
        status = self.get_status(user_id)

        if target_action not in self.CRITICAL_TOPICS:
            return True, "no_confirmation_needed", []

        required_topics = self.CRITICAL_TOPICS[target_action]
        missing = [t for t in required_topics if t not in status.confirmed_topics]

        if not missing:
            return True, "all_confirmed", []

        return False, "missing_confirmations", missing

    def get_confirmation_prompt(self, topic: str, lang: str = "es") -> str:
        """Genera prompt para confirmar comprensión de un tema"""
        prompts = {
            "es": {
                "visa_types": "¿Entiendes las diferencias entre los tipos de visa que mencioné?",
                "requirements": "¿Te quedaron claros los requisitos?",
                "costs": "¿Entiendes los costos involucrados?",
                "timeline": "¿Te queda claro el tiempo que toma el proceso?",
                "cost_of_living": "¿Entiendes el costo de vida en esta ciudad?",
                "job_market": "¿Te queda claro el mercado laboral?",
                "safety": "¿Entiendes los niveles de seguridad?",
                "price": "¿Entiendes el precio del servicio?",
                "what_includes": "¿Te queda claro qué incluye?",
                "refund_policy": "¿Entiendes la política de devolución?",
                "default": "¿Todo claro hasta aquí?",
            },
            "en": {
                "visa_types": "Do you understand the differences between the visa types I mentioned?",
                "requirements": "Are the requirements clear?",
                "costs": "Do you understand the costs involved?",
                "timeline": "Is the timeline clear?",
                "cost_of_living": "Do you understand the cost of living in this city?",
                "job_market": "Is the job market clear?",
                "safety": "Do you understand the safety levels?",
                "price": "Do you understand the service price?",
                "what_includes": "Is it clear what's included?",
                "refund_policy": "Do you understand the refund policy?",
                "default": "Is everything clear so far?",
            },
        }

        lang_prompts = prompts.get(lang, prompts["es"])
        return lang_prompts.get(topic, lang_prompts["default"])


# ============== VISA RECOMMENDATION GUARD ==============


class VisaRecommendationGuard:
    """
    Bloquea recomendaciones de visa sin datos mínimos.
    Regla: Prohibido recomendar visas sin: quién migra + edades + familia + motivo + restricciones.
    """

    @staticmethod
    def check_can_recommend(user_data: dict[str, Any]) -> tuple[bool, list[str], str]:
        """
        Verifica si hay datos suficientes para recomendar visa.
        Returns: (can_recommend, missing_data, message)
        """
        missing = []
        profile = user_data.get("profile", {})
        personal = profile.get("personal", {})
        history = profile.get("history", {})

        # Verificar quién migra
        if not personal.get("name"):
            missing.append("name")
        if not personal.get("birth_date") and not personal.get("age"):
            missing.append("age")
        if not personal.get("nationality"):
            missing.append("nationality")

        # Verificar familia
        family_status = user_data.get("family_status")
        if family_status is None:
            missing.append("family_status")
        elif family_status not in ["single", "alone", "solo"] and not user_data.get("family_members"):
            # Solo pedir detalles de familia si NO viaja solo
            missing.append("family_details")

        # Verificar motivo
        preferences = user_data.get("preferences", {})
        if not preferences.get("migration_reason"):
            missing.append("migration_reason")

        # Verificar restricciones
        if history.get("has_visas") is None:
            missing.append("visa_history")
        if history.get("criminal_record") is None:
            missing.append("criminal_record")

        if missing:
            return False, missing, VisaRecommendationGuard._get_missing_message(missing, "es")

        return True, [], ""

    @staticmethod
    def _get_missing_message(missing: list[str], lang: str) -> str:
        """Genera mensaje sobre datos faltantes"""
        labels = {
            "es": {
                "name": "tu nombre",
                "age": "tu edad",
                "nationality": "tu nacionalidad",
                "family_status": "si viajas con familia",
                "family_details": "información de tu familia",
                "migration_reason": "por qué quieres migrar",
                "visa_history": "tu historial de visas",
                "criminal_record": "si tienes antecedentes",
            },
            "en": {
                "name": "your name",
                "age": "your age",
                "nationality": "your nationality",
                "family_status": "if you're traveling with family",
                "family_details": "your family information",
                "migration_reason": "why you want to migrate",
                "visa_history": "your visa history",
                "criminal_record": "if you have a criminal record",
            },
        }

        lang_labels = labels.get(lang, labels["es"])
        missing_labels = [lang_labels.get(m, m) for m in missing[:3]]

        if lang == "es":
            return f"Antes de recomendarte una visa, necesito saber: {', '.join(missing_labels)}."
        else:
            return f"Before recommending a visa, I need to know: {', '.join(missing_labels)}."

    @staticmethod
    def get_next_required_question(user_data: dict[str, Any], lang: str = "es") -> tuple[str, str]:
        """
        Obtiene la siguiente pregunta requerida para poder recomendar visa.
        Returns: (question, field_name)
        """
        can_recommend, missing, _ = VisaRecommendationGuard.check_can_recommend(user_data)

        if can_recommend:
            return "", ""

        questions = {
            "es": {
                "name": ("¿Cómo te llamas?", "name"),
                "age": ("¿Cuántos años tienes?", "age"),
                "nationality": ("¿De qué país eres?", "nationality"),
                "family_status": ("¿Viajas solo o con familia?", "family_status"),
                "family_details": ("Cuéntame sobre tu familia. ¿Quiénes viajan contigo?", "family_details"),
                "migration_reason": ("¿Por qué quieres migrar?", "migration_reason"),
                "visa_history": ("¿Has tenido visas de otros países antes?", "visa_history"),
                "criminal_record": ("¿Tienes algún antecedente legal que deba saber?", "criminal_record"),
            },
            "en": {
                "name": ("What's your name?", "name"),
                "age": ("How old are you?", "age"),
                "nationality": ("What country are you from?", "nationality"),
                "family_status": ("Are you traveling alone or with family?", "family_status"),
                "family_details": ("Tell me about your family. Who's traveling with you?", "family_details"),
                "migration_reason": ("Why do you want to migrate?", "migration_reason"),
                "visa_history": ("Have you had visas from other countries before?", "visa_history"),
                "criminal_record": (
                    "Do you have any legal background I should know about?",
                    "criminal_record",
                ),
            },
        }

        lang_questions = questions.get(lang, questions["es"])

        # Priorizar preguntas en orden lógico
        priority_order = [
            "name",
            "age",
            "nationality",
            "family_status",
            "family_details",
            "migration_reason",
            "visa_history",
            "criminal_record",
        ]

        for field in priority_order:
            if field in missing:
                return lang_questions.get(field, ("", ""))

        return lang_questions.get(missing[0], ("", ""))


# ============== CONVERSATION DIRECTOR ==============


class ConversationDirector:
    """
    El modelo decide qué preguntar, el sistema solo valida.
    Regla: States sirven al diálogo, no lo controlan.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._conversation_history = {}
        return cls._instance

    def record_exchange(
        self, user_id: int, user_input: str, bot_response: str, was_form: bool = False, state: str = ""
    ):
        """Registra un intercambio conversacional"""
        if user_id not in self._conversation_history:
            self._conversation_history[user_id] = []

        self._conversation_history[user_id].append(
            {
                "timestamp": datetime.now().isoformat(),
                "user_input": user_input[:200],
                "bot_response": bot_response[:200],
                "was_form": was_form,
                "state": state,
            }
        )

        # Mantener solo últimos 50 intercambios
        if len(self._conversation_history[user_id]) > 50:
            self._conversation_history[user_id] = self._conversation_history[user_id][-50:]

    def get_conversation_context(self, user_id: int, last_n: int = 5) -> list[dict]:
        """Obtiene contexto de conversación reciente"""
        if user_id not in self._conversation_history:
            return []
        return self._conversation_history[user_id][-last_n:]

    def should_use_form(self, user_id: int, form_type: str) -> tuple[bool, str]:
        """
        Decide si usar formulario o enfoque conversacional.
        El modelo prefiere conversación, formularios son último recurso.
        """
        throttler = FormThrottler()
        can_show, reason = throttler.can_show_form(user_id)

        if not can_show:
            return False, f"throttled: {reason}"

        # Verificar historial - si usuario ha mostrado frustración, evitar formularios
        history = self.get_conversation_context(user_id, 3)
        for exchange in history:
            interpreted = InputInterpreter.interpret(exchange.get("user_input", ""))
            if interpreted.input_type == InputType.FRUSTRATION:
                return False, "user_frustrated"

        return True, "allowed"

    def get_next_action(
        self, user_id: int, user_data: dict[str, Any], current_state: str, user_input: str
    ) -> dict[str, Any]:
        """
        Determina la siguiente acción basada en el contexto completo.
        El modelo decide, el sistema solo valida errores graves.
        """
        # Interpretar input
        interpreted = InputInterpreter.interpret(user_input, current_state)

        # Verificar si puede recomendar visa (si es relevante)
        if "visa" in current_state.lower() or "recommendation" in current_state.lower():
            can_recommend, missing, message = VisaRecommendationGuard.check_can_recommend(user_data)
            if not can_recommend:
                question, field = VisaRecommendationGuard.get_next_required_question(user_data)
                return {
                    "action": "ask_required_data",
                    "message": message,
                    "question": question,
                    "field": field,
                    "block_visa_recommendation": True,
                }

        # Verificar comprensión para acciones críticas
        gatekeeper = UnderstandingGatekeeper()
        if current_state in ["visa_recommendation", "city_selection", "payment"]:
            can_advance, reason, missing = gatekeeper.can_advance_to(user_id, current_state)
            if not can_advance:
                return {
                    "action": "confirm_understanding",
                    "missing_topics": missing,
                    "prompt": gatekeeper.get_confirmation_prompt(missing[0] if missing else "default"),
                }

        # Acción por defecto: continuar conversación
        return {
            "action": "continue_conversation",
            "interpreted_input": interpreted,
            "suggested_response": InputInterpreter.get_contextual_response(interpreted),
            "should_advance": interpreted.should_advance,
            "extracted_data": interpreted.extracted_data,
        }


# ============== SINGLETON GETTERS ==============


def get_form_throttler() -> FormThrottler:
    return FormThrottler()


def get_input_interpreter() -> InputInterpreter:
    return InputInterpreter()


def get_understanding_gatekeeper() -> UnderstandingGatekeeper:
    return UnderstandingGatekeeper()


def get_visa_guard() -> VisaRecommendationGuard:
    return VisaRecommendationGuard()


def get_conversation_director() -> ConversationDirector:
    return ConversationDirector()


# ============== INTEGRATION HELPERS ==============


def should_show_form(user_id: int, form_type: str) -> tuple[bool, str]:
    """Helper para verificar si mostrar formulario"""
    director = get_conversation_director()
    return director.should_use_form(user_id, form_type)


def interpret_user_input(text: str, state: str = "") -> InterpretedInput:
    """Helper para interpretar input del usuario"""
    return InputInterpreter.interpret(text, state)


def can_recommend_visa(user_data: dict[str, Any]) -> tuple[bool, str]:
    """Helper para verificar si se puede recomendar visa"""
    can, missing, message = VisaRecommendationGuard.check_can_recommend(user_data)
    return can, message


def get_next_visa_question(user_data: dict[str, Any], lang: str = "es") -> str:
    """Helper para obtener siguiente pregunta requerida para visa"""
    question, _ = VisaRecommendationGuard.get_next_required_question(user_data, lang)
    return question
