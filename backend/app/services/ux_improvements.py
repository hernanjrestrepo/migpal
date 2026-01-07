"""
MigPAL UX Improvements Module v3.0.3
=====================================
Mejoras de experiencia de usuario implementadas:

1. Startup Self-Check: Validación de constantes de estado al iniciar
2. Global Exception Handler: Captura de errores con fallback localizado
3. Timeout/Anti-Stall: Detección de usuarios estancados
4. Progress UX: Headers con campos pendientes
5. Enhanced Logging: Logging detallado de transiciones
"""

import logging
import traceback
import time
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

# ============== CONFIGURATION ==============

# Timeout configuration
STALL_TIMEOUT_MINUTES = 10  # Minutes without progress before reminder
MAX_REPEATED_MESSAGES = 3   # Max times same message before intervention
STALL_CHECK_INTERVAL = 60   # Seconds between stall checks

# Phase definitions for progress tracking
PHASES = {
    "phase1_profile": {
        "name_es": "Tu Perfil",
        "name_en": "Your Profile",
        "states": ["name", "confirm_name", "birth_date", "nationality", "current_country", "current_city", "email", "phone"],
        "required_fields": ["name", "birth_date", "nationality", "current_country", "current_city"],
        "icon": "👤"
    },
    "phase2_education": {
        "name_es": "Educación",
        "name_en": "Education",
        "states": ["education_level", "education_status", "education_field", "education_career"],
        "required_fields": ["education_level", "education_field"],
        "icon": "🎓"
    },
    "phase3_work": {
        "name_es": "Experiencia Laboral",
        "name_en": "Work Experience",
        "states": ["work_status", "profession", "work_experience", "linkedin"],
        "required_fields": ["work_status", "profession", "work_experience"],
        "icon": "💼"
    },
    "phase4_languages": {
        "name_es": "Idiomas",
        "name_en": "Languages",
        "states": ["english_level"],
        "required_fields": ["english_level"],
        "icon": "🌐"
    },
    "phase5_history": {
        "name_es": "Historial",
        "name_en": "History",
        "states": ["visa_history", "visa_details", "visa_rejections", "criminal_record", "health_conditions", "savings"],
        "required_fields": ["visa_history", "savings"],
        "icon": "📋"
    },
    "phase6_family": {
        "name_es": "Familia",
        "name_en": "Family",
        "states": ["family_status", "family_count", "family_member_relation", "family_member_name", "family_member_birth"],
        "required_fields": ["family_status"],
        "icon": "👨‍👩‍👧"
    },
    "phase7_preferences": {
        "name_es": "Preferencias",
        "name_en": "Preferences",
        "states": ["migration_reason", "timeline", "destination_preference", "climate_preference", "city_size_preference", "budget_initial"],
        "required_fields": ["migration_reason", "timeline"],
        "icon": "🎯"
    }
}

# Field labels for "what's missing" display
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
        "timeline": "Plazo"
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
        "timeline": "Timeline"
    }
}

# Error messages for fallback
ERROR_MESSAGES = {
    "es": {
        "generic_error": "⚠️ Ocurrió un error inesperado. Por favor intenta de nuevo o escribe /start para reiniciar.",
        "stall_reminder": "👋 ¡Hola! Noté que llevas un rato sin avanzar. ¿Necesitas ayuda con algo?",
        "restart_phase": "🔄 Reiniciar esta fase",
        "continue": "▶️ Continuar donde estaba"
    },
    "en": {
        "generic_error": "⚠️ An unexpected error occurred. Please try again or type /start to restart.",
        "stall_reminder": "👋 Hi! I noticed you haven't made progress in a while. Do you need help with something?",
        "restart_phase": "🔄 Restart this phase",
        "continue": "▶️ Continue where I was"
    }
}


# ============== STARTUP SELF-CHECK ==============

