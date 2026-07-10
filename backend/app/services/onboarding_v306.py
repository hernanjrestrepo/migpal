#!/usr/bin/env python3
"""
MigPAL Onboarding Conversacional v3.0.6
=======================================
El comando /start NO puede iniciar formularios.
Bloque obligatorio de 3-4 mensajes antes de pedir nombre.

Flujo:
1. Presentación empática (quién soy, para qué estoy, tono humano)
2. Pregunta abierta de vínculo ("¿Qué te trajo hoy aquí?")
3. Escucha libre + respuesta empática breve
4. Explicación corta del proceso
5. SOLO después pedir nombre (con consentimiento explícito)

Prohibido mostrar "FASE 1" hasta consentimiento explícito.
"""

import logging
import random
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OnboardingState(Enum):
    """Estados del onboarding conversacional"""

    WELCOME = "onboarding_welcome"  # Presentación empática
    OPEN_QUESTION = "onboarding_question"  # Pregunta abierta
    LISTENING = "onboarding_listening"  # Escuchando respuesta libre
    PROCESS_EXPLAIN = "onboarding_explain"  # Explicación del proceso
    CONSENT = "onboarding_consent"  # Pedir consentimiento
    NAME_REQUEST = "onboarding_name"  # Ahora sí pedir nombre
    COMPLETED = "onboarding_completed"  # Onboarding terminado


# Estados que son parte del onboarding (NO son formularios)
ONBOARDING_STATES = [
    OnboardingState.WELCOME.value,
    OnboardingState.OPEN_QUESTION.value,
    OnboardingState.LISTENING.value,
    OnboardingState.PROCESS_EXPLAIN.value,
    OnboardingState.CONSENT.value,
    OnboardingState.NAME_REQUEST.value,
]


