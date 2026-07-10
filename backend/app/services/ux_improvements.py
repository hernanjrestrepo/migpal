"""
MigPAL UX Improvements Module v3.1.0
=====================================
Mejoras de experiencia de usuario implementadas:

1. Startup Self-Check: Validación de constantes de estado al iniciar
2. Global Exception Handler: Captura de errores con fallback localizado
3. Timeout/Anti-Stall: Detección de usuarios estancados
4. Progress UX: Headers con campos pendientes
5. Enhanced Logging: Logging detallado de transiciones
6. V3.1.0 - HARDENED NameValidator: Validación estricta de nombres
"""

import logging
import traceback
from datetime import datetime
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)

# ============== CONFIGURATION ==============

STALL_TIMEOUT_MINUTES = 10
MAX_REPEATED_MESSAGES = 3
STALL_CHECK_INTERVAL = 60

PHASES = {
    "phase1_profile": {
        "name_es": "Tu Perfil",
        "name_en": "Your Profile",
        "states": [
            "name",
            "confirm_name",
            "birth_date",
            "nationality",
            "current_country",
            "current_city",
            "email",
            "phone",
        ],
        "required_fields": ["name", "birth_date", "nationality", "current_country", "current_city"],
        "icon": "👤",
    },
    "phase2_education": {
        "name_es": "Educación",
        "name_en": "Education",
        "states": ["education_level", "education_status", "education_field", "education_career"],
        "required_fields": ["education_level", "education_field"],
        "icon": "🎓",
    },
    "phase3_work": {
        "name_es": "Experiencia Laboral",
        "name_en": "Work Experience",
        "states": ["work_status", "profession", "work_experience", "linkedin"],
        "required_fields": ["work_status", "profession", "work_experience"],
        "icon": "💼",
    },
    "phase4_languages": {
        "name_es": "Idiomas",
        "name_en": "Languages",
        "states": ["english_level"],
        "required_fields": ["english_level"],
        "icon": "🌐",
    },
    "phase5_history": {
        "name_es": "Historial",
        "name_en": "History",
        "states": [
            "visa_history",
            "visa_details",
            "visa_rejections",
            "criminal_record",
            "health_conditions",
            "savings",
        ],
        "required_fields": ["visa_history", "savings"],
        "icon": "📋",
    },
    "phase6_family": {
        "name_es": "Familia",
        "name_en": "Family",
        "states": [
            "family_status",
            "family_count",
            "family_member_relation",
            "family_member_name",
            "family_member_birth",
        ],
        "required_fields": ["family_status"],
        "icon": "👨‍👩‍👧",
    },
    "phase7_preferences": {
        "name_es": "Preferencias",
        "name_en": "Preferences",
        "states": [
            "migration_reason",
            "timeline",
            "destination_preference",
            "climate_preference",
            "city_size_preference",
            "budget_initial",
        ],
        "required_fields": ["migration_reason", "timeline"],
        "icon": "🎯",
    },
}

FIELD_LABELS = {
    "es": {
        "name": "Nombre",
        "birth_date": "Fecha de nacimiento",
        "nationality": "Nacionalidad",
        "current_country": "País actual",
        "current_city": "Ciudad actual",
        "email": "Correo electrónico",
        "phone": "Teléfono",
        "education_level": "Nivel educativo",
        "education_field": "Área de estudio",
        "education_career": "Carrera",
        "work_status": "Situación laboral",
        "profession": "Profesión",
        "work_experience": "Experiencia",
        "english_level": "Nivel de inglés",
        "linkedin": "LinkedIn",
        "visa_history": "Historial de visas",
        "savings": "Ahorros",
        "family_status": "Estado familiar",
        "migration_reason": "Razón de migración",
        "timeline": "Plazo",
    },
    "en": {
        "name": "Name",
        "birth_date": "Birth date",
        "nationality": "Nationality",
        "current_country": "Current country",
        "current_city": "Current city",
        "email": "Email",
        "phone": "Phone",
        "education_level": "Education level",
        "education_field": "Field of study",
        "education_career": "Career",
        "work_status": "Work status",
        "profession": "Profession",
        "work_experience": "Experience",
        "english_level": "English level",
        "linkedin": "LinkedIn",
        "visa_history": "Visa history",
        "savings": "Savings",
        "family_status": "Family status",
        "migration_reason": "Migration reason",
        "timeline": "Timeline",
    },
}

