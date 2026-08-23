"""
MigPAL Availability Watchdog - SEGMENTO 1/3
=============================================
REGLAS DURAS DE DISPONIBILIDAD Y RESPUESTA:

1. Todo input (texto, botón, silencio > X seg) debe generar respuesta
2. Si falla un handler → fallback conversacional empático (NO genérico)
3. Si ocurre excepción → responder + loggear, nunca callar
4. Watchdog: si no hay respuesta en <3s, enviar "Sigo aquí, dame un segundo"
5. Prohibido estados muertos: ningún state sin salida válida
6. Priorizar responder algo útil antes que "hacerlo perfecto"
7. Si MigPAL no responde, el sistema está roto

Este módulo implementa:
- ResponseWatchdog: Timer de 3s que envía mensaje si no hay respuesta
- EmpathicFallback: Mensajes de fallback conversacionales, NO genéricos
- DeadStateDetector: Detecta y recupera estados sin salida
- GuaranteedResponse: Decorador que GARANTIZA respuesta
"""

import asyncio
import logging
import traceback
from collections.abc import Callable
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

# ============== CONFIGURACIÓN ==============

# V5.0 FIX: WATCHDOG COMPLETAMENTE DESHABILITADO
# Los mensajes "⏳ Sigo aquí" causan más problemas que soluciones:
# - Interrumpen la conversación natural
# - Generan confusión en el usuario
# - Duplican mensajes cuando hay latencia de IA
WATCHDOG_ENABLED = False  # DESHABILITADO PERMANENTEMENTE

WATCHDOG_TIMEOUT_SECONDS = 10.0  # No usado - watchdog deshabilitado
MAX_RESPONSE_TIME_SECONDS = 30.0  # Tiempo máximo antes de forzar respuesta
EMPATHIC_FALLBACK_ENABLED = True  # Usar fallbacks empáticos vs genéricos
WATCHDOG_THROTTLE_SECONDS = 300.0  # No usado - watchdog deshabilitado

# V4.2.1 FIX: Estados donde el watchdog está DESHABILITADO (usan IA intensiva)
WATCHDOG_DISABLED_STATES = {
    "start",  # Estado inicial puede usar IA
    "emotion_clarification",  # Clarificación emocional usa IA
    "onboarding_question",  # Onboarding puede usar IA
    "onboarding_listening",  # Escucha activa usa IA
    "consulting",  # Consultoría usa IA intensiva
}


# ============== MENSAJES EMPÁTICOS DE FALLBACK ==============

EMPATHIC_FALLBACKS = {
    "es": {
        # Mensaje de watchdog (3 segundos sin respuesta)
        "watchdog_waiting": "⏳ Sigo aquí, dame un segundo...",
        "watchdog_processing": "🔄 Estoy procesando tu información...",
        "watchdog_thinking": "💭 Déjame pensar en la mejor respuesta para ti...",
        # Fallbacks por contexto (NO genéricos)
        "handler_error": "😅 Ups, algo no salió como esperaba. Pero no te preocupes, ¿me repites lo que necesitas?",
        "unknown_input": "🤔 No estoy seguro de entender. ¿Podrías decírmelo de otra forma?",
        "state_recovery": "📍 Parece que nos perdimos un poco. Volvamos a donde estábamos: {context}",
        "timeout_recovery": "⏰ Perdona la demora. ¿En qué te puedo ayudar?",
        # Fallbacks por fase del proceso
        "phase_profile": "👤 Estamos en tu perfil. ¿Cuál es tu nombre completo?",
        "phase_education": "🎓 Cuéntame sobre tu educación. ¿Cuál es tu nivel de estudios?",
        "phase_work": "💼 Hablemos de tu experiencia laboral. ¿A qué te dedicas?",
        "phase_family": "👨‍👩‍👧 Ahora sobre tu familia. ¿Viajas solo o con familia?",
        "phase_preferences": "🎯 Definamos tus preferencias. ¿Por qué quieres migrar?",
        "phase_exploration": "🗺️ Exploremos opciones. ¿Qué país te interesa?",
        # Fallback de último recurso (empático, no genérico)
        "last_resort": "🤝 Estoy aquí para ayudarte. Escríbeme lo que necesitas y te guío paso a paso.",
        # Confirmaciones de que seguimos activos
        "still_here": "👋 ¡Sigo aquí! ¿En qué te ayudo?",
        "ready_to_help": "✨ Listo para continuar. ¿Qué necesitas?",
    },
    "en": {
        "watchdog_waiting": "⏳ Still here, give me a second...",
        "watchdog_processing": "🔄 Processing your information...",
        "watchdog_thinking": "💭 Let me think of the best answer for you...",
        "handler_error": "😅 Oops, something didn't go as expected. No worries, can you repeat what you need?",
        "unknown_input": "🤔 I'm not sure I understand. Could you say it differently?",
        "state_recovery": "📍 Looks like we got a bit lost. Let's go back to where we were: {context}",
        "timeout_recovery": "⏰ Sorry for the delay. How can I help you?",
        "phase_profile": "👤 We're on your profile. What's your full name?",
        "phase_education": "🎓 Tell me about your education. What's your education level?",
        "phase_work": "💼 Let's talk about your work experience. What do you do?",
        "phase_family": "👨‍👩‍👧 Now about your family. Are you traveling alone or with family?",
        "phase_preferences": "🎯 Let's define your preferences. Why do you want to migrate?",
        "phase_exploration": "🗺️ Let's explore options. Which country interests you?",
        "last_resort": "🤝 I'm here to help. Write me what you need and I'll guide you step by step.",
        "still_here": "👋 Still here! How can I help?",
        "ready_to_help": "✨ Ready to continue. What do you need?",
    },
}