@dataclass
class OnboardingMessages:
    """Mensajes del onboarding por idioma"""

    # === PASO 1: PRESENTACIÓN EMPÁTICA ===
    WELCOME = {
        "es": (
            "¡Hola! 👋\n\n"
            "Soy MigPAL, pero más que un asistente, me gusta pensar que soy "
            "tu amigo en este viaje de migración.\n\n"
            "Sé que dar este paso puede sentirse abrumador. Hay tantas preguntas, "
            "tantas dudas, tanta información... Y a veces parece que nadie entiende "
            "realmente por lo que estás pasando.\n\n"
            "Estoy aquí para eso. Para escucharte, para aclarar tus dudas, "
            "y para ayudarte a ver el camino con más claridad. 🌟\n\n"
            "Sin presiones, sin prisas. A tu ritmo."
        ),
        "en": (
            "Hi! 👋\n\n"
            "I'm MigPAL, but more than an assistant, I like to think of myself as "
            "your friend on this migration journey.\n\n"
            "I know taking this step can feel overwhelming. So many questions, "
            "so many doubts, so much information... And sometimes it feels like "
            "nobody really understands what you're going through.\n\n"
            "That's why I'm here. To listen to you, to answer your questions, "
            "and to help you see the path more clearly. 🌟\n\n"
            "No pressure, no rush. At your own pace."
        ),
    }

    # === PASO 2: PREGUNTA ABIERTA DE VÍNCULO ===
    OPEN_QUESTIONS = {
        "es": [
            "Cuéntame... ¿qué te trajo hoy aquí? 💭",
            "Me encantaría saber... ¿cómo te sientes con tu idea de migrar? 💭",
            "¿Qué es lo que más te emociona o preocupa de este proceso? 💭",
        ],
        "en": [
            "Tell me... what brought you here today? 💭",
            "I'd love to know... how do you feel about your idea of migrating? 💭",
            "What excites or worries you most about this process? 💭",
        ],
    }

    # === PASO 3: RESPUESTAS EMPÁTICAS (según lo que digan) ===
    EMPATHIC_RESPONSES = {
        "es": {
            "work": (
                "Entiendo perfectamente. Buscar mejores oportunidades laborales es una de las "
                "razones más comunes y válidas para migrar. Querer crecer profesionalmente "
                "y darle un mejor futuro a tu familia es algo muy valiente. 💪"
            ),
            "family": (
                "Reunirse con la familia es algo muy especial. Esa conexión es invaluable, "
                "y entiendo lo difícil que puede ser estar lejos de quienes amas. "
                "Vamos a trabajar juntos para acercarte a ellos. ❤️"
            ),
            "quality": (
                "Buscar una mejor calidad de vida es completamente válido. Todos merecemos "
                "vivir en un lugar donde podamos sentirnos seguros, tranquilos y con "
                "oportunidades de crecer. 🌱"
            ),
            "education": (
                "¡La educación es una inversión increíble! Estudiar en otro país abre "
                "puertas que ni te imaginas. Es una decisión muy inteligente. 📚"
            ),
            "safety": (
                "Entiendo. La seguridad es fundamental. Nadie debería vivir con miedo, "
                "y buscar un lugar más seguro para ti y tu familia es lo más natural "
                "del mundo. Estoy aquí para ayudarte. 🛡️"
            ),
            "default": (
                "Gracias por compartir eso conmigo. Cada historia es única, y la tuya "
                "es importante. Sea cual sea tu razón, estoy aquí para ayudarte a "
                "encontrar el mejor camino. 🌟"
            ),
            "uncertain": (
                "Es completamente normal sentirse así. Migrar es una decisión grande "
                "y es natural tener dudas. No tienes que tener todo claro ahora. "
                "Vamos paso a paso, juntos. 🤝"
            ),
            "excited": (
                "¡Me encanta tu entusiasmo! Esa energía positiva es muy importante "
                "en este proceso. Vamos a canalizar esa emoción en un plan concreto. 🚀"
            ),
            "scared": (
                "Es normal sentir miedo. Dar un paso tan grande siempre da un poco de "
                "vértigo. Pero ¿sabes qué? El miedo y la emoción a veces se sienten igual. "
                "Estás siendo muy valiente. 💪"
            ),
        },
        "en": {
            "work": (
                "I completely understand. Looking for better job opportunities is one of the "
                "most common and valid reasons to migrate. Wanting to grow professionally "
                "and give your family a better future is very brave. 💪"
            ),
            "family": (
                "Reuniting with family is something very special. That connection is priceless, "
                "and I understand how hard it can be to be away from those you love. "
                "Let's work together to bring you closer to them. ❤️"
            ),
            "quality": (
                "Seeking a better quality of life is completely valid. We all deserve "
                "to live in a place where we can feel safe, peaceful and with "
                "opportunities to grow. 🌱"
            ),
            "education": (
                "Education is an incredible investment! Studying in another country opens "
                "doors you can't even imagine. It's a very smart decision. 📚"
            ),
            "safety": (
                "I understand. Safety is fundamental. Nobody should live in fear, "
                "and looking for a safer place for you and your family is the most natural "
                "thing in the world. I'm here to help you. 🛡️"
            ),
            "default": (
                "Thank you for sharing that with me. Every story is unique, and yours "
                "is important. Whatever your reason, I'm here to help you "
                "find the best path. 🌟"
            ),
            "uncertain": (
                "It's completely normal to feel that way. Migrating is a big decision "
                "and it's natural to have doubts. You don't have to have everything figured out now. "
                "Let's go step by step, together. 🤝"
            ),
            "excited": (
                "I love your enthusiasm! That positive energy is very important "
                "in this process. Let's channel that excitement into a concrete plan. 🚀"
            ),
            "scared": (
                "It's normal to feel scared. Taking such a big step always gives you "
                "some vertigo. But you know what? Fear and excitement sometimes feel the same. "
                "You're being very brave. 💪"
            ),
        },
    }

    # === PASO 4: EXPLICACIÓN DEL PROCESO ===
    PROCESS_EXPLANATION = {
        "es": (
            "Así es como vamos a trabajar juntos:\n\n"
            "🗣️ *Primero conversamos* - Quiero conocerte, entender tu situación, "
            "tus sueños y tus preocupaciones.\n\n"
            "📋 *Luego ordenamos la info* - Una vez que te conozca mejor, "
            "te haré algunas preguntas específicas para armar tu perfil.\n\n"
            "🗺️ *Creamos tu plan* - Con toda esa información, diseñamos juntos "
            "un plan de migración personalizado.\n\n"
            '💡 *Mi filosofía:* "La visa es el VEHÍCULO, no el DESTINO". '
            "Primero definimos qué vida quieres vivir, luego encontramos cómo llegar.\n\n"
            "¿Suena bien?"
        ),
        "en": (
            "This is how we'll work together:\n\n"
            "🗣️ *First we talk* - I want to get to know you, understand your situation, "
            "your dreams and your concerns.\n\n"
            "📋 *Then we organize the info* - Once I know you better, "
            "I'll ask you some specific questions to build your profile.\n\n"
            "🗺️ *We create your plan* - With all that information, we design together "
            "a personalized migration plan.\n\n"
            '💡 *My philosophy:* "The visa is the VEHICLE, not the DESTINATION". '
            "First we define what life you want to live, then we find how to get there.\n\n"
            "Sound good?"
        ),
    }

    # === PASO 5: PEDIR CONSENTIMIENTO ===
    CONSENT_REQUEST = {"es": "¿Te parece si empezamos? 🚀", "en": "Shall we get started? 🚀"}

    CONSENT_BUTTONS = {
        "es": [
            ("✅ ¡Sí, empecemos!", "onboarding_yes"),
            ("🤔 Tengo más preguntas", "onboarding_questions"),
            ("⏰ Mejor después", "onboarding_later"),
        ],
        "en": [
            ("✅ Yes, let's start!", "onboarding_yes"),
            ("🤔 I have more questions", "onboarding_questions"),
            ("⏰ Maybe later", "onboarding_later"),
        ],
    }

    # === PASO 6: PEDIR NOMBRE (después del consentimiento) ===
    NAME_REQUEST = {
        "es": (
            "¡Perfecto! 🎉\n\n"
            "Antes de continuar, me encantaría saber cómo te llamas.\n\n"
            "¿Cuál es tu nombre?"
        ),
        "en": ("Perfect! 🎉\n\n" "Before we continue, I'd love to know your name.\n\n" "What's your name?"),
    }

    # === RESPUESTAS A "TENGO MÁS PREGUNTAS" ===
    MORE_QUESTIONS_RESPONSE = {
        "es": (
            "¡Claro! Pregunta lo que quieras. 😊\n\n"
            "Puedes preguntarme sobre:\n"
            "• El proceso de migración en general\n"
            "• Tipos de visas\n"
            "• Costos aproximados\n"
            "• Tiempos del proceso\n"
            "• Cualquier duda que tengas\n\n"
            "Escríbeme tu pregunta y te respondo."
        ),
        "en": (
            "Of course! Ask me anything. 😊\n\n"
            "You can ask me about:\n"
            "• The migration process in general\n"
            "• Types of visas\n"
            "• Approximate costs\n"
            "• Process timelines\n"
            "• Any questions you have\n\n"
            "Write your question and I'll answer."
        ),
    }

    # === RESPUESTA A "MEJOR DESPUÉS" ===
    LATER_RESPONSE = {
        "es": (
            "¡Sin problema! 👋\n\n"
            "Estaré aquí cuando estés listo/a. Solo escríbeme /start "
            "cuando quieras retomar la conversación.\n\n"
            "¡Mucho éxito en todo!"
        ),
        "en": (
            "No problem! 👋\n\n"
            "I'll be here when you're ready. Just write /start "
            "when you want to continue the conversation.\n\n"
            "Best of luck with everything!"
        ),
    }