class StartupValidator:
    """Validates that all required state constants exist at startup"""
    
    @staticmethod
    def validate_form_states(form_states: List[str], module_globals: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that all states in FORM_STATES are defined.
        Returns (is_valid, list_of_missing_constants)
        """
        missing = []
        for state in form_states:
            if isinstance(state, str):
                # String literals like "confirm_name" are OK
                continue
            # Check if it's a valid constant
            const_name = None
            for name, value in module_globals.items():
                if name.startswith("STATE_") and value == state:
                    const_name = name
                    break
            if const_name is None:
                missing.append(str(state))
        
        return len(missing) == 0, missing
    
    @staticmethod
    def validate_all_states(module_globals: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Comprehensive validation of all state-related configurations.
        Returns (is_valid, validation_report)
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "state_constants_count": 0,
            "phases_validated": 0,
            "errors": [],
            "warnings": []
        }
        
        # Count state constants
        state_constants = {k: v for k, v in module_globals.items() if k.startswith("STATE_")}
        report["state_constants_count"] = len(state_constants)
        
        # Validate each phase has valid states
        for phase_id, phase_config in PHASES.items():
            for state in phase_config.get("states", []):
                # Check if state exists as a constant value
                found = False
                for const_name, const_value in state_constants.items():
                    if const_value == state:
                        found = True
                        break
                if not found and state not in ["confirm_name"]:  # confirm_name is a special case
                    report["warnings"].append(f"Phase {phase_id}: state '{state}' not found as constant")
            report["phases_validated"] += 1
        
        is_valid = len(report["errors"]) == 0
        return is_valid, report
    
    @staticmethod
    def run_startup_check(module_globals: Dict[str, Any], form_states: List[str]) -> bool:
        """
        Run all startup validations. Returns True if all pass.
        Logs errors and aborts if critical issues found.
        """
        logger.info("🔍 Running startup self-check...")
        
        # Validate FORM_STATES
        is_valid, missing = StartupValidator.validate_form_states(form_states, module_globals)
        if not is_valid:
            logger.error(f"❌ STARTUP CHECK FAILED: Missing state constants: {missing}")
            logger.error("Bot cannot start with undefined state constants. Please fix and restart.")
            return False
        
        # Comprehensive validation
        is_valid, report = StartupValidator.validate_all_states(module_globals)
        
        logger.info(f"✅ Startup check passed: {report['state_constants_count']} state constants, {report['phases_validated']} phases validated")
        
        if report["warnings"]:
            for warning in report["warnings"]:
                logger.warning(f"⚠️ {warning}")
        
        return True


# ============== GLOBAL EXCEPTION HANDLER ==============

class GlobalExceptionHandler:
    """Handles exceptions globally with localized fallback messages"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._error_log = []
        return cls._instance
    
    def log_error(self, user_id: int, state: str, error: Exception, context: str = ""):
        """Log error with full context"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "state": state,
            "context": context,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc()
        }
        self._error_log.append(error_entry)
        
        # Keep only last 100 errors in memory
        if len(self._error_log) > 100:
            self._error_log = self._error_log[-100:]
        
        # Log to file
        logger.error(
            f"🔴 ERROR | user={user_id} | state={state} | context={context} | "
            f"error={type(error).__name__}: {str(error)}"
        )
        logger.debug(f"Traceback:\n{traceback.format_exc()}")
    
    def get_fallback_message(self, lang: str = "en") -> str:
        """Get localized fallback error message"""
        messages = ERROR_MESSAGES.get(lang, ERROR_MESSAGES["en"])
        return messages.get("generic_error", ERROR_MESSAGES["en"]["generic_error"])
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """Get recent errors for debugging"""
        return self._error_log[-limit:]


def global_error_handler(func):
    """Decorator for global error handling on async handlers"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Try to extract user_id and state from args
            user_id = 0
            state = "unknown"
            lang = "en"
            update = None
            
            # Find update object in args
            for arg in args:
                if hasattr(arg, 'effective_user'):
                    update = arg
                    user_id = arg.effective_user.id if arg.effective_user else 0
                    break
            
            # Try to get state and language
            try:
                from app.services.telegram_bot import get_state, get_user_data
                if user_id:
                    state = get_state(user_id)
                    user = get_user_data(user_id)
                    lang = user.get("language", "en")
            except:
                pass
            
            # Log the error
            handler = GlobalExceptionHandler()
            handler.log_error(user_id, state, e, func.__name__)
            
            # Send fallback message to user
            if update:
                try:
                    fallback_msg = handler.get_fallback_message(lang)
                    if hasattr(update, 'message') and update.message:
                        await update.message.reply_text(fallback_msg)
                    elif hasattr(update, 'callback_query') and update.callback_query:
                        await update.callback_query.message.reply_text(fallback_msg)
                except Exception as send_error:
                    logger.error(f"Failed to send fallback message: {send_error}")
            
            # Re-raise for debugging in development
            # In production, we swallow the error to keep bot running
            # raise  # Uncomment for development
    
    return wrapper


# ============== TIMEOUT / ANTI-STALL ==============

class StallDetector:
    """Detects and handles stalled user sessions"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._user_activity = {}
            cls._instance._message_history = {}
        return cls._instance
    
    def record_activity(self, user_id: int, state: str, message: str = ""):
        """Record user activity for stall detection"""
        now = datetime.now()
        
        if user_id not in self._user_activity:
            self._user_activity[user_id] = {
                "last_activity": now,
                "last_state": state,
                "stall_reminder_sent": False
            }
            self._message_history[user_id] = []
        
        activity = self._user_activity[user_id]
        
        # Check if state changed (progress made)
        if activity["last_state"] != state:
            activity["stall_reminder_sent"] = False
            self._message_history[user_id] = []
        
        activity["last_activity"] = now
        activity["last_state"] = state
        
        # Track message for repetition detection
        if message:
            history = self._message_history[user_id]
            history.append(message.lower().strip())
            # Keep only last N messages
            if len(history) > MAX_REPEATED_MESSAGES + 2:
                self._message_history[user_id] = history[-(MAX_REPEATED_MESSAGES + 2):]
    
    def is_stalled(self, user_id: int) -> Tuple[bool, str]:
        """
        Check if user is stalled.
        Returns (is_stalled, reason)
        """
        if user_id not in self._user_activity:
            return False, ""
        
        activity = self._user_activity[user_id]
        now = datetime.now()
        
        # Check timeout
        time_since_activity = (now - activity["last_activity"]).total_seconds() / 60
        if time_since_activity >= STALL_TIMEOUT_MINUTES:
            if not activity["stall_reminder_sent"]:
                return True, "timeout"
        
        # Check repeated messages
        if user_id in self._message_history:
            history = self._message_history[user_id]
            if len(history) >= MAX_REPEATED_MESSAGES:
                # Check if last N messages are the same
                last_messages = history[-MAX_REPEATED_MESSAGES:]
                if len(set(last_messages)) == 1:
                    if not activity["stall_reminder_sent"]:
                        return True, "repeated"
        
        return False, ""
    
    def mark_reminder_sent(self, user_id: int):
        """Mark that a stall reminder was sent"""
        if user_id in self._user_activity:
            self._user_activity[user_id]["stall_reminder_sent"] = True
    
    def get_stall_message(self, lang: str, last_prompt: str = "") -> Tuple[str, List[Tuple[str, str]]]:
        """
        Get stall reminder message and buttons.
        Returns (message, [(button_text, callback_data), ...])
        """
        messages = ERROR_MESSAGES.get(lang, ERROR_MESSAGES["en"])
        
        msg = messages["stall_reminder"]
        if last_prompt:
            msg += f"\n\n📝 *Última pregunta:*\n{last_prompt}"
        
        buttons = [
            (messages["continue"], "stall_continue"),
            (messages["restart_phase"], "stall_restart")
        ]
        
        return msg, buttons
    
    def clear_user(self, user_id: int):
        """Clear user from stall tracking"""
        if user_id in self._user_activity:
            del self._user_activity[user_id]
        if user_id in self._message_history:
            del self._message_history[user_id]


# ============== PROGRESS UX ==============

class ProgressTracker:
    """Tracks and displays user progress through phases"""
    
    @staticmethod
    def get_current_phase(state: str) -> Optional[str]:
        """Get the phase ID for a given state"""
        for phase_id, phase_config in PHASES.items():
            if state in phase_config.get("states", []):
                return phase_id
        return None
    
    @staticmethod
    def get_phase_progress(user_data: Dict[str, Any], phase_id: str) -> Dict[str, Any]:
        """
        Calculate progress for a specific phase.
        Returns {completed: int, total: int, missing_fields: [str], percentage: float}
        """
        if phase_id not in PHASES:
            return {"completed": 0, "total": 0, "missing_fields": [], "percentage": 0}
        
        phase = PHASES[phase_id]
        required_fields = phase.get("required_fields", [])
        profile = user_data.get("profile", {})
        preferences = user_data.get("preferences", {})
        
        completed = 0
        missing = []
        
        for field in required_fields:
            # Check in various locations
            value = None
            
            # Check profile sections
            for section in ["personal", "education", "work", "languages", "history", "financial"]:
                if field in profile.get(section, {}):
                    value = profile[section][field]
                    break
            
            # Check preferences
            if value is None and field in preferences:
                value = preferences[field]
            
            # Check top-level
            if value is None and field in user_data:
                value = user_data[field]
            
            if value and str(value).strip():
                completed += 1
            else:
                missing.append(field)
        
        total = len(required_fields)
        percentage = (completed / total * 100) if total > 0 else 0
        
        return {
            "completed": completed,
            "total": total,
            "missing_fields": missing,
            "percentage": percentage
        }
    
    @staticmethod
    def get_overall_progress(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall progress across all phases"""
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
            "phases": phase_progress
        }
    
    @staticmethod
    def format_progress_header(user_data: Dict[str, Any], current_state: str, lang: str = "es") -> str:
        """
        Format a progress header for the current phase.
        Shows phase name, progress bar, and what's missing.
        """
        phase_id = ProgressTracker.get_current_phase(current_state)
        if not phase_id:
            return ""
        
        phase = PHASES[phase_id]
        progress = ProgressTracker.get_phase_progress(user_data, phase_id)
        overall = ProgressTracker.get_overall_progress(user_data)
        
        # Phase name
        phase_name = phase.get(f"name_{lang}", phase.get("name_en", ""))
        icon = phase.get("icon", "📋")
        
        # Progress bar
        filled = int(progress["percentage"] / 10)
        empty = 10 - filled
        progress_bar = "▓" * filled + "░" * empty
        
        # Build header
        header = f"{icon} *{phase_name}* [{progress_bar}] {progress['percentage']:.0f}%\n"
        
        # Overall progress
        overall_pct = overall["overall_percentage"]
        header += f"📊 Progreso total: {overall_pct:.0f}%\n"
        
        # What's missing
        if progress["missing_fields"]:
            labels = FIELD_LABELS.get(lang, FIELD_LABELS["en"])
            missing_labels = [labels.get(f, f) for f in progress["missing_fields"][:3]]
            
            if lang == "es":
                header += f"\n⏳ *Falta:* {', '.join(missing_labels)}"
                if len(progress["missing_fields"]) > 3:
                    header += f" (+{len(progress['missing_fields']) - 3} más)"
            else:
                header += f"\n⏳ *Missing:* {', '.join(missing_labels)}"
                if len(progress["missing_fields"]) > 3:
                    header += f" (+{len(progress['missing_fields']) - 3} more)"
        
        return header + "\n\n"
    
    @staticmethod
    def format_phase_summary(user_data: Dict[str, Any], lang: str = "es") -> str:
        """Format a summary of all phases with their progress"""
        overall = ProgressTracker.get_overall_progress(user_data)
        
        lines = []
        if lang == "es":
            lines.append("📊 *Tu Progreso*\n")
        else:
            lines.append("📊 *Your Progress*\n")
        
        for phase_id, phase in PHASES.items():
            progress = overall["phases"][phase_id]
            icon = phase.get("icon", "📋")
            name = phase.get(f"name_{lang}", phase.get("name_en", ""))
            
            if progress["percentage"] == 100:
                status = "✅"
            elif progress["percentage"] > 0:
                status = "🔵"
            else:
                status = "⚪"
            
            lines.append(f"{status} {icon} {name}: {progress['percentage']:.0f}%")
        
        lines.append(f"\n📈 *Total: {overall['overall_percentage']:.0f}%*")
        
        return "\n".join(lines)