# Mapeo de estados a fases para fallbacks contextuales
STATE_TO_PHASE = {
    "start": "phase_profile",
    "name": "phase_profile",
    "confirm_name": "phase_profile",
    "birth_date": "phase_profile",
    "nationality": "phase_profile",
    "current_country": "phase_profile",
    "current_city": "phase_profile",
    "email": "phase_profile",
    "phone": "phase_profile",
    "education_level": "phase_education",
    "education_status": "phase_education",
    "education_field": "phase_education",
    "education_career": "phase_education",
    "work_status": "phase_work",
    "profession": "phase_work",
    "work_experience": "phase_work",
    "linkedin": "phase_work",
    "english_level": "phase_work",
    "visa_history": "phase_profile",
    "visa_details": "phase_profile",
    "visa_rejections": "phase_profile",
    "criminal_record": "phase_profile",
    "health_conditions": "phase_profile",
    "savings": "phase_profile",
    "family_status": "phase_family",
    "family_count": "phase_family",
    "family_member_relation": "phase_family",
    "family_member_name": "phase_family",
    "family_member_birth": "phase_family",
    "migration_reason": "phase_preferences",
    "timeline": "phase_preferences",
    "destination_preference": "phase_preferences",
    "climate_preference": "phase_preferences",
    "city_size_preference": "phase_preferences",
    "budget_initial": "phase_preferences",
    "select_country": "phase_exploration",
    "select_visa": "phase_exploration",
    "select_state": "phase_exploration",
    "select_city": "phase_exploration",
}


# ============== RESPONSE WATCHDOG ==============


