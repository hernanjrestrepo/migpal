"""
MigPAL Profile Validator v1.0
=============================
Valida que el perfil del usuario esté confirmado antes de hacer recomendaciones.

REGLA CRÍTICA: Prohibido decir "basado en tu perfil" si el perfil no está confirmado.

Este módulo implementa:
- Validación de campos confirmados por el usuario
- Generación de mensajes apropiados según estado del perfil
- Tracking de confirmaciones explícitas del usuario
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProfileConfirmation:
    """Estado de confirmación del perfil de un usuario"""

    user_id: int
    confirmed_fields: dict[str, datetime] = field(default_factory=dict)
    summary_confirmed: bool = False
    summary_confirmed_at: datetime | None = None
    last_correction: datetime | None = None


class ProfileValidator:
    """
    Valida que el perfil del usuario esté confirmado antes de usarlo.

    REGLA: No se puede decir "basado en tu perfil" si:
    1. El perfil no tiene datos confirmados por el usuario
    2. El usuario no ha visto/confirmado el resumen de comprensión
    3. El usuario ha hecho correcciones recientes no confirmadas
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._confirmations: dict[int, ProfileConfirmation] = {}
        return cls._instance

    # Campos mínimos requeridos para usar "basado en tu perfil"
    MINIMUM_CONFIRMED_FIELDS = ["name"]

    # Campos que dan más confianza al perfil
    CONFIDENCE_FIELDS = [
        "name",
        "birth_date",
        "nationality",
        "profession",
        "education_level",
        "english_level",
        "migration_reason",
    ]

    def get_confirmation(self, user_id: int) -> ProfileConfirmation:
        """Obtiene el estado de confirmación del usuario"""
        if user_id not in self._confirmations:
            self._confirmations[user_id] = ProfileConfirmation(user_id=user_id)
        return self._confirmations[user_id]

    def confirm_field(self, user_id: int, field_name: str):
        """Marca un campo como confirmado por el usuario"""
        confirmation = self.get_confirmation(user_id)
        confirmation.confirmed_fields[field_name] = datetime.now()
        logger.info(f"✅ PROFILE | user={user_id} | field_confirmed={field_name}")

    def confirm_summary(self, user_id: int):
        """Marca el resumen de comprensión como confirmado"""
        confirmation = self.get_confirmation(user_id)
        confirmation.summary_confirmed = True
        confirmation.summary_confirmed_at = datetime.now()
        logger.info(f"✅ PROFILE | user={user_id} | summary_confirmed=True")

    def register_correction(self, user_id: int, field_name: str):
        """Registra una corrección del usuario (invalida confirmación del campo)"""
        confirmation = self.get_confirmation(user_id)
        confirmation.last_correction = datetime.now()
        # Remover confirmación del campo corregido
        if field_name in confirmation.confirmed_fields:
            del confirmation.confirmed_fields[field_name]
        logger.info(f"✏️ PROFILE | user={user_id} | field_corrected={field_name}")

    def reset_user(self, user_id: int):
        """Resetea todas las confirmaciones de un usuario"""
        if user_id in self._confirmations:
            del self._confirmations[user_id]
        logger.info(f"🔄 PROFILE | user={user_id} | reset=True")

    def can_use_profile_based_message(self, user_id: int, user_data: dict[str, Any]) -> tuple[bool, str]:
        """
        Verifica si se puede usar "basado en tu perfil".

        Returns:
            (can_use, reason)
        """
        confirmation = self.get_confirmation(user_id)

        # Verificar si hay campos mínimos confirmados
        has_minimum = all(field in confirmation.confirmed_fields for field in self.MINIMUM_CONFIRMED_FIELDS)

        if not has_minimum:
            return False, "no_minimum_fields"

        # Verificar si el perfil tiene datos reales (no solo telegram_name)
        profile = user_data.get("profile", {})
        personal = profile.get("personal", {})

        # El nombre debe existir y no ser solo el telegram_name
        name = personal.get("name")
        telegram_name = personal.get("telegram_name")

        if not name or name == telegram_name:
            return False, "name_not_confirmed"

        # Si hay corrección reciente sin confirmar, no usar
        if confirmation.last_correction:
            time_since_correction = (datetime.now() - confirmation.last_correction).total_seconds()
            if time_since_correction < 60:  # 1 minuto
                return False, "recent_correction"

        return True, "allowed"

    def get_profile_confidence_level(self, user_id: int) -> tuple[str, float]:
        """
        Calcula el nivel de confianza del perfil.

        Returns:
            (level, percentage)
            level: "low", "medium", "high"
            percentage: 0.0 - 1.0
        """
        confirmation = self.get_confirmation(user_id)

        confirmed_count = len(confirmation.confirmed_fields)
        total_fields = len(self.CONFIDENCE_FIELDS)

        percentage = confirmed_count / total_fields if total_fields > 0 else 0.0

        if percentage < 0.3:
            return "low", percentage
        elif percentage < 0.7:
            return "medium", percentage
        else:
            return "high", percentage

    def get_confirmed_fields_list(self, user_id: int) -> list[str]:
        """Retorna lista de campos confirmados"""
        confirmation = self.get_confirmation(user_id)
        return list(confirmation.confirmed_fields.keys())