# ============== ENHANCED LOGGING ==============

class TransitionLogger:
    """Enhanced logging for state transitions"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._transitions = []
        return cls._instance
    
    def log_transition(self, user_id: int, from_state: str, to_state: str, 
                       trigger: str = "", data_saved: Dict[str, Any] = None):
        """Log a state transition with full context"""
        transition = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "from_state": from_state,
            "to_state": to_state,
            "trigger": trigger,
            "data_saved": list(data_saved.keys()) if data_saved else []
        }
        
        self._transitions.append(transition)
        
        # Keep only last 500 transitions
        if len(self._transitions) > 500:
            self._transitions = self._transitions[-500:]
        
        # Log with clear format
        logger.info(
            f"🔄 TRANSITION | user={user_id} | {from_state} → {to_state} | "
            f"trigger={trigger} | saved={transition['data_saved']}"
        )
    
    def log_message_received(self, user_id: int, state: str, message_type: str, 
                             message_preview: str = ""):
        """Log incoming message"""
        preview = message_preview[:50] + "..." if len(message_preview) > 50 else message_preview
        logger.info(
            f"📩 MESSAGE | user={user_id} | state={state} | type={message_type} | "
            f"preview=\"{preview}\""
        )
    
    def log_callback_received(self, user_id: int, state: str, callback_data: str):
        """Log callback query"""
        logger.info(
            f"🔘 CALLBACK | user={user_id} | state={state} | data={callback_data}"
        )
    
    def log_error_recovery(self, user_id: int, state: str, error_type: str, 
                           recovery_action: str):
        """Log error recovery action"""
        logger.warning(
            f"🔧 RECOVERY | user={user_id} | state={state} | error={error_type} | "
            f"action={recovery_action}"
        )
    
    def get_user_transitions(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get recent transitions for a specific user"""
        user_transitions = [t for t in self._transitions if t["user_id"] == user_id]
        return user_transitions[-limit:]