class ResponseWatchdog:
    """
    Watchdog que garantiza respuesta en menos de 3 segundos.
    Si el handler tarda más, envía mensaje de "Sigo aquí...".

    THROTTLE: Máximo 1 mensaje "sigo aquí" cada 5 minutos por usuario
    para evitar spam y mantener la conversación natural.
    """

    _instance = None
    _pending_responses: dict[int, asyncio.Task] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._pending_responses = {}
            cls._instance._response_sent = {}
            cls._instance._last_watchdog_message = {}  # Throttle: último mensaje por usuario
        return cls._instance

    def _can_send_watchdog_message(self, user_id: int) -> bool:
        """
        Verifica si se puede enviar mensaje de watchdog (throttle).
        Máximo 1 mensaje cada WATCHDOG_THROTTLE_SECONDS por usuario.
        """
        now = datetime.now()
        last_sent = self._last_watchdog_message.get(user_id)

        if last_sent is None:
            return True

        time_since_last = (now - last_sent).total_seconds()
        return time_since_last >= WATCHDOG_THROTTLE_SECONDS

    def _record_watchdog_message(self, user_id: int):
        """Registra que se envió un mensaje de watchdog"""
        self._last_watchdog_message[user_id] = datetime.now()

    async def start_watchdog(
        self, user_id: int, send_callback: Callable, lang: str = "es", current_state: str = ""
    ):
        """
        Inicia el watchdog para un usuario.
        V5.0: COMPLETAMENTE DESHABILITADO - los mensajes "⏳" causan más problemas.
        """
        # V5.0 FIX: Watchdog completamente deshabilitado
        if not WATCHDOG_ENABLED:
            logger.debug(f"⏱️ WATCHDOG DISABLED GLOBALLY | user={user_id}")
            return

        # V4.2.1 FIX: No iniciar watchdog en estados con IA intensiva
        if current_state in WATCHDOG_DISABLED_STATES:
            logger.debug(f"⏱️ WATCHDOG DISABLED | user={user_id} | state={current_state} (IA intensive)")
            return

        # Cancelar watchdog anterior si existe
        if user_id in self._pending_responses:
            self._pending_responses[user_id].cancel()

        self._response_sent[user_id] = False

        async def watchdog_timer():
            try:
                await asyncio.sleep(WATCHDOG_TIMEOUT_SECONDS)

                # Si no se ha enviado respuesta, enviar mensaje de espera (con throttle)
                if not self._response_sent.get(user_id, False):
                    # THROTTLE: Solo enviar si no se ha enviado recientemente
                    if self._can_send_watchdog_message(user_id):
                        messages = EMPATHIC_FALLBACKS.get(lang, EMPATHIC_FALLBACKS["es"])
                        watchdog_msg = messages["watchdog_waiting"]

                        try:
                            await send_callback(watchdog_msg)
                            self._record_watchdog_message(user_id)
                            logger.info(
                                f"⏱️ WATCHDOG | user={user_id} | Sent waiting message after {WATCHDOG_TIMEOUT_SECONDS}s"
                            )
                        except Exception as e:
                            logger.error(f"⏱️ WATCHDOG | user={user_id} | Failed to send: {e}")
                    else:
                        logger.debug(f"⏱️ WATCHDOG THROTTLED | user={user_id} | Skipping (sent recently)")

            except asyncio.CancelledError:
                # Watchdog cancelado porque se envió respuesta a tiempo
                pass

        self._pending_responses[user_id] = asyncio.create_task(watchdog_timer())

    def mark_response_sent(self, user_id: int):
        """Marca que se envió respuesta y cancela el watchdog"""
        self._response_sent[user_id] = True

        if user_id in self._pending_responses:
            self._pending_responses[user_id].cancel()
            del self._pending_responses[user_id]

    def cancel_watchdog(self, user_id: int):
        """Cancela el watchdog sin marcar respuesta"""
        if user_id in self._pending_responses:
            self._pending_responses[user_id].cancel()
            del self._pending_responses[user_id]


# ============== EMPATHIC FALLBACK GENERATOR ==============


class EmpathicFallback:
    """
    Genera fallbacks empáticos basados en contexto.
    NUNCA devuelve mensajes genéricos.
    """

    @staticmethod
    def get_fallback(lang: str, context_type: str, state: str = "", extra_context: str = "") -> str:
        """
        Obtiene un fallback empático basado en el contexto.

        Args:
            lang: Idioma (es/en)
            context_type: Tipo de contexto (handler_error, unknown_input, etc.)
            state: Estado actual del usuario
            extra_context: Contexto adicional para personalizar

        Returns:
            Mensaje de fallback empático
        """
        messages = EMPATHIC_FALLBACKS.get(lang, EMPATHIC_FALLBACKS["es"])

        # Intentar obtener mensaje específico del contexto
        if context_type in messages:
            msg = messages[context_type]
            if "{context}" in msg and extra_context:
                msg = msg.format(context=extra_context)
            return msg

        # Si no hay mensaje específico, usar fallback de fase
        if state:
            phase = STATE_TO_PHASE.get(state, "")
            if phase and phase in messages:
                return messages[phase]

        # Último recurso: mensaje empático general
        return messages.get("last_resort", messages.get("still_here", "🤝 Estoy aquí para ayudarte."))

    @staticmethod
    def get_phase_fallback(lang: str, state: str) -> str:
        """Obtiene fallback específico de la fase actual"""
        messages = EMPATHIC_FALLBACKS.get(lang, EMPATHIC_FALLBACKS["es"])
        phase = STATE_TO_PHASE.get(state, "")

        if phase and phase in messages:
            return messages[phase]

        return messages.get("last_resort", "🤝 Estoy aquí para ayudarte.")

    @staticmethod
    def get_error_fallback(lang: str, error_type: str = "handler_error") -> str:
        """Obtiene fallback para errores"""
        messages = EMPATHIC_FALLBACKS.get(lang, EMPATHIC_FALLBACKS["es"])
        return messages.get(error_type, messages.get("handler_error", "😅 Algo salió mal, pero sigo aquí."))