class OnboardingEngine:
    """Motor del onboarding conversacional"""

    def __init__(self):
        self.messages = OnboardingMessages()

    def get_welcome_message(self, lang: str = "es") -> str:
        """Obtener mensaje de bienvenida (Paso 1)"""
        return self.messages.WELCOME.get(lang, self.messages.WELCOME["es"])

    def get_open_question(self, lang: str = "es") -> str:
        """Obtener pregunta abierta (Paso 2)"""
        questions = self.messages.OPEN_QUESTIONS.get(lang, self.messages.OPEN_QUESTIONS["es"])
        return random.choice(questions)

    def get_empathic_response(self, user_text: str, lang: str = "es") -> str:
        """Obtener respuesta empática basada en lo que dijo el usuario (Paso 3)"""
        responses = self.messages.EMPATHIC_RESPONSES.get(lang, self.messages.EMPATHIC_RESPONSES["es"])

        # Detectar tema principal
        text_lower = user_text.lower()

        # Palabras clave por tema
        keywords = {
            "work": [
                "trabajo",
                "empleo",
                "profesional",
                "carrera",
                "salario",
                "job",
                "work",
                "career",
                "salary",
                "professional",
            ],
            "family": [
                "familia",
                "hijos",
                "esposo",
                "esposa",
                "padres",
                "reunir",
                "family",
                "children",
                "husband",
                "wife",
                "parents",
                "reunite",
            ],
            "quality": [
                "calidad",
                "vida",
                "mejor",
                "oportunidad",
                "futuro",
                "quality",
                "life",
                "better",
                "opportunity",
                "future",
            ],
            "education": [
                "estudiar",
                "universidad",
                "educación",
                "carrera",
                "study",
                "university",
                "education",
                "degree",
            ],
            "safety": ["seguridad", "violencia", "miedo", "peligro", "safety", "violence", "fear", "danger"],
            "uncertain": [
                "no sé",
                "duda",
                "confundido",
                "no estoy seguro",
                "don't know",
                "doubt",
                "confused",
                "not sure",
            ],
            "excited": ["emocionado", "feliz", "ilusionado", "excited", "happy", "thrilled"],
            "scared": ["miedo", "nervioso", "asustado", "scared", "nervous", "afraid"],
        }

        # Buscar coincidencias
        for theme, words in keywords.items():
            if any(word in text_lower for word in words):
                return responses.get(theme, responses["default"])

        return responses["default"]

    def get_process_explanation(self, lang: str = "es") -> str:
        """Obtener explicación del proceso (Paso 4)"""
        return self.messages.PROCESS_EXPLANATION.get(lang, self.messages.PROCESS_EXPLANATION["es"])

    def get_consent_request(self, lang: str = "es") -> tuple[str, list[tuple[str, str]]]:
        """Obtener solicitud de consentimiento (Paso 5)"""
        text = self.messages.CONSENT_REQUEST.get(lang, self.messages.CONSENT_REQUEST["es"])
        buttons = self.messages.CONSENT_BUTTONS.get(lang, self.messages.CONSENT_BUTTONS["es"])
        return text, buttons

    def get_name_request(self, lang: str = "es") -> str:
        """Obtener solicitud de nombre (Paso 6 - después del consentimiento)"""
        return self.messages.NAME_REQUEST.get(lang, self.messages.NAME_REQUEST["es"])

    def get_more_questions_response(self, lang: str = "es") -> str:
        """Respuesta cuando el usuario tiene más preguntas"""
        return self.messages.MORE_QUESTIONS_RESPONSE.get(lang, self.messages.MORE_QUESTIONS_RESPONSE["es"])

    def get_later_response(self, lang: str = "es") -> str:
        """Respuesta cuando el usuario quiere continuar después"""
        return self.messages.LATER_RESPONSE.get(lang, self.messages.LATER_RESPONSE["es"])

    def is_onboarding_state(self, state: str) -> bool:
        """Verificar si el estado es parte del onboarding"""
        return state in ONBOARDING_STATES

    def get_next_state(self, current_state: str) -> str:
        """Obtener el siguiente estado del onboarding"""
        state_flow = {
            OnboardingState.WELCOME.value: OnboardingState.OPEN_QUESTION.value,
            OnboardingState.OPEN_QUESTION.value: OnboardingState.LISTENING.value,
            OnboardingState.LISTENING.value: OnboardingState.PROCESS_EXPLAIN.value,
            OnboardingState.PROCESS_EXPLAIN.value: OnboardingState.CONSENT.value,
            OnboardingState.CONSENT.value: OnboardingState.NAME_REQUEST.value,
            OnboardingState.NAME_REQUEST.value: OnboardingState.COMPLETED.value,
        }
        return state_flow.get(current_state, OnboardingState.COMPLETED.value)