# Singleton instance
_profile_validator: ProfileValidator | None = None


def get_profile_validator() -> ProfileValidator:
    """Obtiene la instancia singleton del validador de perfil"""
    global _profile_validator
    if _profile_validator is None:
        _profile_validator = ProfileValidator()
    return _profile_validator


def get_profile_based_intro(user_id: int, user_data: dict[str, Any], lang: str = "es") -> str:
    """
    Genera el intro apropiado según el estado del perfil.

    Si el perfil está confirmado: "Basado en tu perfil..."
    Si no está confirmado: Mensaje alternativo sin asumir datos
    """
    validator = get_profile_validator()
    can_use, reason = validator.can_use_profile_based_message(user_id, user_data)

    if can_use:
        # Obtener datos confirmados para personalizar
        profile = user_data.get("profile", {})
        personal = profile.get("personal", {})
        work = profile.get("work", {})

        personal.get("name", "")
        profession = work.get("profession", "")

        if profession:
            if lang == "es":
                return f"Basado en tu perfil como {profession}"
            else:
                return f"Based on your profile as a {profession}"
        else:
            if lang == "es":
                return "Basado en lo que me has contado"
            else:
                return "Based on what you've told me"
    else:
        # Mensaje alternativo sin asumir datos
        if lang == "es":
            alternatives = {
                "no_minimum_fields": "Para darte una recomendación personalizada, cuéntame más sobre ti",
                "name_not_confirmed": "Primero, ¿cómo te llamas?",
                "recent_correction": "Entendido. Con esta información actualizada",
            }
            return alternatives.get(reason, "Cuéntame más sobre ti para ayudarte mejor")
        else:
            alternatives = {
                "no_minimum_fields": "To give you a personalized recommendation, tell me more about yourself",
                "name_not_confirmed": "First, what's your name?",
                "recent_correction": "Got it. With this updated information",
            }
            return alternatives.get(reason, "Tell me more about yourself so I can help you better")


def is_profile_confirmed(user_id: int, user_data: dict[str, Any]) -> bool:
    """Verifica si el perfil está confirmado para usar en recomendaciones"""
    validator = get_profile_validator()
    can_use, _ = validator.can_use_profile_based_message(user_id, user_data)
    return can_use


# ============== PRIORITY INTENT HANDLER ==============