# ============== DEAD STATE DETECTOR ==============


class DeadStateDetector:
    """
    Detecta estados sin salida válida y los recupera.
    Ningún estado puede quedar sin respuesta posible.
    """

    # Estados que DEBEN tener handlers definidos
    REQUIRED_HANDLERS = {
        "start",
        "name",
        "confirm_name",
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
        "linkedin",
        "english_level",
        "visa_history",
        "visa_details",
        "visa_rejections",
        "criminal_record",
        "health_conditions",
        "savings",
        "family_status",
        "family_count",
        "family_member_relation",
        "family_member_name",
        "family_member_birth",
        "migration_reason",
        "timeline",
        "destination_preference",
        "climate_preference",
        "city_size_preference",
        "budget_initial",
        "select_country",
        "select_visa",
        "select_state",
        "select_city",
    }

    # Transiciones válidas desde cada estado
    VALID_TRANSITIONS = {
        "start": ["name"],
        "name": ["confirm_name", "birth_date"],
        "confirm_name": ["name", "birth_date"],
        "birth_date": ["nationality"],
        # ... (se puede expandir según necesidad)
    }

    @staticmethod
    def is_dead_state(state: str, available_handlers: set) -> bool:
        """Verifica si un estado no tiene handler"""
        return state not in available_handlers and state in DeadStateDetector.REQUIRED_HANDLERS

    @staticmethod
    def get_recovery_state(current_state: str) -> str:
        """Obtiene el estado de recuperación para un estado muerto"""
        # Mapeo de estados muertos a estados de recuperación
        recovery_map = {
            # Si estamos en un estado de perfil, volver a name
            "confirm_name": "name",
            "birth_date": "name",
            "nationality": "name",
            # Si estamos en educación, volver a education_level
            "education_status": "education_level",
            "education_field": "education_level",
            "education_career": "education_level",
            # Default: volver a start
        }

        return recovery_map.get(current_state, "start")

    @staticmethod
    def validate_all_states(handlers: dict[str, Callable]) -> tuple[bool, list[str]]:
        """
        Valida que todos los estados requeridos tengan handlers.
        Returns: (is_valid, list_of_dead_states)
        """
        dead_states = []
        handler_states = set(handlers.keys()) if handlers else set()

        for state in DeadStateDetector.REQUIRED_HANDLERS:
            if state not in handler_states:
                dead_states.append(state)

        return len(dead_states) == 0, dead_states


# ============== GUARANTEED RESPONSE DECORATOR ==============