# Singleton
_onboarding_engine = None


def get_onboarding_engine() -> OnboardingEngine:
    """Obtener instancia del motor de onboarding"""
    global _onboarding_engine
    if _onboarding_engine is None:
        _onboarding_engine = OnboardingEngine()
    return _onboarding_engine


def is_form_state(state: str) -> bool:
    """
    Verificar si un estado es un formulario.
    Los estados de onboarding NO son formularios.
    """
    # Estados que son formularios (piden datos específicos)
    FORM_STATES = [
        "name",
        "birth_date",
        "nationality",
        "current_country",
        "current_city",
        "email",
        "phone",
        "education_level",
        "education_status",
        "education_field",
        "education_career",
        "work_status",
        "profession",
        "work_experience",
        "english_level",
        "budget",
        "timeline",
        "savings",
    ]

    # Los estados de onboarding NO son formularios
    if state in ONBOARDING_STATES:
        return False

    return state in FORM_STATES


def validate_onboarding_flow(first_message: str, first_state: str) -> tuple[bool, str]:
    """
    Validar que el onboarding no empiece con un formulario.

    Returns:
        Tuple[is_valid, error_message]
    """
    # El primer estado debe ser de onboarding
    if first_state not in ONBOARDING_STATES:
        return False, f"El primer estado '{first_state}' no es de onboarding"

    # El primer mensaje no debe pedir datos de formulario
    form_keywords = [
        "nombre completo",
        "full name",
        "fecha de nacimiento",
        "birth date",
        "correo electrónico",
        "email",
        "teléfono",
        "phone",
        "FASE 1",
        "PHASE 1",
        "nivel educativo",
        "education level",
    ]

    for keyword in form_keywords:
        if keyword.lower() in first_message.lower():
            return False, f"El primer mensaje contiene '{keyword}' que es de formulario"

    return True, ""