ERROR_MESSAGES = {
    "es": {
        "generic_error": "⚠️ Ocurrió un error inesperado. Por favor intenta de nuevo o escribe /start para reiniciar.",
        "stall_reminder": "👋 ¡Hola! Noté que llevas un rato sin avanzar. ¿Necesitas ayuda con algo?",
        "restart_phase": "🔄 Reiniciar esta fase",
        "continue": "▶️ Continuar donde estaba",
    },
    "en": {
        "generic_error": "⚠️ An unexpected error occurred. Please try again or type /start to restart.",
        "stall_reminder": "👋 Hi! I noticed you haven't made progress in a while. Do you need help with something?",
        "restart_phase": "🔄 Restart this phase",
        "continue": "▶️ Continue where I was",
    },
}


# ============== STARTUP SELF-CHECK ==============


class StartupValidator:
    """Validates that all required state constants exist at startup"""

    @staticmethod
    def validate_form_states(
        form_states: list[str], module_globals: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        missing = []
        for state in form_states:
            if isinstance(state, str):
                continue
            const_name = None
            for name, value in module_globals.items():
                if name.startswith("STATE_") and value == state:
                    const_name = name
                    break
            if const_name is None:
                missing.append(str(state))
        return len(missing) == 0, missing

    @staticmethod
    def validate_all_states(module_globals: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        report = {
            "timestamp": datetime.now().isoformat(),
            "state_constants_count": 0,
            "phases_validated": 0,
            "errors": [],
            "warnings": [],
        }
        state_constants = {k: v for k, v in module_globals.items() if k.startswith("STATE_")}
        report["state_constants_count"] = len(state_constants)

        for phase_id, phase_config in PHASES.items():
            for state in phase_config.get("states", []):
                found = False
                for _const_name, const_value in state_constants.items():
                    if const_value == state:
                        found = True
                        break
                if not found and state not in ["confirm_name"]:
                    report["warnings"].append(f"Phase {phase_id}: state '{state}' not found as constant")
            report["phases_validated"] += 1

        is_valid = len(report["errors"]) == 0
        return is_valid, report

    @staticmethod
    def run_startup_check(module_globals: dict[str, Any], form_states: list[str]) -> bool:
        logger.info("🔍 Running startup self-check...")
        is_valid, missing = StartupValidator.validate_form_states(form_states, module_globals)
        if not is_valid:
            logger.error(f"❌ STARTUP CHECK FAILED: Missing state constants: {missing}")
            return False
        is_valid, report = StartupValidator.validate_all_states(module_globals)
        logger.info(f"✅ Startup check passed: {report['state_constants_count']} state constants")
        return True


# ============== GLOBAL EXCEPTION HANDLER ==============


class GlobalExceptionHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._error_log = []
        return cls._instance

    def log_error(self, user_id: int, state: str, error: Exception, context: str = ""):
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "state": state,
            "context": context,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
        }
        self._error_log.append(error_entry)
        if len(self._error_log) > 100:
            self._error_log = self._error_log[-100:]
        logger.error(
            f"🔴 ERROR | user={user_id} | state={state} | error={type(error).__name__}: {str(error)}"
        )

    def get_fallback_message(self, lang: str = "en") -> str:
        messages = ERROR_MESSAGES.get(lang, ERROR_MESSAGES["en"])
        return messages.get("generic_error", ERROR_MESSAGES["en"]["generic_error"])

    def get_recent_errors(self, limit: int = 10) -> list[dict]:
        return self._error_log[-limit:]


def global_error_handler(func):
    """Decorator for global error handling with recovery to /start.

    V4.1 FIX: Improved error handling with:
    - Full traceback logging
    - State validation before use
    - Recovery to /start without duplicating messages
    - Safe defaults for all user data

    V4.2 FIX (PRODUCTION BUG): Short-circuit post-error:
    - Cancel watchdog immediately to prevent "⏳ Sigo aquí…" messages
    - Mark response as sent to prevent duplicate messages
    - Return early after sending recovery message
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            user_id = 0
            state = "unknown"
            lang = "es"
            update = None
            error_type = type(e).__name__

            # Extract update object from args
            for arg in args:
                if hasattr(arg, "effective_user"):
                    update = arg
                    user_id = arg.effective_user.id if arg.effective_user else 0
                    break

            # V4.2 FIX: IMMEDIATELY cancel watchdog to prevent "Sigo aquí" messages
            # This MUST happen before any other processing
            if user_id:
                try:
                    from app.services.availability_watchdog import get_response_tracker, get_watchdog

                    watchdog = get_watchdog()
                    watchdog.cancel_watchdog(user_id)
                    watchdog.mark_response_sent(user_id)

                    # Also mark response in tracker to prevent any follow-up messages
                    response_tracker = get_response_tracker()
                    response_tracker.record_response(user_id)

                    logger.info(f"🛑 ERROR_SHORT_CIRCUIT | user={user_id} | watchdog cancelled")
                except Exception as watchdog_err:
                    logger.warning(f"🔧 WATCHDOG_CANCEL_FAILED | user={user_id} | error={watchdog_err}")

            # Safely get state and user data with defensive checks
            try:
                from app.services.telegram_bot import STATE_START, get_state, get_user_data, set_state

                if user_id:
                    # Defensive state retrieval
                    try:
                        state = get_state(user_id)
                        if state is None or not isinstance(state, str):
                            state = STATE_START
                            logger.warning(
                                f"🔧 RECOVERY | user={user_id} | null/invalid state, resetting to START"
                            )
                    except Exception as state_err:
                        state = STATE_START
                        logger.warning(f"🔧 RECOVERY | user={user_id} | state retrieval failed: {state_err}")

                    # Defensive user data retrieval
                    try:
                        user = get_user_data(user_id)
                        if user and isinstance(user, dict):
                            lang = user.get("language", "es") or "es"
                        else:
                            lang = "es"
                    except Exception as user_err:
                        lang = "es"
                        logger.warning(
                            f"🔧 RECOVERY | user={user_id} | user data retrieval failed: {user_err}"
                        )
            except ImportError:
                pass

            # Log the error with full traceback
            handler = GlobalExceptionHandler()
            handler.log_error(user_id, state, e, func.__name__)

            # Log additional context for debugging
            logger.error(
                f"🔴 EXCEPTION | func={func.__name__} | user={user_id} | state={state} | "
                f"type={error_type} | msg={str(e)[:200]}"
            )

            # Send recovery message to user (without duplicating)
            if update:
                try:
                    # Get localized error message
                    fallback_msg = handler.get_fallback_message(lang)

                    # Determine if we should offer /start recovery
                    # Only offer recovery for certain error types that indicate corrupted state
                    should_offer_recovery = error_type in [
                        "KeyError",
                        "TypeError",
                        "AttributeError",
                        "ValueError",
                        "IndexError",
                        "NoneType",
                    ]

                    if should_offer_recovery:
                        recovery_hint = (
                            "\n\n💡 Si el problema persiste, escribe /start para reiniciar."
                            if lang == "es"
                            else "\n\n💡 If the problem persists, type /start to restart."
                        )
                        fallback_msg += recovery_hint

                    # Send message based on update type
                    message_sent = False
                    if hasattr(update, "message") and update.message:
                        await update.message.reply_text(fallback_msg)
                        message_sent = True
                    elif hasattr(update, "callback_query") and update.callback_query:
                        try:
                            await update.callback_query.message.reply_text(fallback_msg)
                            message_sent = True
                        except Exception:
                            # Callback query message might be too old
                            pass

                    if message_sent:
                        logger.info(f"✅ RECOVERY_MSG_SENT | user={user_id} | func={func.__name__}")
                except Exception as send_err:
                    logger.error(f"❌ RECOVERY_MSG_FAILED | user={user_id} | error={send_err}")

            # V4.2 FIX: Return early to prevent any further processing
            # This ensures the handler execution stops completely after error
            return None

    return wrapper


# ============== STALL DETECTOR ==============


class StallDetector:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._user_activity = {}
            cls._instance._message_history = {}
        return cls._instance

    def record_activity(self, user_id: int, state: str, message: str = ""):
        now = datetime.now()
        if user_id not in self._user_activity:
            self._user_activity[user_id] = {
                "last_activity": now,
                "last_state": state,
                "stall_reminder_sent": False,
            }
            self._message_history[user_id] = []

        activity = self._user_activity[user_id]
        if activity["last_state"] != state:
            activity["stall_reminder_sent"] = False
            self._message_history[user_id] = []

        activity["last_activity"] = now
        activity["last_state"] = state

        if message:
            history = self._message_history[user_id]
            history.append(message.lower().strip())
            if len(history) > MAX_REPEATED_MESSAGES + 2:
                self._message_history[user_id] = history[-(MAX_REPEATED_MESSAGES + 2) :]

    def is_stalled(self, user_id: int) -> tuple[bool, str]:
        if user_id not in self._user_activity:
            return False, ""

        activity = self._user_activity[user_id]
        now = datetime.now()
        time_since_activity = (now - activity["last_activity"]).total_seconds() / 60

        if time_since_activity >= STALL_TIMEOUT_MINUTES:
            if not activity["stall_reminder_sent"]:
                return True, "timeout"

        if user_id in self._message_history:
            history = self._message_history[user_id]
            if len(history) >= MAX_REPEATED_MESSAGES:
                last_messages = history[-MAX_REPEATED_MESSAGES:]
                if len(set(last_messages)) == 1:
                    if not activity["stall_reminder_sent"]:
                        return True, "repeated"

        return False, ""

    def mark_reminder_sent(self, user_id: int):
        if user_id in self._user_activity:
            self._user_activity[user_id]["stall_reminder_sent"] = True

    def get_stall_message(self, lang: str, last_prompt: str = "") -> tuple[str, list[tuple[str, str]]]:
        messages = ERROR_MESSAGES.get(lang, ERROR_MESSAGES["en"])
        msg = messages["stall_reminder"]
        if last_prompt:
            msg += f"\n\n📝 *Última pregunta:*\n{last_prompt}"
        buttons = [(messages["continue"], "stall_continue"), (messages["restart_phase"], "stall_restart")]
        return msg, buttons

    def clear_user(self, user_id: int):
        if user_id in self._user_activity:
            del self._user_activity[user_id]
        if user_id in self._message_history:
            del self._message_history[user_id]


# ============== PROGRESS TRACKER ==============


class ProgressTracker:
    @staticmethod
    def get_current_phase(state: str) -> str | None:
        for phase_id, phase_config in PHASES.items():
            if state in phase_config.get("states", []):
                return phase_id
        return None

    @staticmethod
    def get_phase_progress(user_data: dict[str, Any], phase_id: str) -> dict[str, Any]:
        if phase_id not in PHASES:
            return {"completed": 0, "total": 0, "missing_fields": [], "percentage": 0}

        phase = PHASES[phase_id]
        required_fields = phase.get("required_fields", [])
        profile = user_data.get("profile", {})
        preferences = user_data.get("preferences", {})

        completed = 0
        missing = []

        for field in required_fields:
            value = None
            for section in ["personal", "education", "work", "languages", "history", "financial"]:
                if field in profile.get(section, {}):
                    value = profile[section][field]
                    break
            if value is None and field in preferences:
                value = preferences[field]
            if value is None and field in user_data:
                value = user_data[field]

            if value and str(value).strip():
                completed += 1
            else:
                missing.append(field)

        total = len(required_fields)
        percentage = (completed / total * 100) if total > 0 else 0
        return {"completed": completed, "total": total, "missing_fields": missing, "percentage": percentage}

    @staticmethod
    def get_overall_progress(user_data: dict[str, Any]) -> dict[str, Any]:
        total_completed = 0
        total_required = 0
        phase_progress = {}

        for phase_id in PHASES:
            progress = ProgressTracker.get_phase_progress(user_data, phase_id)
            phase_progress[phase_id] = progress
            total_completed += progress["completed"]
            total_required += progress["total"]

        overall_percentage = (total_completed / total_required * 100) if total_required > 0 else 0
        return {
            "overall_percentage": overall_percentage,
            "total_completed": total_completed,
            "total_required": total_required,
            "phases": phase_progress,
        }

    @staticmethod
    def format_progress_header(user_data: dict[str, Any], current_state: str, lang: str = "es") -> str:
        phase_id = ProgressTracker.get_current_phase(current_state)
        if not phase_id:
            return ""

        phase = PHASES[phase_id]
        progress = ProgressTracker.get_phase_progress(user_data, phase_id)
        overall = ProgressTracker.get_overall_progress(user_data)

        phase_name = phase.get(f"name_{lang}", phase.get("name_en", ""))
        icon = phase.get("icon", "📋")

        filled = int(progress["percentage"] / 10)
        empty = 10 - filled
        progress_bar = "▓" * filled + "░" * empty

        header = f"{icon} *{phase_name}* [{progress_bar}] {progress['percentage']:.0f}%\n"
        header += f"📊 Progreso total: {overall['overall_percentage']:.0f}%\n"

        if progress["missing_fields"]:
            labels = FIELD_LABELS.get(lang, FIELD_LABELS["en"])
            missing_labels = [labels.get(f, f) for f in progress["missing_fields"][:3]]
            if lang == "es":
                header += f"\n⏳ *Falta:* {', '.join(missing_labels)}"
            else:
                header += f"\n⏳ *Missing:* {', '.join(missing_labels)}"

        return header + "\n\n"


# ============== TRANSITION LOGGER ==============


class TransitionLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._transitions = []
        return cls._instance

    def log_transition(
        self,
        user_id: int,
        from_state: str,
        to_state: str,
        trigger: str = "",
        data_saved: dict[str, Any] = None,
    ):
        transition = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "from_state": from_state,
            "to_state": to_state,
            "trigger": trigger,
            "data_saved": list(data_saved.keys()) if data_saved else [],
        }
        self._transitions.append(transition)
        if len(self._transitions) > 500:
            self._transitions = self._transitions[-500:]
        logger.info(f"🔄 TRANSITION | user={user_id} | {from_state} → {to_state}")

    def get_user_transitions(self, user_id: int, limit: int = 20) -> list[dict]:
        user_transitions = [t for t in self._transitions if t["user_id"] == user_id]
        return user_transitions[-limit:]

    def log_message_received(self, user_id: int, state: str, msg_type: str, content: str):
        """Log incoming message for debugging/analytics"""
        logger.debug(f"📩 MSG_RECV | user={user_id} | state={state} | type={msg_type} | len={len(content)}")

    def log_callback_received(self, user_id: int, state: str, callback_data: str):
        """Log incoming callback for debugging/analytics"""
        logger.debug(f"🔘 CALLBACK_RECV | user={user_id} | state={state} | data={callback_data}")


# ============== NAME VALIDATOR (V3.2.0 ULTRA-HARDENED) ==============
# Importar desde el nuevo módulo V3.2.0
from app.services.name_validator_v32 import (
    NameValidatorV32,
)

# Alias para compatibilidad hacia atrás - hereda todo de NameValidatorV32
NameValidator = NameValidatorV32


# ============== RESPONSE ROTATOR ==============


class ResponseRotator:
    """Response rotation with memory per user_id to prevent loops"""

    _instance = None
    ROTATION_MEMORY = 3

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._user_history = {}
        return cls._instance

    def record_response(self, user_id: int, template_id: str):
        if user_id not in self._user_history:
            self._user_history[user_id] = []
        history = self._user_history[user_id]
        history.append(template_id)
        if len(history) > self.ROTATION_MEMORY + 2:
            self._user_history[user_id] = history[-(self.ROTATION_MEMORY + 2) :]

    def get_recent_templates(self, user_id: int) -> list[str]:
        if user_id not in self._user_history:
            return []
        return self._user_history[user_id][-self.ROTATION_MEMORY :]

    def should_avoid_template(self, user_id: int, template_id: str) -> bool:
        recent = self.get_recent_templates(user_id)
        return template_id in recent

    def select_template(
        self, user_id: int, templates: list[tuple[str, str]], default_idx: int = 0
    ) -> tuple[str, str]:
        if not templates:
            return ("default", "")
        recent = self.get_recent_templates(user_id)
        for template_id, template_text in templates:
            if template_id not in recent:
                self.record_response(user_id, template_id)
                return (template_id, template_text)
        template_id, template_text = templates[default_idx % len(templates)]
        self.record_response(user_id, template_id)
        return (template_id, template_text)

    def clear_user(self, user_id: int):
        if user_id in self._user_history:
            del self._user_history[user_id]


# ============== SINGLETON GETTERS ==============


def get_exception_handler() -> GlobalExceptionHandler:
    return GlobalExceptionHandler()


def get_stall_detector() -> StallDetector:
    return StallDetector()


def get_progress_tracker() -> ProgressTracker:
    return ProgressTracker()


def get_transition_logger() -> TransitionLogger:
    return TransitionLogger()


def get_startup_validator() -> StartupValidator:
    return StartupValidator()


def get_response_rotator() -> ResponseRotator:
    return ResponseRotator()


# ============== INTEGRATION HELPERS ==============


def enhanced_set_state(user_id: int, new_state: str, trigger: str = "", data_saved: dict[str, Any] = None):
    from app.services.telegram_bot import get_state, set_state

    old_state = get_state(user_id)
    get_transition_logger().log_transition(user_id, old_state, new_state, trigger, data_saved)
    get_stall_detector().record_activity(user_id, new_state)
    set_state(user_id, new_state)


def check_and_handle_stall(user_id: int, lang: str, last_prompt: str = "") -> tuple[str, list] | None:
    detector = get_stall_detector()
    is_stalled, reason = detector.is_stalled(user_id)
    if is_stalled:
        detector.mark_reminder_sent(user_id)
        return detector.get_stall_message(lang, last_prompt)
    return None