def guaranteed_response(fallback_type: str = "handler_error"):
    """
    Decorador que GARANTIZA que siempre se envíe una respuesta.

    Reglas:
    1. Si el handler funciona → respuesta normal
    2. Si hay excepción → fallback empático + log
    3. Si hay timeout → fallback de timeout
    4. NUNCA se queda sin responder

    Usage:
        @guaranteed_response("handler_error")
        async def my_handler(update, context):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            update = None
            user_id = 0
            lang = "es"
            state = "unknown"

            # Extraer update de los argumentos
            for arg in args:
                if hasattr(arg, "effective_user"):
                    update = arg
                    user_id = arg.effective_user.id if arg.effective_user else 0
                    break

            # Obtener idioma y estado del usuario
            try:
                from app.services.telegram_bot import get_state, get_user_data

                if user_id:
                    user = get_user_data(user_id)
                    lang = user.get("language", "es")
                    state = get_state(user_id)
            except:
                pass

            # Función para enviar mensaje
            async def send_message(text: str):
                if update:
                    try:
                        if hasattr(update, "message") and update.message:
                            await update.message.reply_text(text)
                        elif hasattr(update, "callback_query") and update.callback_query:
                            await update.callback_query.message.reply_text(text)
                    except Exception as e:
                        logger.error(f"Failed to send guaranteed response: {e}")

            # Iniciar watchdog
            watchdog = ResponseWatchdog()
            await watchdog.start_watchdog(user_id, send_message, lang)

            response_sent = False

            try:
                # Ejecutar el handler con timeout
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=MAX_RESPONSE_TIME_SECONDS)
                response_sent = True
                watchdog.mark_response_sent(user_id)
                return result

            except TimeoutError:
                # Timeout - enviar fallback
                logger.error(f"🔴 TIMEOUT | user={user_id} | state={state} | handler={func.__name__}")

                if not response_sent:
                    fallback_msg = EmpathicFallback.get_fallback(lang, "timeout_recovery", state)
                    await send_message(fallback_msg)
                    watchdog.mark_response_sent(user_id)

            except Exception as e:
                # Excepción - loggear y enviar fallback empático
                logger.error(
                    f"🔴 EXCEPTION | user={user_id} | state={state} | handler={func.__name__} | "
                    f"error={type(e).__name__}: {str(e)}"
                )
                logger.debug(f"Traceback:\n{traceback.format_exc()}")

                if not response_sent:
                    fallback_msg = EmpathicFallback.get_fallback(lang, fallback_type, state)
                    await send_message(fallback_msg)
                    watchdog.mark_response_sent(user_id)

            finally:
                # Asegurar que el watchdog se cancele
                watchdog.cancel_watchdog(user_id)

        return wrapper

    return decorator


# ============== RESPONSE TRACKER ==============


class ResponseTracker:
    """
    Rastrea todas las respuestas para garantizar que ningún input quede sin respuesta.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._pending_inputs = {}
            cls._instance._response_times = []
        return cls._instance

    def record_input(self, user_id: int, input_type: str, input_data: str = ""):
        """Registra un input que espera respuesta"""
        self._pending_inputs[user_id] = {
            "timestamp": datetime.now(),
            "type": input_type,
            "data": input_data[:100],  # Truncar para logs
        }
        logger.debug(f"📥 INPUT | user={user_id} | type={input_type}")

    def record_response(self, user_id: int):
        """Registra que se envió respuesta"""
        if user_id in self._pending_inputs:
            input_info = self._pending_inputs[user_id]
            response_time = (datetime.now() - input_info["timestamp"]).total_seconds()

            self._response_times.append(response_time)
            if len(self._response_times) > 1000:
                self._response_times = self._response_times[-1000:]

            del self._pending_inputs[user_id]

            logger.debug(f"📤 RESPONSE | user={user_id} | time={response_time:.2f}s")

    def get_pending_inputs(self) -> dict[int, dict]:
        """Obtiene inputs pendientes de respuesta"""
        return self._pending_inputs.copy()

    def get_average_response_time(self) -> float:
        """Obtiene tiempo promedio de respuesta"""
        if not self._response_times:
            return 0.0
        return sum(self._response_times) / len(self._response_times)

    def check_stale_inputs(self, max_age_seconds: float = 30.0) -> list[int]:
        """Encuentra inputs que llevan demasiado tiempo sin respuesta"""
        stale = []
        now = datetime.now()

        for user_id, input_info in self._pending_inputs.items():
            age = (now - input_info["timestamp"]).total_seconds()
            if age > max_age_seconds:
                stale.append(user_id)

        return stale


# ============== SINGLETON GETTERS ==============


def get_watchdog() -> ResponseWatchdog:
    return ResponseWatchdog()


def get_empathic_fallback() -> EmpathicFallback:
    return EmpathicFallback()


def get_dead_state_detector() -> DeadStateDetector:
    return DeadStateDetector()


def get_response_tracker() -> ResponseTracker:
    return ResponseTracker()


# ============== INTEGRATION HELPER ==============


async def ensure_response(update, context, handler_func: Callable, fallback_type: str = "handler_error"):
    """
    Helper que garantiza respuesta al ejecutar un handler.
    Uso alternativo al decorador para casos específicos.
    """
    user_id = update.effective_user.id if update.effective_user else 0
    lang = "es"
    state = "unknown"

    try:
        from app.services.telegram_bot import get_state, get_user_data

        if user_id:
            user = get_user_data(user_id)
            lang = user.get("language", "es")
            state = get_state(user_id)
    except:
        pass

    tracker = get_response_tracker()
    tracker.record_input(user_id, "handler", handler_func.__name__)

    try:
        result = await handler_func(update, context)
        tracker.record_response(user_id)
        return result

    except Exception as e:
        logger.error(f"🔴 ensure_response | user={user_id} | error={e}")

        # Enviar fallback empático
        fallback_msg = EmpathicFallback.get_fallback(lang, fallback_type, state)

        try:
            if update.message:
                await update.message.reply_text(fallback_msg)
            elif update.callback_query:
                await update.callback_query.message.reply_text(fallback_msg)
        except:
            pass

        tracker.record_response(user_id)
