#!/usr/bin/env python3
"""
MigPAL UX Improvements v3.0.5
=============================
- NLU de corrección: detectar cuando usuario quiere corregir un campo
- Onboarding conversacional: saludo empático + explicación breve
- Manejo seguro de Markdown
- Soporte para voice (transcripción)
- Multi-select en opciones

MigPAL es más que un consultor experto - es tu amigo y coach de migración.
Super empático, no promete nada, interpreta la información como es.
La personalidad se adapta a las necesidades del cliente.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ============== PERSONALIDAD DE MIGPAL ==============


class MigPALPersonality:
    """
    MigPAL es un consultor experto pero más allá de eso es un asesor y coach de migración.
    Es super empático pero no promete nada e interpreta la información como es.
    Su personalidad cambia de acuerdo a las necesidades del cliente.
    La idea es que el cliente se sienta cómodo y acompañado.
    """

    GREETINGS = {
        "es": [
            "¡Hola {name}! 👋 Soy MigPAL, tu amigo y guía en este viaje de migración.",
            "¡Bienvenido/a {name}! 🌟 Estoy aquí para acompañarte en cada paso.",
            "¡Qué gusto conocerte, {name}! 🤝 Juntos vamos a planificar tu nueva vida.",
        ],
        "en": [
            "Hi {name}! 👋 I'm MigPAL, your friend and guide on this migration journey.",
            "Welcome {name}! 🌟 I'm here to accompany you every step of the way.",
            "Nice to meet you, {name}! 🤝 Together we'll plan your new life.",
        ],
    }

    EMPATHY_PHRASES = {
        "es": {
            "understanding": "Entiendo perfectamente cómo te sientes. Migrar es una decisión grande y es normal tener muchas preguntas.",
            "support": "No estás solo/a en esto. Estoy aquí para aclarar todas tus dudas.",
            "encouragement": "Cada paso que das te acerca más a tu sueño. ¡Vamos juntos!",
            "validation": "Es completamente válido sentirse así. Muchos han pasado por lo mismo.",
            "reassurance": "No te preocupes, vamos paso a paso. No hay prisa.",
        },
        "en": {
            "understanding": "I completely understand how you feel. Migrating is a big decision and it's normal to have many questions.",
            "support": "You're not alone in this. I'm here to answer all your questions.",
            "encouragement": "Every step you take brings you closer to your dream. Let's go together!",
            "validation": "It's completely valid to feel that way. Many have gone through the same.",
            "reassurance": "Don't worry, let's go step by step. There's no rush.",
        },
    }

    EXPLANATIONS = {
        "es": {
            "process": (
                "Te voy a guiar paso a paso para crear tu plan de migración personalizado. "
                "Primero te conozco, luego definimos tu plan de vida, y finalmente encontramos "
                "la mejor ruta migratoria para ti. 🗺️"
            ),
            "philosophy": (
                "Mi filosofía es simple: 'La visa es el VEHÍCULO, no el DESTINO'. "
                "Primero definimos qué vida quieres vivir, luego encontramos cómo llegar. 💡"
            ),
            "honesty": (
                "Siempre te voy a dar información real y honesta. No prometo nada que no pueda cumplir. "
                "Mi trabajo es darte las herramientas para que tomes las mejores decisiones. 🎯"
            ),
        },
        "en": {
            "process": (
                "I'll guide you step by step to create your personalized migration plan. "
                "First I get to know you, then we define your life plan, and finally we find "
                "the best migration route for you. 🗺️"
            ),
            "philosophy": (
                "My philosophy is simple: 'The visa is the VEHICLE, not the DESTINATION'. "
                "First we define what life you want to live, then we find how to get there. 💡"
            ),
            "honesty": (
                "I'll always give you real and honest information. I don't promise anything I can't deliver. "
                "My job is to give you the tools to make the best decisions. 🎯"
            ),
        },
    }

    @classmethod
    def get_greeting(cls, name: str, lang: str = "es") -> str:
        """Obtener saludo personalizado"""
        import random

        greetings = cls.GREETINGS.get(lang, cls.GREETINGS["es"])
        return random.choice(greetings).format(name=name or "amigo/a")

    @classmethod
    def get_empathy(cls, context: str, lang: str = "es") -> str:
        """Obtener frase empática según contexto"""
        phrases = cls.EMPATHY_PHRASES.get(lang, cls.EMPATHY_PHRASES["es"])
        return phrases.get(context, phrases["support"])

    @classmethod
    def get_explanation(cls, topic: str, lang: str = "es") -> str:
        """Obtener explicación sobre un tema"""
        explanations = cls.EXPLANATIONS.get(lang, cls.EXPLANATIONS["es"])
        return explanations.get(topic, explanations["process"])


# ============== NLU DE CORRECCIÓN ==============


class CorrectionType(Enum):
    """Tipos de corrección que el usuario puede hacer"""

    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    DATE = "date"
    CITY = "city"
    COUNTRY = "country"
    OCCUPATION = "occupation"  # V4.2.1 FIX: Nuevo tipo para profesión
    NONE = "none"


@dataclass
class CorrectionIntent:
    """Intención de corrección detectada"""

    type: CorrectionType
    value: str
    confidence: float
    original_text: str


class CorrectionNLU:
    """
    NLU para detectar cuando el usuario quiere corregir un campo.
    Ejemplo: "mi correo correcto es hernan@gmail.com" mientras está en otro prompt.
    """

    # Patrones de corrección por tipo
    PATTERNS = {
        CorrectionType.EMAIL: [
            r"(?:mi\s+)?(?:correo|email|mail)\s+(?:correcto|real|es|:)\s*[:\s]*([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
            r"(?:corregir|cambiar|actualizar)\s+(?:mi\s+)?(?:correo|email)\s+(?:a|por|:)\s*([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
            r"(?:el\s+)?(?:correo|email)\s+(?:correcto|real)\s+es\s*:?\s*([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
            r"(?:perdón|perdon|disculpa),?\s+(?:mi\s+)?(?:correo|email)\s+es\s*:?\s*([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
        ],
        CorrectionType.PHONE: [
            r"(?:mi\s+)?(?:teléfono|telefono|celular|número|numero|tel)\s+(?:correcto|real|es|:)\s*[:\s]*(\+?[\d\s\-\(\)]{8,20})",
            r"(?:corregir|cambiar|actualizar)\s+(?:mi\s+)?(?:teléfono|telefono|celular)\s+(?:a|por|:)\s*(\+?[\d\s\-\(\)]{8,20})",
            r"(?:el\s+)?(?:teléfono|telefono|celular)\s+(?:correcto|real)\s+es\s*:?\s*(\+?[\d\s\-\(\)]{8,20})",
        ],
        CorrectionType.NAME: [
            r"(?:mi\s+)?nombre\s+(?:correcto|real|completo|es|:)\s*[:\s]*([A-Za-záéíóúñÁÉÍÓÚÑ\s]{2,50})",
            r"(?:corregir|cambiar)\s+(?:mi\s+)?nombre\s+(?:a|por|:)\s*([A-Za-záéíóúñÁÉÍÓÚÑ\s]{2,50})",
            # V4.2.1 FIX: "me llamo" solo para nombres propios, NO ocupaciones
            r"me\s+llamo\s+([A-Za-záéíóúñÁÉÍÓÚÑ\s]{2,50})",
        ],
        # V4.2.1 FIX: Nuevo tipo para ocupación/profesión
        CorrectionType.OCCUPATION: [
            r"(?:soy|trabajo\s+(?:como|de))\s+(ingenier[oa]|doctor[a]?|abogad[oa]|profesor[a]?|contador[a]?|enferm[oa]|programador[a]?|diseñador[a]?|arquitect[oa]|médic[oa]|psicólog[oa]|econom[oi]sta|administrador[a]?|gerente|director[a]?|analista|consultor[a]?|vendedor[a]?|chef|cocinero[a]?|electricista|mecánico[a]?|plomero[a]?|carpintero[a]?|maestro[a]?|periodista|escritor[a]?|músico[a]?|artista|fotógrafo[a]?|veterinario[a]?|farmacéutico[a]?|biólogo[a]?|químico[a]?|físico[a]?|matemático[a]?)(?:\s+de\s+\w+)?",
            r"(?:mi\s+)?(?:profesión|ocupación|trabajo)\s+(?:es|:)\s*(.+)",
            r"(?:trabajo|laburo)\s+(?:en|como)\s+(.+)",
        ],
        CorrectionType.DATE: [
            r"(?:mi\s+)?(?:fecha\s+de\s+)?(?:nacimiento|cumpleaños)\s+(?:es|:)\s*[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
            r"(?:nací|naci)\s+(?:el\s+)?(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})",
        ],
    }

    # Palabras clave que indican corrección
    CORRECTION_KEYWORDS = [
        "correcto",
        "corregir",
        "cambiar",
        "actualizar",
        "perdón",
        "perdon",
        "disculpa",
        "error",
        "equivoqué",
        "equivoque",
        "mal",
        "incorrecto",
        "correct",
        "change",
        "update",
        "sorry",
        "wrong",
        "mistake",
    ]

    @classmethod
    def detect_correction(cls, text: str) -> CorrectionIntent | None:
        """
        Detectar si el usuario quiere corregir un campo.

        Args:
            text: Texto del usuario

        Returns:
            CorrectionIntent si se detecta corrección, None si no
        """
        text_lower = text.lower().strip()

        # Verificar si hay palabras clave de corrección
        has_correction_keyword = any(kw in text_lower for kw in cls.CORRECTION_KEYWORDS)

        # Buscar patrones de corrección
        for correction_type, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    confidence = 0.9 if has_correction_keyword else 0.7

                    return CorrectionIntent(
                        type=correction_type, value=value, confidence=confidence, original_text=text
                    )

        # Si hay keyword de corrección pero no se detectó el tipo específico
        if has_correction_keyword:
            # Intentar detectar email suelto
            email_match = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text)
            if email_match:
                return CorrectionIntent(
                    type=CorrectionType.EMAIL, value=email_match.group(1), confidence=0.6, original_text=text
                )

            # Intentar detectar teléfono suelto
            phone_match = re.search(r"(\+?[\d\s\-\(\)]{10,20})", text)
            if phone_match:
                return CorrectionIntent(
                    type=CorrectionType.PHONE,
                    value=phone_match.group(1).strip(),
                    confidence=0.6,
                    original_text=text,
                )

        return None

    @classmethod
    def get_confirmation_message(cls, correction: CorrectionIntent, lang: str = "es") -> str:
        """Obtener mensaje de confirmación para la corrección"""
        messages = {
            "es": {
                CorrectionType.EMAIL: f"✅ Perfecto, actualicé tu correo a: {correction.value}",
                CorrectionType.PHONE: f"✅ Listo, tu teléfono ahora es: {correction.value}",
                CorrectionType.NAME: f"✅ Entendido, tu nombre es: {correction.value}",
                CorrectionType.DATE: f"✅ Actualicé tu fecha de nacimiento a: {correction.value}",
                CorrectionType.OCCUPATION: f"✅ Excelente, eres {correction.value}. ¿Cómo te llamas?",  # V4.2.1
            },
            "en": {
                CorrectionType.EMAIL: f"✅ Perfect, I updated your email to: {correction.value}",
                CorrectionType.PHONE: f"✅ Done, your phone is now: {correction.value}",
                CorrectionType.NAME: f"✅ Got it, your name is: {correction.value}",
                CorrectionType.DATE: f"✅ I updated your birth date to: {correction.value}",
                CorrectionType.OCCUPATION: f"✅ Great, you're a {correction.value}. What's your name?",  # V4.2.1
            },
        }

        lang_messages = messages.get(lang, messages["es"])
        return lang_messages.get(correction.type, "✅ Actualizado")


# ============== MANEJO SEGURO DE MARKDOWN ==============


class SafeMarkdown:
    """Utilidades para manejar Markdown de forma segura"""

    # Caracteres especiales de Markdown que necesitan escape
    SPECIAL_CHARS = ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]

    @classmethod
    def escape(cls, text: str) -> str:
        """Escapar caracteres especiales de Markdown"""
        if not text:
            return ""

        for char in cls.SPECIAL_CHARS:
            text = text.replace(char, f"\\{char}")

        return text

    @classmethod
    def safe_bold(cls, text: str) -> str:
        """Crear texto en negrita de forma segura"""
        escaped = cls.escape(text)
        return f"*{escaped}*"

    @classmethod
    def safe_italic(cls, text: str) -> str:
        """Crear texto en cursiva de forma segura"""
        escaped = cls.escape(text)
        return f"_{escaped}_"

    @classmethod
    def validate_markdown(cls, text: str) -> tuple[bool, str]:
        """
        Validar que el Markdown está bien formateado.

        Returns:
            Tuple[is_valid, cleaned_text]
        """
        # Contar asteriscos y guiones bajos
        asterisks = text.count("*")
        underscores = text.count("_")

        # Deben ser pares
        if asterisks % 2 != 0:
            # Intentar arreglar
            text = text.replace("*", "")

        if underscores % 2 != 0:
            text = text.replace("_", "")

        # Verificar que no hay entidades mal cerradas
        # Patrón: *texto* o _texto_

        # Si hay asteriscos o guiones bajos sueltos, limpiar
        cleaned = text

        # Verificar balance
        is_valid = (cleaned.count("*") % 2 == 0) and (cleaned.count("_") % 2 == 0)

        return is_valid, cleaned

    @classmethod
    def strip_markdown(cls, text: str) -> str:
        """Remover todo el Markdown del texto"""
        # Remover negrita
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        # Remover cursiva
        text = re.sub(r"_([^_]+)_", r"\1", text)
        # Remover código
        text = re.sub(r"`([^`]+)`", r"\1", text)

        return text


# ============== PREFERENCIAS DE REGIÓN ==============


class RegionPreferences:
    """Mapeo de preferencias a regiones recomendadas"""

    PREFERENCES = {
        "warm": {
            "regions": ["south", "west"],
            "states": ["Florida", "Texas", "Arizona", "California"],
            "description": {
                "es": "Para clima cálido, te recomiendo el Sur o el Oeste de Estados Unidos.",
                "en": "For warm weather, I recommend the South or West of the United States.",
            },
        },
        "cheap": {
            "regions": ["south", "midwest"],
            "states": ["Texas", "Florida", "Ohio", "Indiana", "Tennessee"],
            "description": {
                "es": "Para bajo costo de vida, el Sur y el Medio Oeste son excelentes opciones.",
                "en": "For low cost of living, the South and Midwest are excellent options.",
            },
        },
        "tech": {
            "regions": ["west", "northeast"],
            "states": ["California", "Washington", "Texas", "New York", "Massachusetts"],
            "description": {
                "es": "Para empleos tech, California, Washington, Texas y la costa Este son los mejores.",
                "en": "For tech jobs, California, Washington, Texas and the East Coast are the best.",
            },
        },
        "latino": {
            "regions": ["south", "west"],
            "states": ["Florida", "Texas", "California", "New York", "New Jersey"],
            "description": {
                "es": "Para comunidad latina grande, Florida, Texas, California y Nueva York tienen las más grandes.",
                "en": "For large Latino community, Florida, Texas, California and New York have the largest.",
            },
        },
    }

    @classmethod
    def get_recommendation(cls, preference: str, lang: str = "es") -> dict[str, Any]:
        """Obtener recomendación basada en preferencia"""
        pref_data = cls.PREFERENCES.get(preference, cls.PREFERENCES["tech"])

        return {
            "regions": pref_data["regions"],
            "states": pref_data["states"],
            "description": pref_data["description"].get(lang, pref_data["description"]["es"]),
        }


# ============== ONBOARDING CONVERSACIONAL ==============


class ConversationalOnboarding:
    """
    Onboarding conversacional con saludo, empatía y explicación breve.
    Formularios solo cuando aplique, con opción "otro: escribir".
    """

    @classmethod
    def get_welcome_message(cls, name: str, lang: str = "es") -> str:
        """Obtener mensaje de bienvenida conversacional"""
        greeting = MigPALPersonality.get_greeting(name, lang)
        empathy = MigPALPersonality.get_empathy("understanding", lang)
        explanation = MigPALPersonality.get_explanation("process", lang)

        if lang == "es":
            return f"{greeting}\n\n" f"{empathy}\n\n" f"{explanation}\n\n" "¿Listo/a para empezar? 🚀"
        else:
            return f"{greeting}\n\n" f"{empathy}\n\n" f"{explanation}\n\n" "Ready to start? 🚀"

    @classmethod
    def get_question_with_other(
        cls, question: str, options: list[tuple[str, str]], lang: str = "es"
    ) -> tuple[str, list[tuple[str, str]]]:
        """
        Agregar opción "Otro: escribir" a las opciones.

        Args:
            question: Pregunta a mostrar
            options: Lista de (texto, callback_data)
            lang: Idioma

        Returns:
            Tuple[question, options_with_other]
        """
        other_option = (
            ("✏️ Otro (escribir)", "other_write") if lang == "es" else ("✏️ Other (write)", "other_write")
        )

        options_with_other = list(options) + [other_option]

        return question, options_with_other


# ============== SOPORTE DE VOZ ==============


class VoiceSupport:
    """Soporte para mensajes de voz: transcribir, parafrasear y confirmar"""

    @classmethod
    def get_transcription_confirmation(cls, transcription: str, lang: str = "es") -> str:
        """Obtener mensaje de confirmación de transcripción"""
        if lang == "es":
            return f'🎤 Escuché: "{transcription}"\n\n' "¿Es correcto?"
        else:
            return f'🎤 I heard: "{transcription}"\n\n' "Is that correct?"

    @classmethod
    def get_paraphrase(cls, text: str, context: str, lang: str = "es") -> str:
        """Parafrasear el texto según el contexto"""
        # Simplificar para el contexto actual
        if lang == "es":
            return f"Entendí que {text.lower()}. ¿Es correcto?"
        else:
            return f"I understood that {text.lower()}. Is that correct?"


# ============== MULTI-SELECT ==============


class MultiSelect:
    """Soporte para selección múltiple en opciones"""

    @classmethod
    def create_multi_select_keyboard(
        cls, options: list[tuple[str, str]], selected: list[str] = None
    ) -> list[list[tuple[str, str]]]:
        """
        Crear teclado con checkboxes para selección múltiple.

        Args:
            options: Lista de (texto, callback_data)
            selected: Lista de callback_data seleccionados

        Returns:
            Lista de filas de botones
        """
        selected = selected or []

        keyboard = []
        for text, data in options:
            # Agregar checkbox
            checkbox = "✅ " if data in selected else "⬜ "
            keyboard.append([(f"{checkbox}{text}", f"multi_{data}")])

        # Agregar botón de confirmar
        keyboard.append([("✔️ Confirmar selección", "multi_confirm")])

        return keyboard

    @classmethod
    def toggle_selection(cls, current: list[str], item: str) -> list[str]:
        """Toggle un item en la selección"""
        if item in current:
            return [x for x in current if x != item]
        else:
            return current + [item]


# ============== LOGGING MEJORADO ==============


def log_user_interaction(user_id: int, interaction_type: str, details: dict[str, Any]):
    """Log detallado de interacción de usuario"""
    logger.info(f"👤 USER_INTERACTION | user={user_id} | type={interaction_type} | " f"details={details}")


def log_correction_detected(user_id: int, correction: CorrectionIntent):
    """Log de corrección detectada"""
    logger.info(
        f"✏️ CORRECTION_DETECTED | user={user_id} | type={correction.type.value} | "
        f"value={correction.value} | confidence={correction.confidence:.2f}"
    )


def log_markdown_error(user_id: int, original_text: str, error: str):
    """Log de error de Markdown"""
    logger.warning(
        f"⚠️ MARKDOWN_ERROR | user={user_id} | error={error} | " f"text_preview={original_text[:50]}..."
    )