class PriorityIntentHandler:
    """
    Maneja intents prioritarios que deben procesarse ANTES de cualquier flujo.

    REGLA: Las preguntas, confusión, preocupaciones y reclamos del usuario
    tienen PRIORIDAD sobre cualquier flujo interno del bot.

    V5.0 FIX: emotion_clarification solo se activa con señales EXPLÍCITAS de confusión.
    NO se activa cuando el usuario responde coherentemente a una pregunta activa.

    Señales EXPLÍCITAS de confusión (únicas que activan emotion_clarification):
    - "no entiendo", "estoy confundido/a", "me perdí", "estoy perdido/a"
    - "no comprendo", "no me queda claro"
    - "confused", "don't understand", "lost"

    NO son señales de confusión (respuestas válidas):
    - "soy ingeniero" (respuesta a ¿a qué te dedicas?)
    - "tengo una empresa" (respuesta a ocupación)
    - "no sé" seguido de información ("no sé, pero trabajo en...")
    """

    # V5.0: Patrones de intents prioritarios RESTRINGIDOS
    # Solo señales EXPLÍCITAS de confusión activan emotion_clarification
    PRIORITY_PATTERNS = {
        "confusion": [
            # V5.0: SOLO expresiones EXPLÍCITAS de confusión
            # Removidos: "ajá", "qué pasa", "no sé" (son respuestas válidas)
            r"\bno entiendo\b",
            r"\bno comprendo\b",
            r"\bestoy confundid[oa]\b",
            r"\bconfundid[oa]\b",
            r"\bme perdí\b",
            r"\bestoy perdid[oa]\b",
            r"\bperdid[oa]\b",
            r"\bno me queda claro\b",
            r"\bno capto\b",
            r"\bno pillo\b",
            r"\bdon't understand\b",
            r"\bconfused\b",
            r"\bi'm lost\b",
            r"\bwhat do you mean\b",
            r"\bwhat does.*mean\b",
            # V5.0.1: Variaciones adicionales
            r"estoy confundido",
            r"estoy confundida",
            r"estoy perdido",
            r"estoy perdida",
        ],
        "frustration": [
            # V5.0: Expresiones de frustración que indican que el bot no escucha
            r"\bya te dije\b",
            r"\bte lo dije\b",
            r"\bya dije\b",
            r"\beso ya lo dije\b",
            r"\bte lo acabo de decir\b",
            r"\bno me escuchas\b",
            r"\bno entiendes\b",
            r"\brepites\b",
            r"\bya te conté\b",
            r"\bya te conte\b",
            r"\balready told you\b",
            r"\byou're not listening\b",
        ],
        "concern": [
            # Expresiones de preocupación
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
            r"es seguro",
            r"es confiable",
            r"puedo confiar",
            r"será seguro",
            r"me asusta",
            r"me inquieta",
            r"riesgoso",
            r"peligroso",
        ],
        "complaint": [
            r"no funciona",
            r"está mal",
            r"error",
            r"problema",
            r"no sirve",
            r"doesn't work",
            r"broken",
            r"wrong",
            r"esto no es lo que",
            r"no es correcto",
            r"incorrecto",
        ],
        "question": [
            # Preguntas explícitas (detectar DESPUÉS de confusion/frustration)
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
            r"^es posible ",
            r"^se puede ",
            r"^hay forma ",
        ],
    }

    # Respuestas empáticas por tipo de intent
    EMPATHIC_RESPONSES = {
        "es": {
            "question": "Buena pregunta. 🤔 Déjame explicarte...",
            "confusion": "Entiendo que puede ser confuso. 💭 Déjame aclararte...",
            "concern": "Entiendo tu preocupación. 🤝 Es completamente normal sentirse así...",
            "frustration": "Perdona si no fui claro. 🙏 Déjame explicarte mejor...",
            "complaint": "Lamento que tengas ese problema. 😔 Déjame ayudarte...",
        },
        "en": {
            "question": "Good question. 🤔 Let me explain...",
            "confusion": "I understand it can be confusing. 💭 Let me clarify...",
            "concern": "I understand your concern. 🤝 It's completely normal to feel that way...",
            "frustration": "Sorry if I wasn't clear. 🙏 Let me explain better...",
            "complaint": "I'm sorry you're having that problem. 😔 Let me help you...",
        },
    }

    # V5.0: Patrones que indican respuesta VÁLIDA a una pregunta
    # Si el usuario da información, NO es confusión
    VALID_RESPONSE_PATTERNS = [
        # Ocupación/Profesión
        r"\bsoy\s+(ingenier|doctor|abogad|profesor|contador|enferm|programador|diseñador|arquitect|médic|psicólog|econom|administrador|gerente|director|analista|consultor|vendedor|chef|cocinero|electricista|mecánic|plomero|carpintero|maestro|periodista|escritor|músic|artista|fotógraf|veterinari|farmacéutic|biólog|químic|físic|matemátic)",
        r"\btrabajo\s+(como|en|de)\b",
        r"\btengo\s+(una\s+)?(empresa|negocio|compañía|startup)\b",
        r"\bmi\s+(profesión|trabajo|ocupación)\b",
        # Información personal
        r"\bme\s+llamo\b",
        r"\bmi\s+nombre\s+es\b",
        r"\btengo\s+\d+\s+(años|meses)\b",
        # Destino/Migración
        r"\bquiero\s+(ir|migrar|vivir)\b",
        r"\b(estados\s+unidos|usa|canada|españa|alemania|australia)\b",
        # Presupuesto
        r"\$\d+",
        r"\bpresupuesto\b",
        # Confirmaciones
        r"^(sí|si|yes|ok|okay|claro|correcto|exacto|así es|eso es)$",
        # Negaciones con información
        r"\bno\s+(tengo|sé|se)\s+.{5,}",  # "no tengo experiencia en..." es válido
    ]

    # V5.0: Señales EXPLÍCITAS de confusión que NUNCA son respuestas válidas
    EXPLICIT_CONFUSION_SIGNALS = [
        "no entiendo",
        "no comprendo",
        "no me queda claro",
        "confundido",
        "confundida",
        "confundid",  # Variaciones de género
        "perdido",
        "perdida",
        "perdí",
        "me perdí",
        "no capto",
        "no pillo",
        "confused",
        "lost",
        "don't understand",
        "what do you mean",
        "what does that mean",
    ]

    @staticmethod
    def is_valid_response(text: str) -> bool:
        """
        V5.0: Detecta si el texto es una respuesta VÁLIDA a una pregunta.
        Si es válida, NO debe activar emotion_clarification.

        REGLA: Si el texto contiene señales EXPLÍCITAS de confusión,
        NO es una respuesta válida.

        Returns:
            True si es una respuesta válida, False si no
        """
        import re

        text_lower = text.lower().strip()

        # V5.0 FIX: Primero verificar si tiene señales explícitas de confusión
        # Si las tiene, NO es respuesta válida
        for signal in PriorityIntentHandler.EXPLICIT_CONFUSION_SIGNALS:
            if signal in text_lower:
                return False

        # Verificar patrones de respuesta válida
        for pattern in PriorityIntentHandler.VALID_RESPONSE_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        # Si el texto tiene más de 10 caracteres y no tiene signos de confusión,
        # probablemente es una respuesta válida
        if len(text_lower) > 10:
            return True

        return False

    @staticmethod
    def detect_priority_intent(text: str, current_state: str = "") -> str | None:
        """
        V5.0: Detecta si el texto contiene un intent prioritario.
        IMPORTANTE: Si el usuario está respondiendo coherentemente, NO detectar confusión.

        Args:
            text: Texto del usuario
            current_state: Estado actual del flujo (para contexto)

        Returns:
            Tipo de intent ("question", "confusion", etc.) o None
        """
        import re

        text_lower = text.lower().strip()

        # V5.0 FIX: Primero verificar si es una respuesta válida
        # Si el usuario está dando información, NO es confusión
        if PriorityIntentHandler.is_valid_response(text):
            logger.debug(f"🟢 VALID_RESPONSE | text={text[:50]} | NOT triggering confusion")
            return None

        for intent_type, patterns in PriorityIntentHandler.PRIORITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    # V5.0: Para confusión, verificar que sea EXPLÍCITA
                    if intent_type == "confusion":
                        # Solo activar si es confusión explícita Y no hay información útil
                        if len(text_lower) > 50:  # Mensajes largos probablemente tienen info
                            logger.debug("🟡 CONFUSION_SKIPPED | text too long, likely has info")
                            continue
                    return intent_type

        return None

    @staticmethod
    def get_empathic_response(intent_type: str, lang: str = "es") -> str:
        """Obtiene respuesta empática para el tipo de intent"""
        responses = PriorityIntentHandler.EMPATHIC_RESPONSES.get(
            lang, PriorityIntentHandler.EMPATHIC_RESPONSES["es"]
        )
        return responses.get(intent_type, responses["question"])

    @staticmethod
    def should_interrupt_flow(
        text: str, current_state: str = "", active_question: str = ""
    ) -> tuple[bool, str | None, str | None]:
        """
        V5.0: Determina si el input debe interrumpir el flujo actual.

        REGLA CRÍTICA: Si hay una pregunta activa y el usuario responde coherentemente,
        NO interrumpir el flujo con emotion_clarification.

        Args:
            text: Texto del usuario
            current_state: Estado actual del flujo
            active_question: Pregunta activa que el bot hizo (para contexto)

        Returns:
            (should_interrupt, intent_type, empathic_response)
        """
        # V5.0 FIX: Primero verificar si es respuesta válida
        if PriorityIntentHandler.is_valid_response(text):
            logger.info(f"✅ VALID_RESPONSE | NOT interrupting flow | text={text[:50]}")
            return False, None, None

        intent_type = PriorityIntentHandler.detect_priority_intent(text, current_state)

        if intent_type:
            # V5.0: Para confusión, ser más estricto
            if intent_type == "confusion":
                # Solo interrumpir si es confusión EXPLÍCITA
                # V5.0.1: Usar la constante EXPLICIT_CONFUSION_SIGNALS
                text_lower = text.lower()
                if not any(
                    signal in text_lower for signal in PriorityIntentHandler.EXPLICIT_CONFUSION_SIGNALS
                ):
                    logger.info(f"🟡 CONFUSION_NOT_EXPLICIT | NOT interrupting | text={text[:50]}")
                    return False, None, None

            # Detectar idioma del texto
            lang = "es" if any(c in text.lower() for c in ["á", "é", "í", "ó", "ú", "ñ", "¿", "¡"]) else "en"
            empathic_response = PriorityIntentHandler.get_empathic_response(intent_type, lang)
            return True, intent_type, empathic_response

        return False, None, None


def get_priority_intent_handler() -> PriorityIntentHandler:
    """Obtiene instancia del handler de intents prioritarios"""
    return PriorityIntentHandler()