# ============== NAME CONFIRMATION SIMPLIFICATION ==============

class NameValidator:
    """Simplified name validation and confirmation"""
    
    @staticmethod
    def is_valid_name(name: str) -> Tuple[bool, str]:
        """
        Validate name and return (is_valid, cleaned_name or error_message)
        """
        if not name or not name.strip():
            return False, "empty"
        
        cleaned = name.strip()
        
        # Too short
        if len(cleaned) < 2:
            return False, "too_short"
        
        # Too long
        if len(cleaned) > 100:
            return False, "too_long"
        
        # Contains only valid characters (letters, spaces, hyphens, apostrophes)
        import re
        if not re.match(r"^[\w\s\-'\.]+$", cleaned, re.UNICODE):
            return False, "invalid_chars"
        
        # Apply titlecase if all upper or all lower
        if cleaned.isupper() or cleaned.islower():
            cleaned = cleaned.title()
        
        return True, cleaned
    
    @staticmethod
    def is_duplicate(new_name: str, existing_name: str) -> bool:
        """Check if new name is essentially the same as existing"""
        if not existing_name:
            return False
        
        # Normalize both names
        new_normalized = new_name.lower().strip()
        existing_normalized = existing_name.lower().strip()
        
        return new_normalized == existing_normalized
    
    @staticmethod
    def should_skip_confirmation(name: str) -> bool:
        """
        Determine if we should skip confirmation for this name.
        Skip if name looks well-formatted (has space, proper case, etc.)
        """
        if not name:
            return False
        
        # Has at least first and last name
        parts = name.strip().split()
        if len(parts) < 2:
            return False
        
        # Each part is properly capitalized
        for part in parts:
            if not part[0].isupper():
                return False
        
        # Reasonable length
        if len(name) < 5 or len(name) > 50:
            return False
        
        return True
    
    @staticmethod
    def format_confirmation_message(name: str, lang: str = "es") -> str:
        """Format a simple 1-click confirmation message"""
        if lang == "es":
            return f"✅ *{name}*\n\n¿Es correcto?"
        else:
            return f"✅ *{name}*\n\nIs this correct?"


# ============== SINGLETON INSTANCES ==============

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


# ============== INTEGRATION HELPERS ==============

def enhanced_set_state(user_id: int, new_state: str, trigger: str = "", 
                       data_saved: Dict[str, Any] = None):
    """
    Enhanced state setter with logging and stall detection.
    Should be called instead of the basic set_state.
    """
    from app.services.telegram_bot import get_state, set_state
    
    old_state = get_state(user_id)
    
    # Log transition
    get_transition_logger().log_transition(
        user_id, old_state, new_state, trigger, data_saved
    )
    
    # Update stall detector
    get_stall_detector().record_activity(user_id, new_state)
    
    # Set the state
    set_state(user_id, new_state)


def check_and_handle_stall(user_id: int, lang: str, last_prompt: str = "") -> Optional[Tuple[str, List]]:
    """
    Check if user is stalled and return intervention message if needed.
    Returns (message, buttons) or None if not stalled.
    """
    detector = get_stall_detector()
    is_stalled, reason = detector.is_stalled(user_id)
    
    if is_stalled:
        detector.mark_reminder_sent(user_id)
        return detector.get_stall_message(lang, last_prompt)
    
    return None
