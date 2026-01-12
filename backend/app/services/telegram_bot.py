"""
MigPAL Telegram Bot Service - GLOBAL
Bot GLOBAL para migrantes de TODO EL MUNDO
https://t.me/MigPAL_Bot

Características Completas:
- Soporte para 25+ idiomas
- Cobertura global de países destino (25+)
- Cobertura global de nacionalidades (100+)
- Perfilamiento en 7 fases
- OCR para documentos (qwen3-vl)
- Score de probabilidad de éxito
- Calculadora de costos inteligente
- Sistema de emergencias /sos
- Comunidad de migrantes
- Persistencia de datos con encriptación
- Checklist inteligente de documentos
- Tracking de aplicación en tiempo real
- Mensajes motivacionales
- Sistema de mentores verificados
- Directorio de abogados
- Bolsa de trabajo con visa sponsorship
- Guía de establecimiento por país
- Generación de reportes PDF
- Rate limiting y seguridad
- Hot-reload para desarrollo
- Backup automático
- Sistema de notificaciones
"""

import os
import re
import asyncio
import logging
import json
import httpx
from typing import Dict, Optional, Any, List
from datetime import datetime
from pathlib import Path

# Load .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# Set default AI config
if not os.getenv("AI_PROVIDER"):
    os.environ["AI_PROVIDER"] = "ollama"
    os.environ["AI_MODEL"] = "migpal:latest"
    os.environ["OLLAMA_URL"] = "http://127.0.0.1:11434"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# SECURITY: Token MUST be set in .env - no hardcoded fallback
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
if not TELEGRAM_BOT_TOKEN:
    logger.error("❌ CRITICAL: TELEGRAM_BOT_TOKEN not set in .env!")
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

# ============== DATA STORAGE ==============
from app.services.case_storage import (
    save_user_data, load_user_data, save_conversation,
    load_conversations, save_document_info, load_documents,
    get_user_summary, delete_user_data
)

# Import advanced features
from app.services.migpal_features import (
    get_motivational_message, MOTIVATIONAL_MESSAGES,
    get_document_checklist, check_document_status, DOCUMENT_CHECKLISTS,
    get_application_stages, calculate_timeline, APPLICATION_STAGES,
    get_mentors, MENTORS,
    get_lawyers, LAWYERS,
    get_jobs, JOBS,
    get_settlement_guide, SETTLEMENT_GUIDES,
    generate_case_report
)

# Import global translations
from app.services.translations import (
    get_text, get_all_languages, detect_language_from_country,
    get_nationalities, get_destination_countries,
    SUPPORTED_LANGUAGES, TRANSLATIONS
)

# Import security module
from app.services.security import (
    check_rate_limit, safe_async_handler, sanitize_input,
    validate_email, validate_phone, validate_date, validate_name,
    encrypt_user_data, decrypt_user_data, log_user_action,
    mask_sensitive_data
)

# Import notification scheduler
from app.services.notification_scheduler import (
    get_scheduler, set_scheduler_callback, start_scheduler, stop_scheduler,
    get_notification_types, get_default_notification_prefs,
    NOTIFICATION_TYPES
)

# Import UI helpers
from app.services.ui_helpers import (
    should_process_click, reset_click_tracking,
    init_multi_select, toggle_selection, get_selections, clear_multi_select,
    get_multi_select_field, build_multi_select_keyboard,
    get_form_header, show_thinking, ThinkingIndicator,
    create_progress_bar, create_step_indicator, FORM_HEADERS
)

# Import gamification system
from app.services.gamification import (
    get_game_engine, Level, LEVEL_INFO, PRICES as GAME_PRICES,
    DELIVERABLES, NON_REFUNDABLE_REASONS, get_prices_summary
)

# Import payment system
from app.services.payments import (
    get_payment_manager, PaymentType, PaymentMethod, PaymentStatus,
    PRICES as PAY_PRICES, get_payment_options_keyboard, get_payment_summary
)

# Import migration planner
from app.services.migration_planner import (
    PREFERENCE_OPTIONS, CITIES_DATABASE, DEFAULT_WEIGHTS,
    calculate_city_score, get_top_cities, get_city_comparison,
    generate_migration_plan, get_next_plan_question, get_question_keyboard,
    MIGRATION_PLAN_QUESTIONS, MAX_CITIES_TO_SHOW,
    filter_cities_by_size, get_city_details
)

# Import deep consulting engine
from app.services.deep_consulting import (
    get_consulting_engine, ConsultingPhase, ConsultingState,
    CONSULTING_PRICES, DEEP_PROFILING_QUESTIONS,
    format_property_list, format_job_list, format_school_list, format_business_list
)

# Import research engine
from app.services.research_engine import (
    get_research_engine, ClientProfile,
    PropertyListing, JobListing, SchoolInfo, BusinessListing, CommunityInfo,
    get_deep_profiling_question, get_next_deep_question
)

# Import conversation flow engine
from app.services.conversation_flow import (
    flow_engine, ConversationState, ConversationContext,
    STATE_QUESTIONS, ScoringWeights
)

# Import scoring engine
from app.services.scoring_engine import (
    scoring_engine, ScoringEngine, ScoredItem,
    LOCATION_PARAMETERS, HOUSING_PARAMETERS, JOB_PARAMETERS,
    get_parameters_for_category, format_score_explanation
)

# Import job search
from app.services.job_search import (
    JobSearchEngine, JobListing,
    search_jobs_for_user, search_jobs_by_industry,
    format_jobs_for_telegram, get_api_status
)

# V2.1 - Import intent detector for invisible commands
from app.services.intent_detector import (
    intent_detector, detect_intent, get_action_from_message,
    Intent, DetectedIntent
)

# V2.1 - Import expanded cities database (1000+ cities)
from app.services.knowledge_base.cities_top_1000 import (
    CITIES_TOP_1000, get_city, get_cities_by_state,
    search_cities, get_top_cities as get_top_1000_cities
)

# V2.1 - Import education search
from app.services.education_search import (
    education_engine, search_schools, search_universities,
    get_university, SchoolType, SchoolCategory
)

# V2.1 - Import city comparator and visual helpers
from app.services.city_comparator import (
    city_comparator, city_formatter, compare_cities,
    format_city_full, format_city_card,
    progress_bar, score_bar, star_rating, format_money, format_population,
    get_city_image_url
)

# V3.0.3 - Import UX improvements module
from app.services.ux_improvements import (
    StartupValidator, GlobalExceptionHandler, StallDetector,
    ProgressTracker, TransitionLogger, NameValidator,
    get_exception_handler, get_stall_detector, get_progress_tracker,
    get_transition_logger, get_startup_validator,
    global_error_handler, enhanced_set_state, check_and_handle_stall,
    PHASES, FIELD_LABELS, ERROR_MESSAGES
)

# SEGMENTO 1/3 - Availability Watchdog: GARANTIZA que MigPAL SIEMPRE responda
from app.services.availability_watchdog import (
    ResponseWatchdog, EmpathicFallback, DeadStateDetector, ResponseTracker,
    get_watchdog, get_empathic_fallback, get_dead_state_detector, get_response_tracker,
    guaranteed_response, ensure_response,
    EMPATHIC_FALLBACKS, STATE_TO_PHASE,
    WATCHDOG_TIMEOUT_SECONDS, MAX_RESPONSE_TIME_SECONDS
)

# SEGMENTO 2/3 - Flow Governor: La conversación manda, no los formularios
from app.services.flow_governor import (
    FormThrottler, InputInterpreter, UnderstandingGatekeeper, 
    VisaRecommendationGuard, ConversationDirector,
    get_form_throttler, get_input_interpreter, get_understanding_gatekeeper,
    get_visa_guard, get_conversation_director,
    should_show_form, interpret_user_input, can_recommend_visa, get_next_visa_question,
    InputType, InterpretedInput, UnderstandingLevel
)

# SEGMENTO 3/3 - Memory Profiler: Extracción ≠ decisión
from app.services.memory_profiler import (
    DataMemory, ProfileValidator, UnderstandingSummarizer,
    CorrectionTracker, LifeGoalExtractor, DecisionGate,
    get_data_memory, get_profile_validator, get_understanding_summarizer,
    get_correction_tracker, get_life_goal_extractor, get_decision_gate,
    store_user_input, validate_profile, generate_understanding_summary,
    detect_correction, can_make_decision, get_next_life_question,
    ProfileCompleteness, ProfileValidationResult,
    is_profile_min_complete  # V4.2 FIX: Guard clause for transitions
)

# SEGMENTO 2/4 - NeverSilent: El bot NUNCA se queda callado
from app.services.never_silent import (
    NeverSilentWrapper, ProcessingWatchdog, AntiMultipleInstances, HealthCheck,
    get_never_silent, get_watchdog as get_processing_watchdog,
    get_anti_multi, get_health_check,
    never_silent, never_silent_callback, with_watchdog,
    full_protection, full_protection_callback,
    WATCHDOG_TIMEOUT
)

# V5.0 - Onboarding Conversacional: Escuchar primero, preguntar después
from app.services.conversational_onboarding import (
    get_conversational_engine, process_conversational_message,
    get_conversational_welcome, is_profile_sufficient
)

# V2.2 - Import housing scraper (Zillow, Apartments.com)
from app.services.housing_scraper import (
    housing_scraper, search_rentals, HousingListing
)

# V2.2 - Import visual generator (images, charts)
from app.services.visual_generator import (
    get_city_image_url as get_real_city_image,
    download_image, chart_generator,
    generate_comparison_chart, generate_radar_chart
)

# V2.2 - Import PDF report generator
from app.services.pdf_report_generator import (
    pdf_generator, generate_diagnostic_pdf, generate_city_pdf,
    generate_comparison_pdf, generate_migration_plan_pdf
)

# V3.1.0 - Import Understanding Summary: Resumen de Entendimiento antes de recomendar visa
from app.services.understanding_summary import (
    get_summary_manager, UnderstandingSummaryManager, ConfirmationStatus,
    can_recommend_visa as can_recommend_visa_with_summary,
    generate_understanding_summary as generate_summary_text,
    mark_summary_confirmed, mark_summary_shown, should_show_summary,
    get_visa_blocking_message
)

# V3.2.0 - Import Profile Validator: Prohibido "basado en tu perfil" sin confirmación
from app.services.profile_validator import (
    get_profile_validator, get_profile_based_intro, is_profile_confirmed,
    PriorityIntentHandler, get_priority_intent_handler
)

# V3.2.1 - Conversation Recorder: Instrumentación y auditoría
from app.services.conversation_recorder import (
    ConversationRecorder, FrictionDetector, FrictionTag,
    get_conversation_recorder, get_friction_detector,
    export_case, export_day
)

# V4.0 - MigPAL USA Standard Middleware
# Feature flag: MIGPAL_USA_STANDARD_V4=1 (default enabled)
from app.services.migpal_v4_middleware import (
    MIGPAL_USA_STANDARD_V4, is_v4_enabled,
    pre_process_message as v4_pre_process,
    post_process_response as v4_post_process,
    check_visa_gating as v4_check_gating,
    get_progress_indicator as v4_get_progress,
    evaluate_states as v4_evaluate_states,
    evaluate_cities as v4_evaluate_cities,
    evaluate_businesses as v4_evaluate_businesses,
    mark_profile_complete as v4_mark_profile_complete,
    mark_summary_confirmed as v4_mark_summary_confirmed,
    advance_phase as v4_advance_phase,
    get_document_checklist as v4_get_doc_checklist,
    get_installation_checklist as v4_get_install_checklist,
    get_interview_prep as v4_get_interview_prep,
    should_add_micro_check as v4_should_micro_check,
    get_micro_check as v4_get_micro_check,
    V4ResponseFormatter, V4GatingEnforcer
)

# In-memory cache (loaded from disk)
user_data: Dict[int, Dict[str, Any]] = {}

# V4.2.1 FIX: Cache de respuestas comunes para reducir llamadas a IA
CACHED_RESPONSES = {
    "confusion_es": "Entiendo que puede ser confuso. 💭 Déjame aclararte...\n\n💭 ¿Qué parte te genera más dudas? Cuéntame y te ayudo a entenderlo mejor.",
    "confusion_en": "I understand it can be confusing. 💭 Let me clarify...\n\n💭 What part confuses you the most? Tell me and I'll help you understand better.",
    "greeting_es": "¡Hola! 👋\n\nSoy MigPAL, tu consultor de migración. 🌍\n\nVoy a guiarte paso a paso en tu proceso de migración.",
    "greeting_en": "Hello! 👋\n\nI'm MigPAL, your migration consultant. 🌍\n\nI'll guide you step by step through your migration process.",
}

# V4.2.1 FIX: Tracker para evitar animaciones duplicadas por usuario
_animation_tracker: Dict[int, float] = {}  # user_id -> last_animation_timestamp
ANIMATION_COOLDOWN = 5.0  # Segundos mínimos entre animaciones

# ============== CONVERSATION STATES ==============
STATE_START = "start"
STATE_NAME = "name"
STATE_BIRTH_DATE = "birth_date"
STATE_NATIONALITY = "nationality"
STATE_CURRENT_COUNTRY = "current_country"
STATE_CURRENT_CITY = "current_city"
STATE_PHONE = "phone"
STATE_EMAIL = "email"
STATE_EDUCATION_LEVEL = "education_level"
STATE_EDUCATION_STATUS = "education_status"
STATE_EDUCATION_FIELD = "education_field"
STATE_EDUCATION_CAREER = "education_career"
STATE_PROFESSION = "profession"
STATE_WORK_STATUS = "work_status"
STATE_WORK_EXPERIENCE = "work_experience"
STATE_ENGLISH_LEVEL = "english_level"
STATE_LINKEDIN = "linkedin"
STATE_VISA_HISTORY = "visa_history"
STATE_VISA_DETAILS = "visa_details"
STATE_VISA_REJECTIONS = "visa_rejections"
STATE_CRIMINAL_RECORD = "criminal_record"
STATE_HEALTH_CONDITIONS = "health_conditions"
STATE_SAVINGS = "savings"

# Familia
STATE_FAMILY_STATUS = "family_status"
STATE_FAMILY_COUNT = "family_count"
STATE_FAMILY_MEMBER_RELATION = "family_member_relation"
STATE_FAMILY_MEMBER_NAME = "family_member_name"
STATE_FAMILY_MEMBER_BIRTH = "family_member_birth"
STATE_FAMILY_MEMBER_PROFESSION = "family_member_profession"
STATE_FAMILY_MEMBER_EDUCATION = "family_member_education"
STATE_FAMILY_MEMBER_STUDY_STATUS = "family_member_study_status"
STATE_FAMILY_MEMBER_ENGLISH = "family_member_english"
STATE_FAMILY_MEMBER_PREFERENCES = "family_member_preferences"
STATE_FAMILY_MEMBER_CONCERNS = "family_member_concerns"

# Preferencias
STATE_MIGRATION_REASON = "migration_reason"
STATE_TIMELINE = "timeline"
STATE_DESTINATION_PREFERENCE = "destination_preference"
STATE_CLIMATE_PREFERENCE = "climate_preference"
STATE_CITY_SIZE_PREFERENCE = "city_size_preference"
STATE_BUDGET_INITIAL = "budget_initial"

# Exploración
STATE_SELECT_COUNTRY = "select_country"
STATE_SELECT_VISA = "select_visa"
STATE_SELECT_STATE = "select_state"
STATE_SELECT_CITY = "select_city"
STATE_HOUSING_TYPE = "housing_type"

# Documentación
STATE_DOCUMENTS_LIST = "documents_list"
STATE_DOCUMENT_UPLOAD = "document_upload"

# Consultoría
STATE_CONSULTING = "consulting"

# V4.2 FIX: Estado de clarificación emocional
# Cuando el usuario expresa confusión/emoción, NO avanzar fase, solo contener
STATE_EMOTION_CLARIFICATION = "emotion_clarification"


# V4.1 FIX: Default user data structure for defensive initialization
DEFAULT_USER_DATA = {
    "state": STATE_START,
    "language": "es",
    "profile": {
        "personal": {},
        "education": {},
        "work": {},
        "languages": {},
        "history": {},
        "financial": {}
    },
    "family_members": [],
    "current_family_index": 0,
    "preferences": {},
    "selected_route": {},
    "documents": [],
}


def _ensure_valid_user_data(data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """V4.1 FIX: Ensure user data has all required fields with safe defaults."""
    if not isinstance(data, dict):
        logger.warning(f"🔧 RECOVERY | user={user_id} | invalid data type, creating new")
        data = {}
    
    # Ensure user_id is set
    data["user_id"] = user_id
    
    # Ensure state is valid
    if "state" not in data or not isinstance(data.get("state"), str):
        data["state"] = STATE_START
        logger.warning(f"🔧 RECOVERY | user={user_id} | missing/invalid state, reset to START")
    
    # Ensure language is valid
    if "language" not in data or not isinstance(data.get("language"), str):
        data["language"] = "es"
    
    # Ensure profile structure exists
    if "profile" not in data or not isinstance(data.get("profile"), dict):
        data["profile"] = {
            "personal": {},
            "education": {},
            "work": {},
            "languages": {},
            "history": {},
            "financial": {}
        }
    else:
        # Ensure all profile sections exist
        for section in ["personal", "education", "work", "languages", "history", "financial"]:
            if section not in data["profile"] or not isinstance(data["profile"].get(section), dict):
                data["profile"][section] = {}
    
    # Ensure other required fields
    if "family_members" not in data or not isinstance(data.get("family_members"), list):
        data["family_members"] = []
    if "current_family_index" not in data:
        data["current_family_index"] = 0
    if "preferences" not in data or not isinstance(data.get("preferences"), dict):
        data["preferences"] = {}
    if "selected_route" not in data or not isinstance(data.get("selected_route"), dict):
        data["selected_route"] = {}
    if "documents" not in data or not isinstance(data.get("documents"), list):
        data["documents"] = []
    
    return data


def get_user_data(user_id: int) -> Dict[str, Any]:
    """Get or create user data - loads from disk if exists (with decryption).
    
    V4.1 FIX: Added defensive validation to handle corrupted/null data.
    """
    try:
        if user_id not in user_data:
            # Try to load from disk first
            saved_data = load_user_data(user_id)
            if saved_data:
                try:
                    # Decrypt sensitive data when loading
                    decrypted = decrypt_user_data(saved_data)
                    user_data[user_id] = _ensure_valid_user_data(decrypted, user_id)
                    logger.info(f"Loaded existing case for user (decrypted)")
                except Exception as e:
                    logger.error(f"🔴 DECRYPT_ERROR | user={user_id} | error={e}")
                    # Create new case if decryption fails
                    user_data[user_id] = _ensure_valid_user_data({}, user_id)
                    user_data[user_id]["created_at"] = datetime.now().isoformat()
                    log_user_action(user_id, "new_case", "Created new case (decrypt failed)")
            else:
                # Create new case
                user_data[user_id] = _ensure_valid_user_data({}, user_id)
                user_data[user_id]["created_at"] = datetime.now().isoformat()
                log_user_action(user_id, "new_case", "Created new migration case")
        else:
            # Validate existing data in memory
            user_data[user_id] = _ensure_valid_user_data(user_data[user_id], user_id)
        
        return user_data[user_id]
    except Exception as e:
        logger.error(f"🔴 GET_USER_DATA_ERROR | user={user_id} | error={e}")
        # Return safe default on any error
        return _ensure_valid_user_data({"user_id": user_id}, user_id)


def set_state(user_id: int, state: str):
    """Set state and auto-save to disk for persistence (with encryption).
    
    V4.1 FIX: Added validation for state parameter.
    """
    # Validate state parameter
    if not state or not isinstance(state, str):
        logger.warning(f"🔧 RECOVERY | user={user_id} | invalid state '{state}', using START")
        state = STATE_START
    
    try:
        data = get_user_data(user_id)
        data["state"] = state
        # Encrypt sensitive data before saving
        encrypted_data = encrypt_user_data(data)
        save_user_data(user_id, encrypted_data)
        log_user_action(user_id, "state_change", f"State: {state}")
    except Exception as e:
        logger.error(f"🔴 SET_STATE_ERROR | user={user_id} | state={state} | error={e}")


def get_state(user_id: int) -> str:
    """Get current state for user.
    
    V4.1 FIX: Added defensive validation to always return valid state.
    """
    try:
        state = get_user_data(user_id).get("state", STATE_START)
        if not state or not isinstance(state, str):
            logger.warning(f"🔧 RECOVERY | user={user_id} | invalid state, returning START")
            return STATE_START
        return state
    except Exception as e:
        logger.error(f"🔴 GET_STATE_ERROR | user={user_id} | error={e}")
        return STATE_START


class MigPALBot:
    """MigPAL Telegram Bot - Global Migration Assistant"""
    
    def __init__(self, token: str = TELEGRAM_BOT_TOKEN):
        self.token = token
        self.application = None
        self._running = False
        
    async def start(self):
        """Start the bot"""
        try:
            from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
            from telegram.ext import (
                Application,
                CommandHandler,
                MessageHandler,
                CallbackQueryHandler,
                filters
            )
        except ImportError:
            logger.error("python-telegram-bot not installed")
            return
        
        # V3.0.3 - Startup Self-Check: Validate all state constants exist
        logger.info("🔍 Running startup self-check...")
        
        # Define FORM_STATES for validation (same as in _handle_message)
        FORM_STATES_CHECK = [
            STATE_NAME, "confirm_name", STATE_BIRTH_DATE, STATE_CURRENT_CITY, STATE_EMAIL, STATE_PHONE,
            STATE_EDUCATION_CAREER, STATE_PROFESSION, STATE_LINKEDIN,
            STATE_TIMELINE, STATE_BUDGET_INITIAL, STATE_SAVINGS,
            STATE_FAMILY_MEMBER_NAME, STATE_FAMILY_MEMBER_BIRTH
        ]
        
        # Get module globals for validation
        module_globals = globals()
        
        # Run startup validation
        validator = get_startup_validator()
        if not validator.run_startup_check(module_globals, FORM_STATES_CHECK):
            logger.error("❌ STARTUP ABORTED: State validation failed")
            raise RuntimeError("Bot startup aborted due to state validation failure")
        
        logger.info("✅ Startup self-check passed")
        
        self.application = Application.builder().token(self.token).build()
        
        # V4.1 FIX - Improved global error handler with recovery to /start
        async def error_handler(update, context):
            """Global error handler for all exceptions.
            
            V4.1 FIX: Improved error handling with:
            - Full traceback logging
            - State validation before use
            - Recovery to /start without duplicating messages
            - Safe defaults for all user data
            """
            import traceback
            
            user_id = 0
            state = "unknown"
            lang = "es"  # Default to Spanish for MigPAL
            error_type = type(context.error).__name__ if context.error else "Unknown"
            
            # Safely extract user info
            if update and update.effective_user:
                user_id = update.effective_user.id
                try:
                    # Defensive state retrieval
                    state = get_state(user_id)
                    if not state or not isinstance(state, str):
                        state = STATE_START
                    
                    # Defensive user data retrieval
                    user = get_user_data(user_id)
                    if user and isinstance(user, dict):
                        lang = user.get("language", "es") or "es"
                except Exception as e:
                    logger.warning(f"🔧 RECOVERY | user={user_id} | error getting state/user: {e}")
            
            # Log the error with full traceback
            handler = get_exception_handler()
            handler.log_error(user_id, state, context.error, "global_handler")
            
            # Log additional context
            logger.error(
                f"🔴 GLOBAL_ERROR | user={user_id} | state={state} | "
                f"type={error_type} | msg={str(context.error)[:200]}\n"
                f"Traceback: {traceback.format_exc()[:500]}"
            )
            
            # Send fallback message with recovery hint
            try:
                fallback_msg = handler.get_fallback_message(lang)
                
                # Add recovery hint for certain error types
                if error_type in ['KeyError', 'TypeError', 'AttributeError', 'ValueError', 'IndexError']:
                    recovery_hint = (
                        "\n\n💡 Si el problema persiste, escribe /start para reiniciar."
                        if lang == "es" else
                        "\n\n💡 If the problem persists, type /start to restart."
                    )
                    fallback_msg += recovery_hint
                
                if update and update.effective_message:
                    await update.effective_message.reply_text(fallback_msg)
                    logger.info(f"✅ RECOVERY_MSG_SENT | user={user_id} | handler=global")
            except Exception as e:
                logger.error(f"❌ RECOVERY_MSG_FAILED | user={user_id} | error={e}")
        
        self.application.add_error_handler(error_handler)
        
        # Handlers
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("help", self._cmd_help))
        self.application.add_handler(CommandHandler("nuevo", self._cmd_new))
        self.application.add_handler(CommandHandler("perfil", self._cmd_profile))
        self.application.add_handler(CommandHandler("resumen", self._cmd_resumen))  # SEGMENTO 3/3
        self.application.add_handler(CommandHandler("estado", self._cmd_status))
        self.application.add_handler(CommandHandler("listo", self._cmd_done_docs))
        self.application.add_handler(CommandHandler("sos", self._cmd_sos))
        self.application.add_handler(CommandHandler("score", self._cmd_score))
        self.application.add_handler(CommandHandler("costos", self._cmd_costs))
        self.application.add_handler(CommandHandler("comunidad", self._cmd_community))
        self.application.add_handler(CommandHandler("checklist", self._cmd_checklist))
        self.application.add_handler(CommandHandler("tracking", self._cmd_tracking))
        self.application.add_handler(CommandHandler("mentores", self._cmd_mentors))
        self.application.add_handler(CommandHandler("abogados", self._cmd_lawyers))
        self.application.add_handler(CommandHandler("empleos", self._cmd_jobs))
        self.application.add_handler(CommandHandler("guia", self._cmd_guide))
        self.application.add_handler(CommandHandler("motivacion", self._cmd_motivation))
        self.application.add_handler(CommandHandler("reporte", self._cmd_report))
        # V3.2.1 - Export commands for auditing
        self.application.add_handler(CommandHandler("export_case", self._cmd_export_case))
        self.application.add_handler(CommandHandler("export_day", self._cmd_export_day))
        self.application.add_handler(CommandHandler("idioma", self._cmd_language))
        self.application.add_handler(CommandHandler("notificaciones", self._cmd_notifications))
        # Gamification & Payment commands
        self.application.add_handler(CommandHandler("nivel", self._cmd_level))
        self.application.add_handler(CommandHandler("diagnostico", self._cmd_diagnostic))
        self.application.add_handler(CommandHandler("precios", self._cmd_prices))
        self.application.add_handler(CommandHandler("pagar", self._cmd_pay))
        self.application.add_handler(CommandHandler("pagos", self._cmd_payments))
        self.application.add_handler(CommandHandler("entregables", self._cmd_deliverables))
        self.application.add_handler(CommandHandler("devolucion", self._cmd_refund))
        # New V2.0 commands - City exploration and housing
        self.application.add_handler(CommandHandler("explorar", self._cmd_explore))
        self.application.add_handler(CommandHandler("viviendas", self._cmd_housing))
        self.application.add_handler(CommandHandler("flujo", self._cmd_flow))
        # V2.2 commands - Education, PDF reports, comparison
        self.application.add_handler(CommandHandler("escuelas", self._cmd_schools))
        self.application.add_handler(CommandHandler("universidades", self._cmd_universities))
        self.application.add_handler(CommandHandler("comparar", self._cmd_compare))
        self.application.add_handler(CommandHandler("pdf", self._cmd_pdf))
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self._handle_document))
        self.application.add_handler(MessageHandler(filters.PHOTO, self._handle_photo))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        logger.info("🤖 MigPAL Bot GLOBAL starting...")
        self._running = True
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        logger.info("✅ MigPAL Bot GLOBAL is running!")
        
        # Start notification scheduler
        try:
            set_scheduler_callback(self._send_notification_message)
            await start_scheduler()
            logger.info("✅ Notification scheduler started!")
        except Exception as e:
            logger.error(f"Failed to start notification scheduler: {e}")
        
    async def stop(self):
        if self.application and self._running:
            self._running = False
            # Stop notification scheduler
            try:
                await stop_scheduler()
                logger.info("Notification scheduler stopped")
            except Exception as e:
                logger.error(f"Error stopping scheduler: {e}")
            
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
    
    def _kb(self, options: list) -> 'InlineKeyboardMarkup':
        """Create inline keyboard"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = []
        for opt in options:
            if isinstance(opt, tuple):
                keyboard.append([InlineKeyboardButton(opt[0], callback_data=opt[1])])
            elif isinstance(opt, list):
                row = [InlineKeyboardButton(o[0], callback_data=o[1]) if isinstance(o, tuple) 
                       else InlineKeyboardButton(o, callback_data=o) for o in opt]
                keyboard.append(row)
            else:
                keyboard.append([InlineKeyboardButton(opt, callback_data=opt)])
        return InlineKeyboardMarkup(keyboard)
    
    def _get_state_prompt(self, state: str, user: dict, lang: str = "es") -> str:
        """Obtener el prompt para el estado actual (para re-preguntar después de corrección)"""
        prompts = {
            "es": {
                STATE_NAME: "¿Cuál es tu nombre completo?",
                STATE_BIRTH_DATE: "¿Cuál es tu fecha de nacimiento? (DD/MM/AAAA)",
                STATE_EMAIL: "¿Cuál es tu correo electrónico?",
                STATE_PHONE: "¿Cuál es tu número de teléfono?",
                STATE_CURRENT_CITY: "¿En qué ciudad vives actualmente?",
                STATE_EDUCATION_CAREER: "¿Qué carrera estudiaste o estudias?",
                STATE_PROFESSION: "¿Cuál es tu profesión actual?",
                "education_level": "¿Cuál es tu nivel educativo?",
                "work_status": "¿Cuál es tu situación laboral actual?",
            },
            "en": {
                STATE_NAME: "What is your full name?",
                STATE_BIRTH_DATE: "What is your birth date? (DD/MM/YYYY)",
                STATE_EMAIL: "What is your email address?",
                STATE_PHONE: "What is your phone number?",
                STATE_CURRENT_CITY: "What city do you currently live in?",
                STATE_EDUCATION_CAREER: "What did you study or are studying?",
                STATE_PROFESSION: "What is your current profession?",
                "education_level": "What is your education level?",
                "work_status": "What is your current work status?",
            }
        }
        
        lang_prompts = prompts.get(lang, prompts["es"])
        return lang_prompts.get(state, "Continúa con tu respuesta:" if lang == "es" else "Continue with your answer:")
    
    # ============== COMMANDS ==============
    
    async def _check_rate_limit(self, update) -> bool:
        """Check rate limit and send message if exceeded"""
        user_id = update.effective_user.id
        allowed, message = check_rate_limit(user_id)
        if not allowed:
            await update.effective_message.reply_text(message)
            return False
        return True
    
    @safe_async_handler
    async def _cmd_start(self, update, context):
        """v3.0.6 - Onboarding conversacional. NO inicia formularios."""
        if not await self._check_rate_limit(update):
            return
        
        user_id = update.effective_user.id
        user_data[user_id] = get_user_data(user_id)
        user_data[user_id]["profile"]["personal"]["telegram_name"] = sanitize_input(update.effective_user.first_name or "")
        
        log_user_action(user_id, "start", "Started bot")
        
        # Verificar si ya tiene idioma seleccionado
        lang = user_data[user_id].get("language")
        
        if not lang:
            # Primer contacto: mostrar selección de idioma con mensaje cálido
            user_data[user_id]["state"] = STATE_START
            save_user_data(user_id, user_data[user_id])
            
            await update.message.reply_text(
                "🌍 ¡Hola! / Hi! / Olá!\n\n"
                "Antes de empezar, ¿cuál es tu idioma preferido?\n"
                "Before we start, what's your preferred language?\n"
                "Antes de começar, qual é o seu idioma preferido?",
                reply_markup=self._kb([
                    [("🇪🇸 Español", "lang_es"), ("🇬🇧 English", "lang_en")],
                    [("🇧🇷 Português", "lang_pt"), ("🇫🇷 Français", "lang_fr")],
                    [("🌐 Más / More", "lang_more")]
                ])
            )
        else:
            # V5.0: Onboarding conversacional simple - UN solo mensaje de bienvenida
            # NO hay estados rígidos, NO hay formularios, solo conversación natural
            
            # Estado simple: "conversing" - el bot está conversando
            user_data[user_id]["state"] = "conversing"
            save_user_data(user_id, user_data[user_id])
            
            # Mensaje de bienvenida conversacional (UN solo mensaje)
            welcome_msg = get_conversational_welcome(lang)
            await update.message.reply_text(welcome_msg)
    
    async def _cmd_help(self, update, context):
        user_id = update.effective_user.id
        lang = get_user_data(user_id).get("language", "en")
        
        await update.message.reply_text(
            "🆘 *MigPAL V2.0 - Tu Consultor de Migración*\n\n"
            "*🗺️ NUEVO - Exploración V2.0:*\n"
            "/flujo - Flujo guiado de migración\n"
            "/explorar - Explorar ciudades con scoring\n"
            "/viviendas - Buscar viviendas (Zillow)\n\n"
            "*🎮 Tu Proceso (Gamificado):*\n"
            "/nivel - Ver tu nivel y progreso\n"
            "/diagnostico - Iniciar diagnóstico ($50)\n"
            "/entregables - Ver tus entregables\n"
            "/precios - Ver precios y garantías\n\n"
            "*💳 Pagos:*\n"
            "/pagar - Realizar un pago\n"
            "/pagos - Historial de pagos\n"
            "/devolucion - Solicitar devolución\n\n"
            "*📝 Proceso:*\n"
            "/start - Iniciar\n"
            "/perfil - Ver perfil\n"
            "/estado - Ver progreso\n\n"
            "*📊 Análisis:*\n"
            "/score - Probabilidad de éxito\n"
            "/costos - Calculadora de costos\n"
            "/checklist - Documentos requeridos\n"
            "/empleos - Buscar empleos con sponsor\n\n"
            "*👥 Apoyo:*\n"
            "/mentores - Conectar con mentores\n"
            "/comunidad - Grupos de apoyo\n\n"
            "*🆘 Emergencia:*\n"
            "/sos - Ayuda urgente\n\n"
            "*⚙️ Configuración:*\n"
            "/idioma - Cambiar idioma\n"
            "/notificaciones - Configurar alertas\n\n"
            "_🌍 MigPAL - La visa es el VEHÍCULO, no el DESTINO_",
            parse_mode='Markdown'
        )
    
    async def _cmd_new(self, update, context):
        """Start a new case - deletes all previous data"""
        user_id = update.effective_user.id
        # Delete from memory
        if user_id in user_data:
            del user_data[user_id]
        # Delete from disk
        delete_user_data(user_id)
        logger.info(f"User {user_id} started new case - all data deleted")
        await self._cmd_start(update, context)
    
    async def _cmd_profile(self, update, context):
        user_id = update.effective_user.id
        data = get_user_data(user_id)
        p = data.get("profile", {})
        personal = p.get("personal", {})
        
        text = "📋 *Tu Perfil*\n\n"
        if personal.get("name"):
            text += f"👤 {personal['name']}\n"
            text += f"🎂 {personal.get('birth_date', 'N/A')}\n"
            text += f"🏳️ {personal.get('nationality', 'N/A')}\n"
            text += f"📍 {personal.get('current_city', '')}, {personal.get('current_country', '')}\n"
        
        work = p.get("work", {})
        if work.get("profession"):
            text += f"\n💼 {work['profession']}\n"
            text += f"📊 {work.get('experience', '')} experiencia\n"
        
        route = data.get("selected_route", {})
        if route.get("country"):
            text += f"\n🎯 Destino: {route['country']}\n"
            text += f"📄 Visa: {route.get('visa_type', 'N/A')}\n"
        
        docs = data.get("documents", [])
        if docs:
            text += f"\n📎 Documentos: {len(docs)} archivo(s)\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def _cmd_resumen(self, update, context):
        """
        V3.1.0: Muestra Resumen de Entendimiento y pide confirmación.
        REGLA CRÍTICA: Sin confirmación de este resumen, NO se puede recomendar visa.
        """
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        lang = user.get("language", "es")
        
        # Validar perfil
        validation = validate_profile(user)
        
        # Generar resumen usando el nuevo módulo
        summary_manager = get_summary_manager()
        summary_text, summary_buttons = summary_manager.generate_summary_text(user, lang)
        
        # Marcar que se mostró el resumen (para tracking)
        mark_summary_shown(user_id)
        
        # Agregar información de completitud
        completeness_msg = f"\n\n📊 *Completitud:* {validation.percentage:.0f}%"
        if validation.missing_required:
            missing_count = len(validation.missing_required)
            completeness_msg += f"\n⚠️ Faltan {missing_count} dato(s) requeridos"
        
        await update.message.reply_text(
            summary_text + completeness_msg,
            parse_mode='Markdown',
            reply_markup=self._kb(summary_buttons)
        )
    
    async def _cmd_status(self, update, context):
        user_id = update.effective_user.id
        state = get_state(user_id)
        
        phases = [
            ("1️⃣ Perfil Personal", ["name", "birth", "nationality", "education", "work", "english", "linkedin", "visa", "savings"]),
            ("2️⃣ Familia", ["family"]),
            ("3️⃣ Preferencias", ["migration_reason", "timeline", "destination", "climate", "budget"]),
            ("4️⃣ Opciones", ["select_country", "select_visa"]),
            ("5️⃣ Planificación", ["select_state", "select_city", "housing"]),
            ("6️⃣ Documentos", ["document"]),
            ("7️⃣ Consultoría", ["consulting"])
        ]
        
        text = "📊 *Tu Progreso*\n\n"
        found = False
        for phase, keywords in phases:
            if not found and any(k in state for k in keywords):
                text += f"🔵 {phase} ← Aquí\n"
                found = True
            elif found:
                text += f"⚪ {phase}\n"
            else:
                text += f"✅ {phase}\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def _cmd_done_docs(self, update, context):
        """Handle /listo command for finishing document upload"""
        user_id = update.effective_user.id
        state = get_state(user_id)
        
        if state == STATE_DOCUMENT_UPLOAD:
            docs = get_user_data(user_id).get("documents", [])
            set_state(user_id, STATE_CONSULTING)
            await update.message.reply_text(
                f"✅ *¡{len(docs)} documento(s) recibido(s)!*\n\n"
                "Los revisaré y te daré retroalimentación.\n\n"
                "Ahora puedes hacerme preguntas sobre tu proceso.\n"
                "¿En qué puedo ayudarte?",
                parse_mode='Markdown',
                reply_markup=self._kb([
                    ("📋 Ver requisitos de visa", "req_visa"),
                    ("💰 Ver costos estimados", "req_costs"),
                    ("⏱️ Ver tiempos del proceso", "req_time"),
                    ("💬 Hacer una pregunta", "ask_question")
                ])
            )
        else:
            await update.message.reply_text(
                "Este comando es para terminar la carga de documentos.\n"
                "Usa /estado para ver en qué fase estás."
            )
    
    # ============== NEW COMMANDS V4 ==============
    
    async def _cmd_sos(self, update, context):
        """Emergency help command - CRITICAL for migrant safety"""
        await update.message.reply_text(
            "🆘 *AYUDA DE EMERGENCIA*\n\n"
            "*Si estás en peligro inmediato, llama al 911*\n\n"
            "📞 *Líneas de Ayuda 24/7:*\n\n"
            "🇺🇸 *USA:*\n"
            "• ICE Detainee: 1-888-351-4024\n"
            "• RAICES (legal): 1-210-231-2475\n"
            "• National Human Trafficking: 1-888-373-7888\n\n"
            "🇨🇦 *Canadá:*\n"
            "• CBSA: 1-800-461-9999\n"
            "• Settlement.org: 1-888-910-1010\n\n"
            "🇪🇸 *España:*\n"
            "• Atención al Ciudadano: 060\n"
            "• Cruz Roja: 900 22 22 92\n\n"
            "🌎 *Internacional:*\n"
            "• OIM (Migración): +41 22 717 9111\n"
            "• ACNUR (Refugiados): +41 22 739 8111\n\n"
            "⚠️ *Estafas Comunes:*\n"
            "• Nunca pagues en efectivo\n"
            "• Verifica abogados en colegios oficiales\n"
            "• No entregues documentos originales\n"
            "• Desconfía de 'garantías' de aprobación\n\n"
            "💪 *Recuerda: Tienes derechos sin importar tu estatus migratorio*",
            parse_mode='Markdown'
        )
    
    async def _cmd_score(self, update, context):
        """Calculate success probability score based on profile"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        profile = user.get("profile", {})
        route = user.get("selected_route", {})
        
        # Check if profile is complete enough
        personal = profile.get("personal", {})
        if not personal.get("name"):
            await update.message.reply_text(
                "⚠️ Necesitas completar tu perfil primero.\n"
                "Usa /start para comenzar."
            )
            return
        
        # Calculate score
        score, breakdown = self._calculate_score(user)
        
        # Determine emoji based on score
        if score >= 80:
            emoji = "🟢"
            message = "¡Excelente perfil!"
        elif score >= 60:
            emoji = "🟡"
            message = "Buen perfil, con mejoras posibles"
        elif score >= 40:
            emoji = "🟠"
            message = "Perfil moderado, considera mejoras"
        else:
            emoji = "🔴"
            message = "Perfil con desafíos, pero hay opciones"
        
        visa = route.get("visa_type", "General")
        country = route.get("country", "No seleccionado")
        
        await update.message.reply_text(
            f"📊 *TU SCORE DE MIGRACIÓN*\n\n"
            f"{emoji} *{score}/100* - {message}\n\n"
            f"🎯 Destino: {country}\n"
            f"📄 Visa: {visa}\n\n"
            f"*Desglose:*\n{breakdown}\n\n"
            f"💡 *Recomendaciones:*\n"
            f"{self._get_recommendations(user, score)}",
            parse_mode='Markdown'
        )
    
    def _calculate_score(self, user: dict) -> tuple:
        """Calculate migration success score"""
        profile = user.get("profile", {})
        personal = profile.get("personal", {})
        education = profile.get("education", {})
        work = profile.get("work", {})
        languages = profile.get("languages", {})
        history = profile.get("history", {})
        financial = profile.get("financial", {})
        
        score = 0
        breakdown = ""
        
        # Education (max 25 points)
        edu_level = education.get("level", "")
        edu_points = {
            "Doctorado": 25, "Maestría": 22, "Especialización": 20,
            "Universitario": 18, "Técnico": 12, "Bachillerato": 8
        }.get(edu_level, 5)
        score += edu_points
        breakdown += f"🎓 Educación: +{edu_points}\n"
        
        # Work Experience (max 20 points)
        exp = work.get("experience", "")
        exp_points = {
            ">15": 20, "10-15": 18, "5-10": 15,
            "3-5": 12, "1-3": 8, "<1": 4
        }.get(exp, 5)
        score += exp_points
        breakdown += f"💼 Experiencia: +{exp_points}\n"
        
        # English Level (max 20 points)
        english = languages.get("english", "")
        eng_points = {
            "Nativo": 20, "Avanzado": 18, "Intermedio": 12,
            "Básico": 6, "Ninguno": 2
        }.get(english, 5)
        score += eng_points
        breakdown += f"🌐 Inglés: +{eng_points}\n"
        
        # Financial (max 15 points)
        savings = financial.get("savings", "")
        fin_points = {
            ">100k": 15, "50k-100k": 14, "30k-50k": 12,
            "15k-30k": 10, "5k-15k": 7, "<5k": 4
        }.get(savings, 5)
        score += fin_points
        breakdown += f"💰 Finanzas: +{fin_points}\n"
        
        # Clean History (max 10 points)
        has_rejections = history.get("rejections", "No") == "Sí"
        has_criminal = history.get("criminal", "No") == "Sí"
        hist_points = 10
        if has_rejections:
            hist_points -= 5
        if has_criminal:
            hist_points -= 5
        score += hist_points
        breakdown += f"📋 Historial: +{hist_points}\n"
        
        # Previous Visas (max 10 points)
        has_visas = history.get("has_visas", "No") == "Sí"
        visa_points = 10 if has_visas else 5
        score += visa_points
        breakdown += f"🛂 Visas previas: +{visa_points}\n"
        
        return min(score, 100), breakdown
    
    def _get_recommendations(self, user: dict, score: int) -> str:
        """Get personalized recommendations based on profile"""
        profile = user.get("profile", {})
        languages = profile.get("languages", {})
        education = profile.get("education", {})
        
        recs = []
        
        english = languages.get("english", "")
        if english in ["Ninguno", "Básico"]:
            recs.append("• 📚 Mejorar inglés aumentaría tu score +10-15 puntos")
        
        edu_level = education.get("level", "")
        if edu_level in ["Bachillerato", "Técnico"]:
            recs.append("• 🎓 Una certificación o posgrado mejoraría tu perfil")
        
        if score < 60:
            recs.append("• 💡 Considera programas de estudio como ruta alternativa")
            recs.append("• 🎲 Aplica a la Lotería de Visas (DV) - es gratis")
        
        if not recs:
            recs.append("• ✅ Tu perfil es competitivo, ¡adelante con tu aplicación!")
        
        return "\n".join(recs)
    
    async def _cmd_costs(self, update, context):
        """Cost calculator for migration"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        route = user.get("selected_route", {})
        prefs = user.get("preferences", {})
        
        country = route.get("country", "USA")
        visa = route.get("visa_type", "General")
        family_count = prefs.get("family_count", 1)
        
        # Cost estimates by country
        costs = self._get_cost_estimates(country, visa, family_count)
        
        await update.message.reply_text(
            f"💰 *CALCULADORA DE COSTOS*\n\n"
            f"🎯 Destino: {country}\n"
            f"📄 Visa: {visa}\n"
            f"👥 Personas: {family_count}\n\n"
            f"*Costos Estimados (USD):*\n\n"
            f"📋 *Trámites y Visa:*\n{costs['tramites']}\n\n"
            f"✈️ *Viaje:*\n{costs['viaje']}\n\n"
            f"🏠 *Primeros 3 Meses:*\n{costs['establecimiento']}\n\n"
            f"⚠️ *Costos Ocultos:*\n{costs['ocultos']}\n\n"
            f"💵 *TOTAL ESTIMADO: ${costs['total']:,} USD*\n\n"
            f"💡 _Estos son estimados. Los costos reales pueden variar._",
            parse_mode='Markdown'
        )
    
    def _get_cost_estimates(self, country: str, visa: str, family_count: int) -> dict:
        """Get cost estimates by country"""
        base_costs = {
            "USA": {
                "visa_fee": 185,
                "biometrics": 85,
                "medical": 200,
                "flight": 800,
                "rent_month": 1800,
                "living_month": 1200,
                "insurance_month": 400,
                "translations": 300,
                "apostilles": 200
            },
            "Canadá": {
                "visa_fee": 150,
                "biometrics": 85,
                "medical": 300,
                "flight": 700,
                "rent_month": 1600,
                "living_month": 1000,
                "insurance_month": 100,
                "translations": 400,
                "apostilles": 200
            },
            "España": {
                "visa_fee": 80,
                "biometrics": 0,
                "medical": 100,
                "flight": 900,
                "rent_month": 1200,
                "living_month": 800,
                "insurance_month": 100,
                "translations": 200,
                "apostilles": 150
            },
            "Alemania": {
                "visa_fee": 75,
                "biometrics": 0,
                "medical": 100,
                "flight": 1000,
                "rent_month": 1400,
                "living_month": 900,
                "insurance_month": 150,
                "translations": 350,
                "apostilles": 200
            }
        }
        
        c = base_costs.get(country, base_costs["USA"])
        
        # Calculate totals
        tramites_total = (c["visa_fee"] + c["biometrics"] + c["medical"]) * family_count
        viaje_total = c["flight"] * family_count
        establecimiento_total = (c["rent_month"] + c["living_month"] + c["insurance_month"]) * 3
        ocultos_total = c["translations"] + c["apostilles"] + 500  # Buffer
        
        return {
            "tramites": f"• Visa: ${c['visa_fee'] * family_count}\n• Biométricos: ${c['biometrics'] * family_count}\n• Examen médico: ${c['medical'] * family_count}\n• Subtotal: ${tramites_total}",
            "viaje": f"• Vuelos: ${viaje_total}\n• Equipaje extra: ~$200",
            "establecimiento": f"• Renta (3 meses): ${c['rent_month'] * 3}\n• Gastos de vida: ${c['living_month'] * 3}\n• Seguro: ${c['insurance_month'] * 3}\n• Subtotal: ${establecimiento_total}",
            "ocultos": f"• Traducciones: ${c['translations']}\n• Apostillas: ${c['apostilles']}\n• Imprevistos: ~$500",
            "total": tramites_total + viaje_total + establecimiento_total + ocultos_total + 200
        }
    
    async def _cmd_community(self, update, context):
        """Community groups and support"""
        await update.message.reply_text(
            "👥 *COMUNIDAD MIGPAL*\n\n"
            "Únete a grupos de apoyo con otros migrantes:\n\n"
            "🇺🇸 *USA:*\n"
            "• Latinos en USA: t.me/latinosenusa\n"
            "• Visas USA Info: t.me/visasusa\n\n"
            "🇨🇦 *Canadá:*\n"
            "• Express Entry Latino: t.me/expressentry_latino\n"
            "• Colombianos en Canadá: t.me/colombianoscanada\n\n"
            "🇪🇸 *España:*\n"
            "• Latinos en España: t.me/latinosenespana\n\n"
            "🌎 *General:*\n"
            "• MigPAL Comunidad: t.me/migpal_comunidad\n\n"
            "💡 *Tips:*\n"
            "• Comparte tu experiencia\n"
            "• Pregunta a quienes ya pasaron por el proceso\n"
            "• Encuentra mentores\n\n"
            "_¿Quieres ser mentor? Escríbenos a @MigPAL_Bot_",
            parse_mode='Markdown'
        )
    
    # ============== NEW V5 COMMANDS ==============
    
    async def _cmd_checklist(self, update, context):
        """Document checklist based on visa type"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        route = user.get("selected_route", {})
        
        country = route.get("country")
        visa = route.get("visa_type")
        
        if not country or not visa:
            await update.message.reply_text(
                "⚠️ Primero debes seleccionar un país y tipo de visa.\n"
                "Usa /start para completar tu perfil."
            )
            return
        
        docs = get_document_checklist(country, visa)
        user_docs = user.get("documents", [])
        status = check_document_status(user_docs, docs)
        
        # Build checklist message
        msg = f"📋 *CHECKLIST DE DOCUMENTOS*\n\n"
        msg += f"🎯 {country} - {visa}\n"
        msg += f"📊 Progreso: {status['completed_percentage']}%\n\n"
        
        msg += "*✅ Documentos Requeridos:*\n"
        for doc in docs:
            if doc["required"]:
                emoji = "✅" if doc["name"] not in [d["name"] for d in status["missing_required"]] else "⬜"
                validity = f" ({doc['validity']})" if doc['validity'] else ""
                msg += f"{emoji} {doc['name']}{validity}\n"
                if doc['notes']:
                    msg += f"   _└ {doc['notes']}_\n"
        
        if status["missing_optional"]:
            msg += "\n*📝 Opcionales:*\n"
            for doc in status["missing_optional"]:
                msg += f"⬜ {doc['name']}\n"
        
        msg += f"\n📤 *Subidos:* {status['uploaded']} documento(s)\n"
        msg += "\n_Envía tus documentos como fotos o archivos_"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def _cmd_tracking(self, update, context):
        """Application tracking timeline"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        route = user.get("selected_route", {})
        
        country = route.get("country")
        visa = route.get("visa_type")
        
        if not country or not visa:
            await update.message.reply_text(
                "⚠️ Primero debes seleccionar un país y tipo de visa.\n"
                "Usa /start para completar tu perfil."
            )
            return
        
        stages = get_application_stages(country, visa)
        if not stages:
            await update.message.reply_text(
                f"⚠️ Aún no tenemos tracking detallado para {visa} en {country}.\n"
                "Estamos trabajando en ello."
            )
            return
        
        timeline = calculate_timeline(stages)
        current_stage = user.get("current_stage", 0)
        
        msg = f"📍 *TRACKING DE APLICACIÓN*\n\n"
        msg += f"🎯 {country} - {visa}\n\n"
        
        for i, stage in enumerate(timeline):
            if i < current_stage:
                emoji = "✅"
            elif i == current_stage:
                emoji = "🔵"
            else:
                emoji = "⚪"
            
            msg += f"{emoji} *{stage['name']}*\n"
            msg += f"   ⏱️ {stage['duration']}\n"
            msg += f"   📅 {stage['start_date']} - {stage['end_date']}\n"
            for task in stage['tasks'][:2]:
                msg += f"   • {task}\n"
            msg += "\n"
        
        msg += "\n_Usa los botones para actualizar tu progreso_"
        
        await update.message.reply_text(
            msg,
            parse_mode='Markdown',
            reply_markup=self._kb([
                ("✅ Marcar etapa completada", "tracking_complete"),
                ("📅 Ver fechas estimadas", "tracking_dates")
            ])
        )
    
    async def _cmd_mentors(self, update, context):
        """Connect with verified mentors"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        route = user.get("selected_route", {})
        country = route.get("country")
        
        mentors = get_mentors(country)
        
        msg = "🧑‍🏫 *MENTORES VERIFICADOS*\n\n"
        msg += "Conecta con migrantes que ya pasaron por el proceso:\n\n"
        
        for mentor in mentors[:5]:
            msg += f"⭐ *{mentor['name']}* ({mentor['rating']}⭐)\n"
            msg += f"   🌍 {mentor['country_origin']} → {mentor['country_destination']}\n"
            msg += f"   📄 {mentor['visa_type']}\n"
            msg += f"   💼 {mentor['profession']}\n"
            msg += f"   💬 {mentor['sessions']} sesiones\n"
            msg += f"   _{mentor['bio']}_\n\n"
        
        msg += "💡 *¿Cómo funciona?*\n"
        msg += "• Sesión de 30 min por videollamada\n"
        msg += "• Resuelve tus dudas específicas\n"
        msg += "• Aprende de experiencias reales\n\n"
        msg += "_Selecciona un mentor para agendar:_"
        
        buttons = [(f"💬 {m['name']}", f"mentor_{m['id']}") for m in mentors[:3]]
        buttons.append(("🔍 Ver más mentores", "mentors_more"))
        
        await update.message.reply_text(
            msg,
            parse_mode='Markdown',
            reply_markup=self._kb(buttons)
        )
    
    async def _cmd_lawyers(self, update, context):
        """Directory of verified immigration lawyers"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        route = user.get("selected_route", {})
        country = route.get("country")
        
        lawyers = get_lawyers(country)
        
        msg = "⚖️ *ABOGADOS DE INMIGRACIÓN VERIFICADOS*\n\n"
        
        if country:
            msg += f"🎯 Especialistas en {country}:\n\n"
        
        for lawyer in lawyers[:4]:
            verified = "✅" if lawyer['verified'] else ""
            msg += f"{verified} *{lawyer['name']}*\n"
            msg += f"   🏢 {lawyer['firm']}\n"
            msg += f"   📍 {lawyer['location']}\n"
            msg += f"   💼 {', '.join(lawyer['specialties'])}\n"
            msg += f"   🗣️ {', '.join(lawyer['languages'])}\n"
            msg += f"   ⭐ {lawyer['rating']} ({lawyer['reviews']} reseñas)\n"
            msg += f"   💰 Consulta: ${lawyer['consultation_fee']} USD\n"
            msg += f"   📧 {lawyer['contact']}\n\n"
        
        msg += "⚠️ *Importante:*\n"
        msg += "• Verifica credenciales antes de contratar\n"
        msg += "• Pide referencias de otros clientes\n"
        msg += "• Nunca pagues sin contrato escrito\n\n"
        msg += "_MigPAL no es responsable por servicios de terceros_"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def _cmd_jobs(self, update, context):
        """Job board with visa sponsorship"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        route = user.get("selected_route", {})
        profile = user.get("profile", {})
        
        country = route.get("country")
        profession = profile.get("work", {}).get("profession")
        
        jobs = get_jobs(country, profession)
        
        msg = "💼 *BOLSA DE TRABAJO CON SPONSOR DE VISA*\n\n"
        
        if not jobs:
            msg += "No encontramos empleos que coincidan con tu perfil.\n"
            msg += "Intenta ampliar tu búsqueda.\n\n"
            jobs = get_jobs()  # Show all jobs
        
        for job in jobs[:5]:
            sponsor = "✅ Sponsor" if job['visa_sponsorship'] else ""
            msg += f"📌 *{job['title']}* {sponsor}\n"
            msg += f"   🏢 {job['company']}\n"
            msg += f"   📍 {job['location']}\n"
            msg += f"   💰 {job['salary']}\n"
            msg += f"   📄 Visas: {', '.join(job['visa_types'])}\n"
            msg += f"   📝 {', '.join(job['requirements'][:2])}\n"
            msg += f"   🔗 {job['url']}\n\n"
        
        msg += "💡 *Tips para conseguir sponsor:*\n"
        msg += "• Destaca habilidades únicas\n"
        msg += "• Aplica a empresas grandes (más experiencia con visas)\n"
        msg += "• Networking en LinkedIn\n"
        msg += "• Considera startups en crecimiento"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def _cmd_guide(self, update, context):
        """Settlement guide for destination country"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        route = user.get("selected_route", {})
        country = route.get("country", "USA")
        
        guide = get_settlement_guide(country)
        
        if not guide:
            await update.message.reply_text(
                f"⚠️ Aún no tenemos guía para {country}.\n"
                "Estamos trabajando en ello."
            )
            return
        
        msg = f"🏠 *GUÍA DE ESTABLECIMIENTO - {country}*\n\n"
        msg += "Selecciona un tema:\n\n"
        
        buttons = []
        for key, section in guide.items():
            buttons.append((section['title'], f"guide_{country}_{key}"))
        
        await update.message.reply_text(
            msg,
            parse_mode='Markdown',
            reply_markup=self._kb(buttons)
        )
    
    async def _cmd_motivation(self, update, context):
        """Send motivational message"""
        message = get_motivational_message()
        
        await update.message.reply_text(
            f"{message}\n\n"
            "_¿Necesitas más motivación? Usa /motivacion de nuevo_",
            parse_mode='Markdown'
        )
    
    async def _cmd_report(self, update, context):
        """Generate case report"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        
        personal = user.get("profile", {}).get("personal", {})
        if not personal.get("name"):
            await update.message.reply_text(
                "⚠️ Necesitas completar tu perfil primero.\n"
                "Usa /start para comenzar."
            )
            return
        
        report = generate_case_report(user)
        
        # Send as text (in production would generate PDF)
        await update.message.reply_text(
            "📄 *REPORTE DE TU CASO*\n\n"
            "Aquí está el resumen de tu proceso migratorio:\n\n"
            f"```\n{report[:3500]}\n```\n\n"
            "_En futuras versiones podrás descargar como PDF_",
            parse_mode='Markdown'
        )
    
    async def _cmd_export_case(self, update, context):
        """
        V3.2.1 - Export conversation case for a user.
        Usage: /export_case <user_id>
        Admin only command.
        """
        user_id = update.effective_user.id
        
        # Check if admin (you can customize this list)
        ADMIN_IDS = [123456789]  # Add your admin user IDs here
        
        # For testing, allow any user to export their own data
        args = context.args if context.args else []
        
        if args:
            target_user_id = int(args[0])
            # Only admins can export other users' data
            if target_user_id != user_id and user_id not in ADMIN_IDS:
                await update.message.reply_text(
                    "⚠️ Solo puedes exportar tus propios datos.\n"
                    "Usa: /export_case (sin argumentos)"
                )
                return
        else:
            target_user_id = user_id
        
        try:
            md_path, json_path = export_case(target_user_id)
            await update.message.reply_text(
                f"✅ *Caso exportado*\n\n"
                f"📄 MD: `{md_path}`\n"
                f"📊 JSON: `{json_path}`\n\n"
                f"_User ID: {target_user_id}_",
                parse_mode='Markdown'
            )
        except ValueError as e:
            await update.message.reply_text(
                f"❌ Error: {str(e)}\n\n"
                "No se encontraron conversaciones para este usuario."
            )
        except Exception as e:
            logger.error(f"Export case error: {e}")
            await update.message.reply_text(
                f"❌ Error al exportar: {str(e)}"
            )
    
    async def _cmd_export_day(self, update, context):
        """
        V3.2.1 - Export all conversations from a specific day.
        Usage: /export_day YYYY-MM-DD
        Admin only command.
        """
        user_id = update.effective_user.id
        
        # Check if admin
        ADMIN_IDS = [123456789]  # Add your admin user IDs here
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text(
                "⚠️ Este comando es solo para administradores."
            )
            return
        
        args = context.args if context.args else []
        
        if not args:
            # Default to today
            from datetime import datetime
            date_str = datetime.now().strftime('%Y-%m-%d')
        else:
            date_str = args[0]
        
        try:
            md_path, json_path = export_day(date_str)
            await update.message.reply_text(
                f"✅ *Día exportado: {date_str}*\n\n"
                f"📄 MD: `{md_path}`\n"
                f"📊 JSON: `{json_path}`",
                parse_mode='Markdown'
            )
        except ValueError as e:
            await update.message.reply_text(
                f"❌ Error: {str(e)}\n\n"
                f"No se encontraron conversaciones para {date_str}."
            )
        except Exception as e:
            logger.error(f"Export day error: {e}")
            await update.message.reply_text(
                f"❌ Error al exportar: {str(e)}"
            )
    
    async def _cmd_language(self, update, context):
        """Change bot language - supports 25+ languages globally"""
        # Get all available languages
        languages = get_all_languages()
        
        # Create buttons in rows of 2
        buttons = []
        row = []
        for name, code in languages[:20]:  # Show first 20 languages
            row.append((name, f"lang_{code}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        
        buttons.append([("🌐 More languages...", "lang_more")])
        
        await update.message.reply_text(
            "🌐 *SELECT YOUR LANGUAGE / SELECCIONA TU IDIOMA*\n\n"
            "请选择您的语言 / 言語を選択 / 언어 선택\n"
            "Выберите язык / اختر لغتك / अपनी भाषा चुनें\n\n"
            "_MigPAL supports 25+ languages for migrants worldwide_",
            parse_mode='Markdown',
            reply_markup=self._kb(buttons)
        )
    
    async def _cmd_notifications(self, update, context):
        """Configure notification preferences"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        
        # Get current preferences
        prefs = user.get("notification_prefs", get_default_notification_prefs())
        
        msg = "🔔 *CONFIGURACIÓN DE NOTIFICACIONES*\n\n"
        msg += "Personaliza qué notificaciones quieres recibir:\n\n"
        
        buttons = []
        for ntype, info in NOTIFICATION_TYPES.items():
            enabled = prefs.get(ntype, info["default_enabled"])
            status = "✅" if enabled else "❌"
            msg += f"{status} *{info['name']}*\n"
            msg += f"   _{info['description']}_\n"
            msg += f"   📅 {info['frequency']}\n\n"
            
            # Toggle button
            action = "off" if enabled else "on"
            btn_text = f"{status} {info['name']}"
            buttons.append((btn_text, f"notif_{ntype}_{action}"))
        
        # Add buttons in pairs
        button_rows = []
        for i in range(0, len(buttons), 2):
            row = buttons[i:i+2]
            button_rows.append(row)
        
        button_rows.append([("✅ Activar todas", "notif_all_on"), ("❌ Desactivar todas", "notif_all_off")])
        button_rows.append([("📊 Ver próximas notificaciones", "notif_schedule")])
        
        await update.message.reply_text(
            msg,
            parse_mode='Markdown',
            reply_markup=self._kb(button_rows)
        )
    
    # ============== GAMIFICATION COMMANDS ==============
    
    async def _cmd_level(self, update, context):
        """Muestra el nivel actual y progreso"""
        user_id = update.effective_user.id
        engine = get_game_engine()
        
        progress = engine.get_progress_display(user_id)
        
        await update.message.reply_text(
            progress,
            parse_mode='Markdown',
            reply_markup=self._kb([
                ("💳 Ver precios", "game_prices"),
                ("📄 Ver entregables", "game_deliverables"),
            ])
        )
    
    async def _cmd_diagnostic(self, update, context):
        """Inicia el proceso de diagnóstico"""
        user_id = update.effective_user.id
        engine = get_game_engine()
        
        can_start, msg = engine.can_start_diagnostic(user_id)
        
        if can_start:
            await update.message.reply_text(
                "🔍 *DIAGNÓSTICO DE VIABILIDAD*\n\n"
                "Evaluaremos tu perfil completo para determinar:\n\n"
                "• Si eres viable para migrar\n"
                "• Tu probabilidad de éxito\n"
                "• Las mejores opciones de visa\n"
                "• Plan de acción personalizado\n\n"
                f"💰 *Costo:* $50 USD\n\n"
                "¿Listo para comenzar?",
                parse_mode='Markdown',
                reply_markup=self._kb([
                    ("✅ Sí, pagar $50", "pay_diagnostic"),
                    ("❓ Más información", "game_info_diagnostic"),
                ])
            )
        else:
            await update.message.reply_text(f"⚠️ {msg}")
    
    async def _cmd_prices(self, update, context):
        """Muestra los precios de MigPAL"""
        await update.message.reply_text(
            get_prices_summary(),
            parse_mode='Markdown',
            reply_markup=self._kb([
                ("🔍 Iniciar diagnóstico", "pay_diagnostic"),
                ("🎮 Ver mi nivel", "game_level"),
            ])
        )
    
    async def _cmd_pay(self, update, context):
        """Muestra opciones de pago"""
        user_id = update.effective_user.id
        engine = get_game_engine()
        state = engine.get_state(user_id)
        
        # Determinar qué debe pagar
        current_level = Level(state.current_level)
        
        if current_level == Level.CONSULTAS:
            payment_type = "diagnostic"
            amount = 50
            next_level = "Diagnóstico"
        elif current_level == Level.DIAGNOSTICO and state.is_viable:
            payment_type = "approval"
            amount = 50
            next_level = "Aprobación"
        elif current_level == Level.APROBACION:
            payment_type = "plan"
            amount = 900
            next_level = "Plan Completo"
        else:
            await update.message.reply_text(
                "✅ No tienes pagos pendientes.\n\n"
                "Usa /nivel para ver tu progreso."
            )
            return
        
        await update.message.reply_text(
            f"💳 *PAGAR: {next_level}*\n\n"
            f"Monto: *${amount} USD*\n\n"
            "Selecciona tu método de pago:",
            parse_mode='Markdown',
            reply_markup=self._kb([
                [("💳 Tarjeta", f"pay_stripe_{payment_type}"), ("🅿️ PayPal", f"pay_paypal_{payment_type}")],
                [("📱 Zelle", f"pay_zelle_{payment_type}"), ("🏦 Transferencia", f"pay_bank_{payment_type}")],
            ])
        )
    
    async def _cmd_payments(self, update, context):
        """Muestra historial de pagos"""
        user_id = update.effective_user.id
        pm = get_payment_manager()
        
        status = pm.get_payment_status_display(user_id)
        
        await update.message.reply_text(
            status,
            parse_mode='Markdown'
        )
    
    async def _cmd_deliverables(self, update, context):
        """Muestra estado de entregables"""
        user_id = update.effective_user.id
        engine = get_game_engine()
        
        status = engine.get_deliverables_status(user_id)
        
        await update.message.reply_text(
            status,
            parse_mode='Markdown'
        )
    
    async def _cmd_refund(self, update, context):
        """Solicita devolución"""
        user_id = update.effective_user.id
        engine = get_game_engine()
        
        can_refund, msg, amount = engine.can_request_refund(user_id)
        
        if can_refund:
            await update.message.reply_text(
                f"💸 *SOLICITAR DEVOLUCIÓN*\n\n"
                f"Monto a devolver: *${amount} USD*\n\n"
                "⚠️ *No aplica devolución si:*\n"
                "• Ocultaste antecedentes penales\n"
                "• Proporcionaste información falsa\n"
                "• Falsificaste documentos\n\n"
                "¿Confirmas que quieres solicitar la devolución?",
                parse_mode='Markdown',
                reply_markup=self._kb([
                    ("✅ Sí, solicitar devolución", "refund_confirm"),
                    ("❌ No, continuar proceso", "refund_cancel"),
                ])
            )
        else:
            await update.message.reply_text(f"⚠️ {msg}")
    
    # ============== V2.0 COMMANDS - EXPLORATION & FLOW ==============
    
    @safe_async_handler
    async def _cmd_explore(self, update, context):
        """Explorar ciudades con scoring personalizado"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        route = user.get("selected_route", {})
        
        # Obtener estado seleccionado o mostrar opciones
        selected_state = route.get("state", "")
        
        if not selected_state:
            # Mostrar estados populares para explorar
            await update.message.reply_text(
                "🗺️ *EXPLORAR CIUDADES*\n\n"
                "Selecciona un estado para explorar sus ciudades:\n\n"
                "🌴 *Costa Este:*",
                parse_mode='Markdown',
                reply_markup=self._kb([
                    [("🌴 Florida", "explore_FL"), ("🗽 New York", "explore_NY")],
                    [("🏛️ New Jersey", "explore_NJ"), ("🦀 Maryland", "explore_MD")],
                ])
            )
            await update.message.reply_text(
                "🌵 *Costa Oeste y Sur:*",
                parse_mode='Markdown',
                reply_markup=self._kb([
                    [("☀️ California", "explore_CA"), ("🤠 Texas", "explore_TX")],
                    [("🌵 Arizona", "explore_AZ"), ("🎰 Nevada", "explore_NV")],
                ])
            )
            await update.message.reply_text(
                "🏔️ *Centro y Norte:*",
                parse_mode='Markdown',
                reply_markup=self._kb([
                    [("🌽 Illinois", "explore_IL"), ("🏈 Georgia", "explore_GA")],
                    [("🎸 Tennessee", "explore_TN"), ("🌲 Washington", "explore_WA")],
                    [("🔍 Buscar por nombre", "explore_search")],
                ])
            )
            return
        
        # Si ya tiene estado, mostrar ciudades de ese estado
        await self._show_cities_for_state(update, user_id, selected_state)
    
    async def _show_cities_for_state(self, update, user_id: int, state_code: str):
        """Muestra ciudades de un estado con scoring"""
        from app.services.knowledge_base.cities_database import CITIES_DATABASE
        
        # Filtrar ciudades del estado
        state_cities = [
            city for city_id, city in CITIES_DATABASE.items()
            if city.get("state_code") == state_code
        ]
        
        if not state_cities:
            await update.message.reply_text(
                f"⚠️ No tenemos ciudades registradas para {state_code}.\n"
                "Usa /explorar para ver otros estados."
            )
            return
        
        # Calcular scores para cada ciudad
        scored_cities = []
        for city in state_cities:
            # Crear scores basados en datos de la ciudad
            city_scores = {
                "costo_vida": 100 - min(100, (city.get("cost_of_living_index", 100) - 70)),
                "seguridad": 100 - city.get("crime_index", 50),
                "oportunidades": min(100, city.get("median_income", 50000) / 1000),
                "educacion": city.get("school_rating", 5) * 10,
                "salud": city.get("healthcare_score", 70),
                "transporte": city.get("transit_score", 30),
                "comunidad_latina": min(100, city.get("latino_pct", 10) * 2),
                "clima": 70,  # Default
                "calidad_vida": city.get("quality_of_life_score", 70),
            }
            
            total, breakdown = scoring_engine.calculate_score(user_id, "location", city_scores)
            scored_cities.append({
                "city": city,
                "score": total,
                "breakdown": breakdown
            })
        
        # Ordenar por score
        scored_cities.sort(key=lambda x: x["score"], reverse=True)
        
        # Guardar en contexto del usuario para navegación
        user = get_user_data(user_id)
        user["exploration"] = {
            "type": "cities",
            "state": state_code,
            "items": scored_cities,
            "current_index": 0
        }
        save_user_data(user_id, encrypt_user_data(user))
        
        # Mostrar primera ciudad
        await self._show_exploration_item(update, user_id, 0)
    
    async def _show_exploration_item(self, update_or_query, user_id: int, index: int):
        """Muestra un item de exploración (ciudad, vivienda, etc.)"""
        user = get_user_data(user_id)
        exploration = user.get("exploration", {})
        items = exploration.get("items", [])
        
        if not items or index >= len(items):
            msg = "✅ Has visto todas las opciones.\n\n¿Qué quieres hacer?"
            kb = self._kb([
                ("🔄 Ver de nuevo", "explore_restart"),
                ("✅ Elegir favorita", "explore_select"),
            ])
            if hasattr(update_or_query, 'message'):
                await update_or_query.message.reply_text(msg, reply_markup=kb)
            else:
                await update_or_query.edit_message_text(msg, reply_markup=kb)
            return
        
        item = items[index]
        exploration["current_index"] = index
        user["exploration"] = exploration
        save_user_data(user_id, encrypt_user_data(user))
        
        if exploration.get("type") == "cities":
            city = item["city"]
            score = item["score"]
            
            # Generar estrellas
            stars = "⭐" * min(5, int(score / 20))
            
            msg = f"🏙️ *{city.get('name')}, {city.get('state_code')}*\n"
            msg += f"{stars} Score: {score:.1f}/100\n\n"
            msg += f"👥 Población: {city.get('population', 0):,}\n"
            msg += f"💰 Ingreso medio: ${city.get('median_income', 0):,}/año\n"
            msg += f"🏠 Renta 2BR: ${city.get('median_rent_2br', 0):,}/mes\n"
            msg += f"🛡️ Seguridad: {100 - city.get('crime_index', 50)}/100\n"
            msg += f"🤝 Comunidad latina: {city.get('latino_pct', 0):.1f}%\n"
            msg += f"🎓 Escuelas: {city.get('school_rating', 0)}/10\n\n"
            
            if city.get("description"):
                msg += f"📝 {city.get('description')[:200]}...\n\n"
            
            msg += f"📍 {index + 1} de {len(items)} ciudades"
            
            kb = self._kb([
                [("⬅️ Anterior", f"explore_prev_{index}"), ("➡️ Siguiente", f"explore_next_{index}")],
                [("❤️ Me gusta", f"explore_like_{city.get('id')}"), ("ℹ️ Más info", f"explore_info_{city.get('id')}")],
                [("✅ Elegir esta ciudad", f"explore_select_{city.get('id')}")],
            ])
        else:
            # Para viviendas u otros tipos
            msg = f"🏠 Item {index + 1} de {len(items)}"
            kb = self._kb([
                [("⬅️ Anterior", f"explore_prev_{index}"), ("➡️ Siguiente", f"explore_next_{index}")],
            ])
        
        if hasattr(update_or_query, 'message'):
            await update_or_query.message.reply_text(msg, parse_mode='Markdown', reply_markup=kb)
        else:
            await update_or_query.edit_message_text(msg, parse_mode='Markdown', reply_markup=kb)
    
    @safe_async_handler
    async def _cmd_housing(self, update, context):
        """Buscar viviendas con Zillow"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        route = user.get("selected_route", {})
        
        city = route.get("city", "")
        state = route.get("state", "")
        
        if not city or not state:
            await update.message.reply_text(
                "🏠 *BÚSQUEDA DE VIVIENDAS*\n\n"
                "Primero necesitas seleccionar una ciudad.\n\n"
                "Usa /explorar para elegir tu ciudad destino,\n"
                "o escríbeme el nombre de la ciudad que te interesa.",
                parse_mode='Markdown',
                reply_markup=self._kb([
                    ("🗺️ Explorar ciudades", "cmd_explore"),
                    ("🔍 Buscar ciudad", "housing_search_city"),
                ])
            )
            return
        
        await update.message.reply_text(
            f"🏠 *VIVIENDAS EN {city.upper()}, {state}*\n\n"
            "🔍 Buscando opciones de renta...\n\n"
            "_Esto puede tomar unos segundos..._",
            parse_mode='Markdown'
        )
        
        try:
            from app.services.zillow import fetch_city_listings
            
            listings = fetch_city_listings(city, state)
            
            if not listings:
                await update.message.reply_text(
                    f"⚠️ No encontramos listados activos en {city}, {state}.\n\n"
                    "Esto puede ser porque:\n"
                    "• La ciudad tiene pocos listados\n"
                    "• Zillow bloqueó temporalmente las consultas\n\n"
                    "💡 *Alternativas:*\n"
                    "• Visita zillow.com directamente\n"
                    "• Prueba con una ciudad cercana",
                    parse_mode='Markdown'
                )
                return
            
            # Calcular scores para cada vivienda
            scored_listings = []
            for listing in listings[:10]:  # Limitar a 10
                housing_scores = {
                    "precio": self._price_score(listing.get("price", 0), user),
                    "ubicacion": 70,  # Default
                    "tamano": self._size_score(listing.get("area", 0), listing.get("beds", 0)),
                    "amenidades": 60,  # Default
                    "seguridad_barrio": 70,  # Default
                    "cercania_trabajo": 50,  # Default
                    "cercania_escuelas": 50,  # Default
                }
                
                total, breakdown = scoring_engine.calculate_score(user_id, "housing", housing_scores)
                scored_listings.append({
                    "listing": listing,
                    "score": total,
                    "breakdown": breakdown
                })
            
            # Ordenar por score
            scored_listings.sort(key=lambda x: x["score"], reverse=True)
            
            # Mostrar resultados
            msg = f"🏠 *{len(scored_listings)} VIVIENDAS EN {city.upper()}*\n\n"
            
            for i, item in enumerate(scored_listings[:5], 1):
                listing = item["listing"]
                score = item["score"]
                stars = "⭐" * min(5, int(score / 20))
                
                price = listing.get("price", 0)
                beds = listing.get("beds", "?")
                baths = listing.get("baths", "?")
                address = listing.get("address", "Dirección no disponible")
                
                msg += f"{i}. {stars} *${price:,}/mes*\n"
                msg += f"   🛏️ {beds} hab | 🚿 {baths} baños\n"
                msg += f"   📍 {address[:40]}...\n"
                if listing.get("detail_url"):
                    msg += f"   🔗 [Ver en Zillow]({listing.get('detail_url')})\n"
                msg += "\n"
            
            msg += "\n💡 _Usa los botones para ver más detalles_"
            
            # Guardar para navegación
            user["exploration"] = {
                "type": "housing",
                "city": city,
                "state": state,
                "items": scored_listings,
                "current_index": 0
            }
            save_user_data(user_id, encrypt_user_data(user))
            
            await update.message.reply_text(
                msg,
                parse_mode='Markdown',
                disable_web_page_preview=True,
                reply_markup=self._kb([
                    [("🔄 Actualizar", "housing_refresh"), ("📊 Ajustar filtros", "housing_filters")],
                    [("❤️ Ver favoritos", "housing_favorites")],
                ])
            )
            
        except Exception as e:
            logger.error(f"Error fetching Zillow listings: {e}")
            await update.message.reply_text(
                "⚠️ Error al buscar viviendas.\n\n"
                f"Detalles: {str(e)[:100]}\n\n"
                "Por favor intenta de nuevo más tarde."
            )
    
    def _price_score(self, price: int, user: dict) -> int:
        """Calcula score de precio basado en presupuesto del usuario"""
        budget = user.get("preferences", {}).get("housing_budget", 2500)
        if price <= budget * 0.7:
            return 100
        elif price <= budget:
            return 80
        elif price <= budget * 1.2:
            return 60
        elif price <= budget * 1.5:
            return 40
        else:
            return 20
    
    def _size_score(self, sqft: int, beds: int) -> int:
        """Calcula score de tamaño"""
        if sqft >= 1500 or beds >= 3:
            return 90
        elif sqft >= 1000 or beds >= 2:
            return 70
        elif sqft >= 700 or beds >= 1:
            return 50
        else:
            return 30
    
    @safe_async_handler
    async def _cmd_flow(self, update, context):
        """Inicia o continúa el flujo conversacional guiado"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        
        # Obtener contexto del flujo
        ctx = flow_engine.get_context(user_id)
        current_state = ctx.current_state
        
        # Obtener pregunta del estado actual
        question_data = STATE_QUESTIONS.get(current_state, {})
        
        if not question_data:
            await update.message.reply_text(
                "🎯 *FLUJO DE MIGRACIÓN*\n\n"
                "¡Vamos a construir tu plan de migración paso a paso!\n\n"
                "Este proceso te guiará para:\n"
                "1️⃣ Entender tu motivación\n"
                "2️⃣ Definir tu plan de vida\n"
                "3️⃣ Elegir la mejor ubicación\n"
                "4️⃣ Encontrar la visa adecuada\n\n"
                "¿Listo para empezar?",
                parse_mode='Markdown',
                reply_markup=self._kb([
                    ("✅ ¡Sí, empecemos!", "flow_start"),
                    ("ℹ️ Más información", "flow_info"),
                ])
            )
            return
        
        # Formatear mensaje con datos del usuario
        name = user.get("profile", {}).get("personal", {}).get("name", "")
        message = question_data.get("message", "").format(
            name=name or "amigo",
            why_migrate_text=ctx.why_migrate or "tu motivación"
        )
        
        # Crear botones de opciones
        options = question_data.get("options", [])
        if options:
            buttons = [(opt[1], f"flow_{opt[0]}") for opt in options]
            kb = self._kb(buttons)
        else:
            kb = None
        
        progress = flow_engine.get_progress_percentage(user_id)
        
        await update.message.reply_text(
            f"📊 Progreso: {progress}%\n\n{message}",
            parse_mode='Markdown',
            reply_markup=kb
        )
    
    async def _send_notification_message(self, user_id: int, message: str, parse_mode: str = None):
        """Send a notification message to a user via Telegram"""
        if not self.application:
            logger.warning("Application not initialized")
            return
        
        try:
            await self.application.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=parse_mode or 'Markdown'
            )
            logger.debug(f"Notification sent to {user_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to {user_id}: {e}")
    
    # ============== CALLBACK HANDLER ==============
    
    @global_error_handler
    async def _handle_callback(self, update, context):
        # ============== SEGMENTO 2/4: NEVER SILENT WRAPPER ==============
        # REGLA: El bot NUNCA se queda callado. SIEMPRE responde.
        never_silent_wrapper = get_never_silent()
        health_check = get_health_check()
        health_check.record_update()  # Registrar actividad para healthcheck
        
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data if query.data else ""
        state = get_state(user_id)
        user = get_user_data(user_id)
        lang = user.get("language", "es")  # Default español para MigPAL
        
        # ============== SEGMENTO 1/3: DISPONIBILIDAD GARANTIZADA ==============
        # REGLA: Todo callback DEBE generar respuesta. NUNCA quedarse callado.
        
        # 1. Registrar input para tracking de respuesta
        response_tracker = get_response_tracker()
        response_tracker.record_input(user_id, "callback", data[:50])
        
        # 2. Iniciar watchdog de 3 segundos
        watchdog = get_watchdog()
        
        async def send_watchdog_message(msg: str):
            try:
                await query.message.reply_text(msg)
            except Exception as e:
                logger.error(f"Watchdog send failed: {e}")
        
        # V4.2.1: Pasar estado actual para deshabilitar watchdog en estados con IA intensiva
        current_state = get_state(user_id)
        await watchdog.start_watchdog(user_id, send_watchdog_message, lang, current_state)
        
        # Anti-spam: solo procesar si pasó suficiente tiempo desde el último click
        if not should_process_click(user_id):
            logger.debug(f"Ignoring spam click from {user_id}")
            watchdog.mark_response_sent(user_id)
            return
        
        # V3.0.3 - Enhanced logging
        transition_logger = get_transition_logger()
        transition_logger.log_callback_received(user_id, state, data)
        
        # V3.0.3 - Record activity for stall detection
        stall_detector = get_stall_detector()
        stall_detector.record_activity(user_id, state, data)
        
        # V3.0.3 - Handle stall callbacks
        if data == "stall_continue":
            # User wants to continue - just acknowledge
            await query.edit_message_text(
                get_text("continue_where_left", lang) if lang != "en" else "▶️ Continuing...",
                parse_mode='Markdown'
            )
            watchdog.mark_response_sent(user_id)
            response_tracker.record_response(user_id)
            return
        elif data == "stall_restart":
            # User wants to restart current phase
            current_phase = ProgressTracker.get_current_phase(state)
            if current_phase and current_phase in PHASES:
                first_state = PHASES[current_phase]["states"][0]
                set_state(user_id, first_state)
                await query.edit_message_text(
                    f"🔄 {get_text('restart_phase', lang)}\n\n" +
                    ProgressTracker.format_progress_header(user, first_state, lang),
                    parse_mode='Markdown'
                )
            watchdog.mark_response_sent(user_id)
            response_tracker.record_response(user_id)
            return
        
        logger.info(f"CB: {user_id} | {state} | {data}")
        
        # ===== v3.0.6: ONBOARDING CALLBACKS =====
        if data.startswith("onboarding_"):
            from app.services.onboarding_v306 import get_onboarding_engine, OnboardingState
            engine = get_onboarding_engine()
            
            if data == "onboarding_yes":
                # Usuario acepta empezar - PASO 6: Pedir nombre
                set_state(user_id, OnboardingState.NAME_REQUEST.value)
                name_request = engine.get_name_request(lang)
                await query.edit_message_text(name_request)
                watchdog.mark_response_sent(user_id)
                return
            
            elif data == "onboarding_questions":
                # Usuario tiene más preguntas
                set_state(user_id, OnboardingState.LISTENING.value)
                response = engine.get_more_questions_response(lang)
                await query.edit_message_text(response)
                watchdog.mark_response_sent(user_id)
                return
            
            elif data == "onboarding_later":
                # Usuario quiere continuar después
                response = engine.get_later_response(lang)
                await query.edit_message_text(response)
                watchdog.mark_response_sent(user_id)
                return
        
        # ===== MULTI-SELECT HANDLERS =====
        if data.startswith("ms_"):
            await self._handle_multi_select(query, user_id, data, user)
            watchdog.mark_response_sent(user_id)
            return
        
        # ===== EXPERTISE MULTI-SELECT =====
        if data.startswith("exp_"):
            await self._handle_expertise_select(query, user_id, data, user)
            watchdog.mark_response_sent(user_id)
            return
        
        # ===== LOGROS MULTI-SELECT =====
        if data.startswith("logro_"):
            await self._handle_logros_select(query, user_id, data, user)
            watchdog.mark_response_sent(user_id)
            return
        
        # ===== PLAN DE MIGRACIÓN =====
        if data.startswith("plan_"):
            await self._handle_migration_plan(query, user_id, data, user)
            watchdog.mark_response_sent(user_id)
            return
        
        # ===== CIUDAD SELECCIONADA =====
        if data.startswith("city_"):
            await self._handle_city_selection(query, user_id, data, user)
            watchdog.mark_response_sent(user_id)
            return
        
        # ===== INVESTIGACIÓN (VIVIENDAS, EMPLEOS, COLEGIOS, NEGOCIOS) =====
        if data.startswith("research_"):
            await self._handle_research(query, user_id, data, user)
            watchdog.mark_response_sent(user_id)
            return
        
        # ===== SEGMENTO 3/3: HANDLERS DE CONFIRMACIÓN DE RESUMEN =====
        if data.startswith("confirm_summary_"):
            action = data.replace("confirm_summary_", "")
            
            if action == "yes":
                # Usuario confirmó el resumen - marcar perfil como validado
                if "confirmations" not in user:
                    user["confirmations"] = []
                user["confirmations"].append({
                    "summary_type": "profile",
                    "confirmed": True,
                    "timestamp": datetime.now().isoformat()
                })
                save_user_data(user_id, user)
                
                # Confirmar correcciones pendientes
                correction_tracker = get_correction_tracker()
                correction_tracker.confirm_corrections(user_id)
                
                await query.edit_message_text(
                    "✅ *¡Perfecto!* Información confirmada.\n\n"
                    "Ahora puedo darte recomendaciones personalizadas.\n\n"
                    "¿Qué te gustaría explorar?",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("🎯 Ver recomendación de visa", "show_visa_recommendation")],
                        [("🏙️ Explorar ciudades", "explore_cities")],
                        [("💼 Buscar empleos", "cmd_jobs")],
                        [("🏠 Buscar viviendas", "cmd_housing")]
                    ])
                )
                watchdog.mark_response_sent(user_id)
                return
            
            elif action == "no":
                # Usuario quiere corregir algo
                await query.edit_message_text(
                    "✏️ *¿Qué necesitas corregir?*\n\n"
                    "Escríbeme qué información está incorrecta y la actualizo.",
                    parse_mode='Markdown'
                )
                watchdog.mark_response_sent(user_id)
                return
            
            elif action == "add":
                # Usuario quiere agregar más información
                # Obtener siguiente pregunta de vida deseada
                next_question = get_next_life_question(user, lang)
                if next_question:
                    await query.edit_message_text(
                        f"🌟 *Entendamos mejor tu sueño*\n\n{next_question}",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(
                        "Cuéntame más sobre ti o tus planes. ¿Qué más te gustaría que supiera?",
                        parse_mode='Markdown'
                    )
                watchdog.mark_response_sent(user_id)
                return
        
        # ===== SHOW UNDERSTANDING SUMMARY =====
        if data == "show_summary" or data == "show_understanding":
            summary_text, summary_buttons = generate_understanding_summary(user, lang)
            await query.edit_message_text(
                summary_text,
                parse_mode='Markdown',
                reply_markup=self._kb(summary_buttons)
            )
            watchdog.mark_response_sent(user_id)
            return
        
        # ===== SHOW VISA RECOMMENDATION (con validación) =====
        if data == "show_visa_recommendation":
            # SEGMENTO 3/3: Verificar si se puede tomar esta decisión
            can_decide, reason, next_action = can_make_decision(user, "visa_recommendation")
            
            if not can_decide:
                if next_action == "show_summary":
                    summary_text, summary_buttons = generate_understanding_summary(user, lang)
                    await query.edit_message_text(
                        f"⚠️ {reason}\n\n{summary_text}",
                        parse_mode='Markdown',
                        reply_markup=self._kb(summary_buttons)
                    )
                else:
                    await query.edit_message_text(
                        f"⚠️ {reason}",
                        parse_mode='Markdown'
                    )
                watchdog.mark_response_sent(user_id)
                return
            
            # Perfil validado - mostrar recomendación
            # (continuar con el flujo normal de visa)
        
        # ===== START =====
        if data == "begin":
            set_state(user_id, STATE_NAME)
            await query.edit_message_text(
                "📝 *FASE 1: Tu Perfil*\n\n"
                "¿Cuál es tu nombre completo?",
                parse_mode='Markdown'
            )
        
        # ===== NATIONALITY =====
        elif state == STATE_NATIONALITY:
            user["profile"]["personal"]["nationality"] = data
            set_state(user_id, STATE_CURRENT_COUNTRY)
            await query.edit_message_text(
                "¿En qué país vives actualmente?",
                reply_markup=self._kb([
                    [("🇨🇴 Colombia", "Colombia"), ("🇲🇽 México", "México")],
                    [("🇻🇪 Venezuela", "Venezuela"), ("🇦🇷 Argentina", "Argentina")],
                    [("🇵🇪 Perú", "Perú"), ("🇪🇨 Ecuador", "Ecuador")],
                    [("🌎 Otro", "Otro")]
                ])
            )
        
        # ===== CURRENT COUNTRY =====
        elif state == STATE_CURRENT_COUNTRY:
            user["profile"]["personal"]["current_country"] = data
            set_state(user_id, STATE_CURRENT_CITY)
            await query.edit_message_text(f"¿En qué ciudad de {data} vives?")
        
        # ===== EDUCATION LEVEL =====
        elif state == STATE_EDUCATION_LEVEL:
            user["profile"]["education"]["level"] = data
            set_state(user_id, STATE_EDUCATION_STATUS)
            await query.edit_message_text(
                "¿Ya terminaste tus estudios o estás cursando?",
                reply_markup=self._kb([
                    ("✅ Ya terminé", "Terminado"),
                    ("📖 Estoy cursando", "Cursando"),
                    ("⏸️ Pausado/Incompleto", "Incompleto")
                ])
            )
        
        # ===== EDUCATION STATUS =====
        elif state == STATE_EDUCATION_STATUS:
            user["profile"]["education"]["status"] = data
            set_state(user_id, STATE_EDUCATION_FIELD)
            await query.edit_message_text(
                "¿En qué área es tu formación?\n\n"
                "💡 Puedes seleccionar varias si aplica:",
                reply_markup=self._kb([
                    [("💻 Tecnología", "Tecnología"), ("🏥 Salud", "Salud")],
                    [("📊 Negocios", "Negocios"), ("⚖️ Derecho", "Derecho")],
                    [("🔧 Ingeniería", "Ingeniería"), ("🎨 Artes", "Artes")],
                    [("📚 Educación", "Educación"), ("📝 Otro", "Otro")]
                ])
            )
        
        # ===== EDUCATION FIELD =====
        elif state == STATE_EDUCATION_FIELD:
            user["profile"]["education"]["field"] = data
            set_state(user_id, STATE_EDUCATION_CAREER)
            await query.edit_message_text(
                "¿Qué carrera o título tienes/estudias?\n\n"
                "Escribe el nombre (ej: Ingeniería de Sistemas, Medicina, Administración...)"
            )
        
        # ===== EDUCATION CAREER ===== (handled in message handler)
        
        # ===== WORK STATUS =====
        elif state == STATE_WORK_STATUS:
            user["profile"]["work"]["status"] = data
            set_state(user_id, STATE_PROFESSION)
            await query.edit_message_text("¿Cuál es tu profesión u ocupación?")
        
        # ===== WORK EXPERIENCE =====
        elif state == STATE_WORK_EXPERIENCE:
            user["profile"]["work"]["experience"] = data
            set_state(user_id, STATE_ENGLISH_LEVEL)
            await query.edit_message_text(
                "🌐 ¿Cuál es tu nivel de inglés?",
                reply_markup=self._kb([
                    ("🔴 Ninguno", "Ninguno"),
                    ("🟠 Básico (A1-A2)", "Básico"),
                    ("🟡 Intermedio (B1-B2)", "Intermedio"),
                    ("🟢 Avanzado (C1-C2)", "Avanzado"),
                    ("🔵 Nativo", "Nativo")
                ])
            )
        
        # ===== ENGLISH LEVEL =====
        elif state == STATE_ENGLISH_LEVEL:
            user["profile"]["languages"]["english"] = data
            set_state(user_id, STATE_LINKEDIN)
            await query.edit_message_text(
                "📱 *Perfil Profesional*\n\n"
                "Comparte tu LinkedIn o CV para conocer mejor tu experiencia.\n\n"
                "Puedes:\n"
                "• Pegar tu URL de LinkedIn\n"
                "• Enviar tu CV como archivo\n"
                "• Escribir 'Omitir' si prefieres no compartir",
                parse_mode='Markdown'
            )
        
        # ===== VISA HISTORY =====
        elif state == STATE_VISA_HISTORY:
            user["profile"]["history"]["has_visas"] = data
            if data == "Sí":
                set_state(user_id, STATE_VISA_DETAILS)
                await query.edit_message_text(
                    "¿Qué visas has tenido?\n"
                    "(ej: USA B1/B2, Schengen, etc.)"
                )
            else:
                user["profile"]["history"]["visas"] = "Ninguna"
                set_state(user_id, STATE_VISA_REJECTIONS)
                await query.edit_message_text(
                    "¿Has tenido algún rechazo de visa?",
                    reply_markup=self._kb([
                        ("❌ No, nunca", "No"),
                        ("⚠️ Sí", "Sí")
                    ])
                )
        
        # ===== VISA REJECTIONS =====
        elif state == STATE_VISA_REJECTIONS:
            user["profile"]["history"]["rejections"] = data
            set_state(user_id, STATE_CRIMINAL_RECORD)
            await query.edit_message_text(
                "⚖️ ¿Tienes antecedentes penales?",
                reply_markup=self._kb([
                    ("✅ No", "No"),
                    ("⚠️ Sí", "Sí")
                ])
            )
        
        # ===== CRIMINAL RECORD =====
        elif state == STATE_CRIMINAL_RECORD:
            user["profile"]["history"]["criminal"] = data
            set_state(user_id, STATE_HEALTH_CONDITIONS)
            await query.edit_message_text(
                "🏥 ¿Tienes condiciones médicas importantes?",
                reply_markup=self._kb([
                    ("✅ No", "No"),
                    ("⚠️ Sí", "Sí")
                ])
            )
        
        # ===== HEALTH =====
        elif state == STATE_HEALTH_CONDITIONS:
            user["profile"]["history"]["health"] = data
            set_state(user_id, STATE_SAVINGS)
            await query.edit_message_text(
                "💰 ¿Cuánto tienes disponible para el proceso?",
                reply_markup=self._kb([
                    [("< $5,000", "<5k"), ("$5k-$15k", "5k-15k")],
                    [("$15k-$30k", "15k-30k"), ("$30k-$50k", "30k-50k")],
                    [("$50k-$100k", "50k-100k"), ("> $100k", ">100k")]
                ])
            )
        
        # ===== SAVINGS =====
        elif state == STATE_SAVINGS:
            user["profile"]["financial"]["savings"] = data
            set_state(user_id, STATE_FAMILY_STATUS)
            await query.edit_message_text(
                "👨‍👩‍👧‍👦 *FASE 2: Familia*\n\n"
                "¿Migrarías solo o con familia?",
                parse_mode='Markdown',
                reply_markup=self._kb([
                    ("👤 Solo/a", "Solo"),
                    ("👫 Con pareja", "Pareja"),
                    ("👨‍👩‍👧 Con familia", "Familia")
                ])
            )
        
        # ===== FAMILY STATUS =====
        elif state == STATE_FAMILY_STATUS:
            user["preferences"]["family_status"] = data
            if data == "Solo":
                set_state(user_id, STATE_MIGRATION_REASON)
                await self._ask_migration_reason(query)
            else:
                set_state(user_id, STATE_FAMILY_COUNT)
                await query.edit_message_text(
                    "¿Cuántas personas en total (incluyéndote)?",
                    reply_markup=self._kb([
                        [("2", "2"), ("3", "3"), ("4", "4")],
                        [("5", "5"), ("6+", "6")]
                    ])
                )
        
        # ===== FAMILY COUNT =====
        elif state == STATE_FAMILY_COUNT:
            count = int(data)
            user["preferences"]["family_count"] = count
            user["family_members"] = []
            user["current_family_index"] = 0
            set_state(user_id, STATE_FAMILY_MEMBER_RELATION)
            await query.edit_message_text(
                f"📝 *Familiar 1 de {count-1}*\n\n"
                "¿Cuál es la relación?",
                parse_mode='Markdown',
                reply_markup=self._kb([
                    [("💑 Esposo/a", "Esposo/a"), ("💕 Pareja", "Pareja")],
                    [("👦 Hijo/a", "Hijo/a"), ("👨 Padre/Madre", "Padre/Madre")]
                ])
            )
        
        # ===== FAMILY MEMBER RELATION =====
        elif state == STATE_FAMILY_MEMBER_RELATION:
            user["family_members"].append({"relation": data})
            set_state(user_id, STATE_FAMILY_MEMBER_NAME)
            await query.edit_message_text(f"¿Nombre completo de tu {data.lower()}?")
        
        # ===== FAMILY MEMBER EDUCATION =====
        elif state == STATE_FAMILY_MEMBER_EDUCATION:
            idx = user["current_family_index"]
            user["family_members"][idx]["education"] = data
            relation = user["family_members"][idx].get("relation", "")
            name = user["family_members"][idx]["name"]
            
            # If studying, ask what they're studying
            if data in ["Primaria", "Secundaria", "Universidad", "Preescolar"]:
                set_state(user_id, STATE_FAMILY_MEMBER_STUDY_STATUS)
                if data == "Universidad":
                    await query.edit_message_text(
                        f"¿Qué está estudiando {name}?\n\n"
                        "Escribe la carrera (ej: Medicina, Derecho, Ingeniería...)"
                    )
                else:
                    set_state(user_id, STATE_FAMILY_MEMBER_ENGLISH)
                    await query.edit_message_text(
                        f"¿Nivel de inglés de {name}?",
                        reply_markup=self._kb([
                            [("🔴 Ninguno", "Ninguno"), ("🟠 Básico", "Básico")],
                            [("🟡 Intermedio", "Intermedio"), ("🟢 Avanzado", "Avanzado")]
                        ])
                    )
            else:
                set_state(user_id, STATE_FAMILY_MEMBER_ENGLISH)
                await query.edit_message_text(
                    f"¿Nivel de inglés de {name}?",
                    reply_markup=self._kb([
                        [("🔴 Ninguno", "Ninguno"), ("🟠 Básico", "Básico")],
                        [("🟡 Intermedio", "Intermedio"), ("🟢 Avanzado", "Avanzado")]
                    ])
                )
        
        # ===== FAMILY MEMBER ENGLISH =====
        elif state == STATE_FAMILY_MEMBER_ENGLISH:
            idx = user["current_family_index"]
            user["family_members"][idx]["english"] = data
            
            # Check if more family members
            total = user["preferences"].get("family_count", 2) - 1
            if idx + 1 < total:
                user["current_family_index"] = idx + 1
                set_state(user_id, STATE_FAMILY_MEMBER_RELATION)
                await query.edit_message_text(
                    f"✅ ¡Registrado!\n\n"
                    f"📝 *Familiar {idx + 2} de {total}*\n\n"
                    "¿Cuál es la relación?",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("💑 Esposo/a", "Esposo/a"), ("💕 Pareja", "Pareja")],
                        [("👦 Hijo/a", "Hijo/a"), ("👨 Padre/Madre", "Padre/Madre")]
                    ])
                )
            else:
                set_state(user_id, STATE_MIGRATION_REASON)
                await query.edit_message_text(
                    "✅ *¡Familia registrada!*",
                    parse_mode='Markdown'
                )
                await query.message.reply_text(
                    "🎯 *FASE 3: Objetivos*\n\n"
                    "¿Principal razón para migrar?",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        ("💼 Trabajo", "Trabajo"),
                        ("📚 Estudios", "Estudios"),
                        ("🏠 Calidad de vida", "Calidad de vida"),
                        ("👨‍👩‍👧 Familia", "Familia"),
                        ("🔒 Seguridad", "Seguridad")
                    ])
                )
        
        # ===== MIGRATION REASON =====
        elif state == STATE_MIGRATION_REASON:
            user["preferences"]["reason"] = data
            set_state(user_id, STATE_TIMELINE)
            await query.edit_message_text(
                "⏰ ¿En qué plazo?",
                reply_markup=self._kb([
                    ("⚡ < 6 meses", "Urgente"),
                    ("📅 6-12 meses", "Mediano"),
                    ("🗓️ 1-2 años", "Largo"),
                    ("🤷 Flexible", "Flexible")
                ])
            )
        
        # ===== TIMELINE =====
        elif state == STATE_TIMELINE:
            user["preferences"]["timeline"] = data
            set_state(user_id, STATE_DESTINATION_PREFERENCE)
            await query.edit_message_text(
                "🌍 ¿País de destino?",
                reply_markup=self._kb([
                    [("🇺🇸 USA", "USA"), ("🇨🇦 Canadá", "Canadá")],
                    [("🇪🇸 España", "España"), ("🇩🇪 Alemania", "Alemania")],
                    [("🇦🇺 Australia", "Australia"), ("🤔 Abierto", "Abierto")]
                ])
            )
        
        # ===== DESTINATION =====
        elif state == STATE_DESTINATION_PREFERENCE:
            user["preferences"]["destination"] = data
            set_state(user_id, STATE_CLIMATE_PREFERENCE)
            await query.edit_message_text(
                "☀️ ¿Preferencia de clima?",
                reply_markup=self._kb([
                    [("🌴 Cálido", "Cálido"), ("🌤️ Templado", "Templado")],
                    [("❄️ Frío", "Frío"), ("🤷 No importa", "Indiferente")]
                ])
            )
        
        # ===== CLIMATE =====
        elif state == STATE_CLIMATE_PREFERENCE:
            user["preferences"]["climate"] = data
            set_state(user_id, STATE_CITY_SIZE_PREFERENCE)
            await query.edit_message_text(
                "🏙️ ¿Tamaño de ciudad?",
                reply_markup=self._kb([
                    [("🌆 Grande", "Grande"), ("🏙️ Mediana", "Mediana")],
                    [("🏘️ Pequeña", "Pequeña"), ("🤷 No importa", "Indiferente")]
                ])
            )
        
        # ===== CITY SIZE =====
        elif state == STATE_CITY_SIZE_PREFERENCE:
            user["preferences"]["city_size"] = data
            set_state(user_id, STATE_BUDGET_INITIAL)
            await query.edit_message_text(
                "💰 ¿Presupuesto inicial para el proceso?",
                reply_markup=self._kb([
                    [("$5k-$10k", "5k-10k"), ("$10k-$20k", "10k-20k")],
                    [("$20k-$40k", "20k-40k"), ("> $40k", ">40k")]
                ])
            )
        
        # ===== BUDGET =====
        elif state == STATE_BUDGET_INITIAL:
            user["preferences"]["budget"] = data
            set_state(user_id, STATE_SELECT_COUNTRY)
            await self._show_options(query, user_id)
        
        # ===== SELECT COUNTRY =====
        elif state == STATE_SELECT_COUNTRY:
            user["selected_route"]["country"] = data
            set_state(user_id, STATE_SELECT_VISA)
            
            # Show visa explanations first
            visa_info = self._get_visa_explanations(data, user)
            await query.edit_message_text(
                visa_info,
                parse_mode='Markdown'
            )
            
            # Then show selection buttons
            visas = self._get_visas(data)
            profile_intro = get_profile_based_intro(user_id, user, lang)
            await query.message.reply_text(
                f"👆 {profile_intro}, ¿cuál te interesa explorar?",
                reply_markup=self._kb(visas)
            )
        
        # ===== SELECT VISA =====
        elif state == STATE_SELECT_VISA:
            user["selected_route"]["visa_type"] = data
            set_state(user_id, STATE_SELECT_STATE)
            country = user["selected_route"]["country"]
            states = self._get_states(country)
            await query.edit_message_text(
                f"📍 ¿Estado/Región en {country}?",
                reply_markup=self._kb(states)
            )
        
        # ===== SELECT STATE =====
        elif state == STATE_SELECT_STATE:
            user["selected_route"]["state"] = data
            set_state(user_id, STATE_SELECT_CITY)
            cities = self._get_cities(data)
            await query.edit_message_text(
                f"🏙️ ¿Ciudad en {data}?",
                reply_markup=self._kb(cities)
            )
        
        # ===== SELECT CITY =====
        elif state == STATE_SELECT_CITY:
            user["selected_route"]["city"] = data
            set_state(user_id, STATE_HOUSING_TYPE)
            await query.edit_message_text(
                "🏠 ¿Tipo de vivienda inicial?",
                reply_markup=self._kb([
                    ("🏢 Apartamento", "Apartamento"),
                    ("🏠 Casa", "Casa"),
                    ("🛏️ Habitación", "Habitación"),
                    ("🏨 Temporal", "Temporal")
                ])
            )
        
        # ===== HOUSING =====
        elif state == STATE_HOUSING_TYPE:
            user["selected_route"]["housing"] = data
            set_state(user_id, STATE_DOCUMENT_UPLOAD)
            await self._show_documents(query, user_id)
        
        # ===== DOCUMENT ACTIONS =====
        elif data == "start_upload":
            set_state(user_id, STATE_DOCUMENT_UPLOAD)
            await query.edit_message_text(
                "📤 *Carga de Documentos*\n\n"
                "Envía tus documentos como:\n"
                "• 📷 Fotos\n"
                "• 📄 Archivos PDF/Word\n\n"
                "Cuando termines, escribe /listo",
                parse_mode='Markdown'
            )
        
        elif data == "skip_docs":
            set_state(user_id, STATE_CONSULTING)
            await query.edit_message_text(
                "✅ *¡Plan guardado!*\n\n"
                "Puedes enviar documentos después.\n\n"
                "¿En qué puedo ayudarte?",
                parse_mode='Markdown',
                reply_markup=self._kb([
                    ("📋 Requisitos", "req_visa"),
                    ("💰 Costos", "req_costs"),
                    ("⏱️ Tiempos", "req_time"),
                    ("💬 Pregunta", "ask_question")
                ])
            )
        
        # ===== CONSULTING =====
        elif data in ["req_visa", "req_costs", "req_time"]:
            response = await self._get_info(data, user)
            await query.edit_message_text(response, parse_mode='Markdown')
        
        elif data == "ask_question":
            await query.edit_message_text("💬 Escribe tu pregunta:")
        
        # ===== V2.0 EXPLORATION & FLOW CALLBACKS =====
        
        # Explore state callbacks
        elif data.startswith("explore_"):
            # V4.2 FIX: Guard clause - profile min complete
            profile_ok, profile_blocking_msg = is_profile_min_complete(user)
            if not profile_ok:
                await query.edit_message_text(
                    profile_blocking_msg,
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("✅ Continuar con mi perfil", "flow_continue_profile")],
                    ])
                )
                watchdog.mark_response_sent(user_id)
                logger.info(f"🚫 PROFILE_MIN_GUARD | user={user_id} | blocked transition to explore")
                return
            
            parts = data.split("_")
            action = parts[1] if len(parts) > 1 else ""
            
            # State selection (explore_FL, explore_CA, etc.)
            if len(action) == 2 and action.isupper():
                state_code = action
                user["selected_route"] = user.get("selected_route", {})
                user["selected_route"]["state"] = state_code
                save_user_data(user_id, encrypt_user_data(user))
                
                await query.edit_message_text(
                    f"🗺️ Cargando ciudades de {state_code}..."
                )
                await self._show_cities_for_state(query, user_id, state_code)
            
            # Navigation
            elif action == "prev":
                index = int(parts[2]) if len(parts) > 2 else 0
                new_index = max(0, index - 1)
                await self._show_exploration_item(query, user_id, new_index)
            
            elif action == "next":
                index = int(parts[2]) if len(parts) > 2 else 0
                new_index = index + 1
                await self._show_exploration_item(query, user_id, new_index)
            
            elif action == "restart":
                await self._show_exploration_item(query, user_id, 0)
            
            elif action == "like":
                city_id = parts[2] if len(parts) > 2 else ""
                if "favorites" not in user:
                    user["favorites"] = {"cities": [], "housing": [], "jobs": []}
                if city_id not in user["favorites"]["cities"]:
                    user["favorites"]["cities"].append(city_id)
                    save_user_data(user_id, encrypt_user_data(user))
                await query.answer("❤️ ¡Agregado a favoritos!")
            
            elif action == "select":
                city_id = parts[2] if len(parts) > 2 else ""
                from app.services.knowledge_base.cities_database import CITIES_DATABASE
                city = CITIES_DATABASE.get(city_id, {})
                if city:
                    user["selected_route"] = user.get("selected_route", {})
                    user["selected_route"]["city"] = city.get("name", "")
                    user["selected_route"]["state"] = city.get("state_code", "")
                    save_user_data(user_id, encrypt_user_data(user))
                    
                    await query.edit_message_text(
                        f"✅ *¡Excelente elección!*\n\n"
                        f"Has seleccionado *{city.get('name')}, {city.get('state_code')}*\n\n"
                        f"🏠 Ahora puedes buscar viviendas con /viviendas\n"
                        f"💼 O buscar empleos con /empleos\n\n"
                        f"¿Qué quieres hacer?",
                        parse_mode='Markdown',
                        reply_markup=self._kb([
                            [("🏠 Buscar viviendas", "cmd_housing"), ("💼 Buscar empleos", "cmd_jobs")],
                            [("🗺️ Explorar más ciudades", "cmd_explore")],
                        ])
                    )
            
            elif action == "info":
                city_id = parts[2] if len(parts) > 2 else ""
                from app.services.knowledge_base.cities_database import CITIES_DATABASE
                city = CITIES_DATABASE.get(city_id, {})
                if city:
                    pros = city.get("pros", [])
                    cons = city.get("cons", [])
                    industries = city.get("top_industries", [])
                    employers = city.get("major_employers", [])
                    
                    msg = f"ℹ️ *MÁS INFO: {city.get('name')}*\n\n"
                    
                    if pros:
                        msg += "✅ *Ventajas:*\n"
                        for p in pros[:3]:
                            msg += f"• {p}\n"
                        msg += "\n"
                    
                    if cons:
                        msg += "⚠️ *Desventajas:*\n"
                        for c in cons[:3]:
                            msg += f"• {c}\n"
                        msg += "\n"
                    
                    if industries:
                        msg += "🏭 *Industrias principales:*\n"
                        msg += ", ".join(industries[:5]) + "\n\n"
                    
                    if employers:
                        msg += "🏢 *Empleadores principales:*\n"
                        msg += ", ".join(employers[:5]) + "\n"
                    
                    await query.edit_message_text(
                        msg,
                        parse_mode='Markdown',
                        reply_markup=self._kb([
                            [("⬅️ Volver", f"explore_back_{city_id}")],
                        ])
                    )
            
            elif action == "search":
                set_state(user_id, "explore_search")
                await query.edit_message_text(
                    "🔍 *BUSCAR CIUDAD*\n\n"
                    "Escribe el nombre de la ciudad que buscas:\n\n"
                    "_Ejemplo: Miami, Austin, Seattle_"
                )
        
        # Housing callbacks
        elif data.startswith("housing_"):
            action = data.split("_")[1]
            
            if action == "refresh":
                route = user.get("selected_route", {})
                city = route.get("city", "")
                state = route.get("state", "")
                if city and state:
                    await query.edit_message_text("🔄 Actualizando listados...")
                    # Re-run housing search
                    # This would need to call the housing function again
            
            elif action == "filters":
                await query.edit_message_text(
                    "📊 *AJUSTAR FILTROS*\n\n"
                    "Selecciona qué es más importante para ti:",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("💰 Precio bajo", "filter_price"), ("🛏️ Más habitaciones", "filter_size")],
                        [("🛡️ Seguridad", "filter_safety"), ("📍 Ubicación", "filter_location")],
                        [("✅ Aplicar filtros", "housing_apply_filters")],
                    ])
                )
            
            elif action == "favorites":
                favorites = user.get("favorites", {}).get("housing", [])
                if not favorites:
                    await query.edit_message_text(
                        "❤️ *TUS FAVORITOS*\n\n"
                        "Aún no tienes viviendas favoritas.\n"
                        "Usa el botón ❤️ para guardar las que te gusten.",
                        parse_mode='Markdown'
                    )
                else:
                    msg = f"❤️ *TUS {len(favorites)} FAVORITOS*\n\n"
                    # Show favorites
                    await query.edit_message_text(msg, parse_mode='Markdown')
        
        # Name confirmation callbacks
        elif data.startswith("confirm_name_"):
            action = data.replace("confirm_name_", "")
            lang = user.get("language", "en")
            
            if action == "yes":
                # Confirmar nombre y continuar
                # v3.0.7: Buscar nombre en _pending_name O en profile.personal.name
                pending_name = user.get("_pending_name", "")
                if not pending_name:
                    # El onboarding v3.0.6 guarda directamente en profile.personal.name
                    pending_name = user.get("profile", {}).get("personal", {}).get("name", "")
                
                if pending_name:
                    user["profile"]["personal"]["name"] = pending_name
                    # Limpiar nombre pendiente si existe
                    if "_pending_name" in user:
                        del user["_pending_name"]
                    encrypted_data = encrypt_user_data(user)
                    save_user_data(user_id, encrypted_data)
                    
                    # V3.0.3 - Enhanced logging
                    get_transition_logger().log_transition(
                        user_id, "confirm_name", STATE_START,
                        "name_confirmed", {"name": pending_name}
                    )
                    logger.info(f"Name confirmed for user {user_id}: {pending_name}")
                    
                    # Mensaje de bienvenida traducido y avance inmediato
                    hello_text = get_text("hello_name", lang).format(name=pending_name)
                    lets_start = get_text("lets_start", lang)
                    philosophy = get_text("philosophy", lang)
                    first_understand = get_text("first_understand", lang)
                    shall_we = get_text("shall_we_start", lang)
                    yes_start = get_text("yes_lets_start", lang)
                    tell_more = get_text("tell_me_more", lang)
                    
                    await query.edit_message_text(
                        f"{hello_text}\n\n"
                        f"{lets_start}\n\n"
                        f"{philosophy}\n\n"
                        f"{first_understand}\n\n"
                        f"{shall_we}",
                        parse_mode='Markdown',
                        reply_markup=self._kb([
                            [(yes_start, "flow_start_discovery")],
                            [(tell_more, "flow_explain_process")],
                        ])
                    )
                    set_state(user_id, STATE_START)
            
            elif action == "no":
                # Pedir nombre nuevamente
                retry_text = get_text("name_retry", lang)
                await query.edit_message_text(retry_text)
                set_state(user_id, STATE_NAME)
        
        # V3.1.0 - Summary confirmation callbacks (Resumen de Entendimiento)
        elif data.startswith("summary_"):
            action = data.replace("summary_", "")
            
            if action == "confirm":
                # Usuario confirmó que el resumen es correcto
                mark_summary_confirmed(user_id)
                
                if lang == "es":
                    await query.edit_message_text(
                        "✅ *¡Perfecto!* He guardado tu confirmación.\n\n"
                        "Ahora puedo darte recomendaciones personalizadas basadas en tu perfil.\n\n"
                        "¿Qué te gustaría hacer ahora?",
                        parse_mode='Markdown',
                        reply_markup=self._kb([
                            [("📝 Ver recomendación de visa", "flow_continue_visa")],
                            [("🗺️ Explorar ciudades", "cmd_explore")],
                            [("💼 Buscar empleos", "cmd_jobs")],
                        ])
                    )
                else:
                    await query.edit_message_text(
                        "✅ *Perfect!* I've saved your confirmation.\n\n"
                        "Now I can give you personalized recommendations based on your profile.\n\n"
                        "What would you like to do now?",
                        parse_mode='Markdown',
                        reply_markup=self._kb([
                            [("📝 See visa recommendation", "flow_continue_visa")],
                            [("🗺️ Explore cities", "cmd_explore")],
                            [("💼 Search jobs", "cmd_jobs")],
                        ])
                    )
                logger.info(f"✅ SUMMARY CONFIRMED | user={user_id}")
            
            elif action == "correct":
                # Usuario quiere corregir algo
                summary_manager = get_summary_manager()
                summary_manager.mark_needs_correction(user_id)
                
                if lang == "es":
                    await query.edit_message_text(
                        "✏️ *Entendido, vamos a corregir.*\n\n"
                        "¿Qué información necesitas cambiar?\n\n"
                        "Puedes decirme directamente qué quieres corregir, por ejemplo:\n"
                        "\"Mi nombre es Juan\" o \"Soy ingeniero, no contador\"",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(
                        "✏️ *Got it, let's correct that.*\n\n"
                        "What information do you need to change?\n\n"
                        "You can tell me directly what you want to correct, for example:\n"
                        "\"My name is John\" or \"I'm an engineer, not an accountant\"",
                        parse_mode='Markdown'
                    )
            
            elif action == "add_info":
                # Usuario quiere agregar información faltante
                if lang == "es":
                    await query.edit_message_text(
                        "➕ *Agreguemos más información.*\n\n"
                        "Cuéntame qué más te gustaría que sepa sobre ti.\n\n"
                        "Por ejemplo:\n"
                        "• Tu profesión y experiencia\n"
                        "• Tu situación familiar\n"
                        "• Por qué quieres migrar\n"
                        "• Tu presupuesto aproximado",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(
                        "➕ *Let's add more information.*\n\n"
                        "Tell me what else you'd like me to know about you.\n\n"
                        "For example:\n"
                        "• Your profession and experience\n"
                        "• Your family situation\n"
                        "• Why you want to migrate\n"
                        "• Your approximate budget",
                        parse_mode='Markdown'
                    )
            
            watchdog.mark_response_sent(user_id)
            response_tracker.record_response(user_id)
            return
        
        # Flow callbacks
        elif data.startswith("flow_"):
            # Obtener la acción completa después de "flow_"
            action = data[5:]  # Remover "flow_" del inicio
            
            # === NUEVOS HANDLERS PROACTIVOS ===
            if action == "start_discovery" or action == "start":
                # Iniciar flujo desde DISCOVERY_WHY
                ctx = flow_engine.get_context(user_id)
                ctx.current_state = ConversationState.DISCOVERY_WHY
                flow_engine.contexts[user_id] = ctx
                
                name = user.get("profile", {}).get("personal", {}).get("name", "")
                greeting = f"{name}, " if name else ""
                
                await query.edit_message_text(
                    f"📊 *PASO 1 DE 5: DESCUBRIMIENTO*\n\n"
                    f"{greeting}para ayudarte mejor, necesito conocerte.\n\n"
                    "💡 *¿Por qué quieres migrar a Estados Unidos?*\n\n"
                    "Selecciona la opción que más te represente:",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("💼 Mejores oportunidades laborales", "flow_why_work")],
                        [("💰 Mejor calidad de vida", "flow_why_quality")],
                        [("👨‍👩‍👧 Reunirme con familia", "flow_why_family")],
                        [("🎓 Estudios/Educación", "flow_why_education")],
                        [("🏢 Emprender un negocio", "flow_why_business")],
                        [("🌍 Otra razón", "flow_why_other")],
                    ])
                )
            
            elif action == "explain_process":
                await query.edit_message_text(
                    "ℹ️ *CÓMO FUNCIONA MIGPAL*\n\n"
                    "Te guío en 5 pasos:\n\n"
                    "*1️⃣ Descubrimiento* - Entender tu situación y sueños\n"
                    "*2️⃣ Plan de Vida* - Definir trabajo/negocio ideal\n"
                    "*3️⃣ Ubicación* - Elegir estado, ciudad y barrio\n"
                    "*4️⃣ Ruta Migratoria* - Encontrar la visa adecuada\n"
                    "*5️⃣ Ejecución* - Documentos y proceso\n\n"
                    "💡 *Filosofía:* \"La visa es el VEHÍCULO, no el DESTINO\"\n\n"
                    "Primero definimos tu plan de vida, luego la visa.",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("✅ Entendido, empecemos", "flow_start_discovery")],
                    ])
                )
            
            elif action == "continue_location":
                # Continuar con selección de ubicación
                await query.edit_message_text(
                    "🗺️ *PASO 3: UBICACIÓN*\n\n"
                    "¿En qué región de Estados Unidos te gustaría vivir?\n\n"
                    "Cada región tiene características únicas:",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("☀️ Sur (FL, TX, GA)", "flow_region_south")],
                        [("🌃 Noreste (NY, NJ, MA)", "flow_region_northeast")],
                        [("🌲 Oeste (CA, WA, CO)", "flow_region_west")],
                        [("🌾 Medio Oeste (IL, OH, MI)", "flow_region_midwest")],
                        [("🤔 No estoy seguro", "flow_region_help")],
                    ])
                )
            
            elif action == "continue_city":
                # Continuar con exploración de ciudades
                route = user.get("selected_route", {})
                state = route.get("state", "")
                await query.edit_message_text(
                    f"🏙️ *EXPLORANDO CIUDADES EN {state.upper()}*\n\n"
                    "Voy a mostrarte las mejores ciudades según tu perfil.\n\n"
                    "¿Qué es más importante para ti?",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("💰 Costo de vida bajo", "flow_priority_cost")],
                        [("🛡️ Seguridad", "flow_priority_safety")],
                        [("💼 Oportunidades laborales", "flow_priority_jobs")],
                        [("🎓 Buenas escuelas", "flow_priority_schools")],
                        [("⚖️ Balance de todo", "flow_priority_balanced")],
                    ])
                )
            
            elif action == "continue_visa":
                # Continuar con análisis de visa
                route = user.get("selected_route", {})
                city = route.get("city", "")
                state = route.get("state", "")
                await query.edit_message_text(
                    f"📝 *ANÁLISIS DE VISA*\n\n"
                    f"Destino: {city}, {state}\n\n"
                    "Ahora analizaré tu perfil para recomendarte la mejor ruta migratoria.\n\n"
                    "¿Cuál es tu situación actual?",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("💼 Tengo oferta de trabajo en USA", "flow_visa_job_offer")],
                        [("🏢 Quiero invertir/emprender", "flow_visa_investor")],
                        [("🎓 Quiero estudiar primero", "flow_visa_student")],
                        [("👨‍👩‍👧 Tengo familia ciudadana/residente", "flow_visa_family")],
                        [("🤔 No tengo nada de eso", "flow_visa_none")],
                    ])
                )
            
            elif action == "continue_execution":
                # Continuar con ejecución del plan
                route = user.get("selected_route", {})
                await query.edit_message_text(
                    "🚀 *EJECUCIÓN DEL PLAN*\n\n"
                    f"Tu plan:\n"
                    f"• Ciudad: {route.get('city', 'Por definir')}\n"
                    f"• Estado: {route.get('state', 'Por definir')}\n"
                    f"• Visa: {route.get('visa_type', 'Por definir')}\n\n"
                    "¿Qué quieres hacer ahora?",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("💳 Iniciar diagnóstico ($50)", "start_diagnosis")],
                        [("📋 Ver checklist de documentos", "show_checklist")],
                        [("🏠 Buscar viviendas", "cmd_housing")],
                        [("💼 Buscar empleos", "cmd_jobs")],
                    ])
                )
            
            elif action == "info":
                await query.edit_message_text(
                    "ℹ️ *SOBRE EL FLUJO DE MIGRACIÓN*\n\n"
                    "Este proceso te ayuda a:\n\n"
                    "🎯 *Definir tu destino* - No solo la visa, sino tu plan de vida\n"
                    "🗺️ *Elegir ubicación* - Estado, ciudad y barrio ideal\n"
                    "🏠 *Encontrar vivienda* - Opciones reales con precios\n"
                    "💼 *Buscar trabajo* - Empleos que patrocinen visa\n"
                    "📄 *Preparar documentos* - Checklist personalizado\n\n"
                    "*Filosofía:* La visa es el VEHÍCULO, no el DESTINO.\n"
                    "Primero define tu plan de vida, luego la visa adecuada.",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        ("✅ Entendido, empecemos", "flow_start"),
                    ])
                )
            
            # === HANDLERS DE RAZÓN DE MIGRACIÓN ===
            elif action.startswith("why_"):
                reason = action[4:]  # work, quality, family, education, business, other
                reason_texts = {
                    "work": "mejores oportunidades laborales",
                    "quality": "mejor calidad de vida",
                    "family": "reunirte con tu familia",
                    "education": "estudios y educación",
                    "business": "emprender un negocio",
                    "other": "otras razones personales",
                }
                reason_text = reason_texts.get(reason, "tu motivación")
                
                # Guardar en el perfil
                user["profile"]["migration"] = user.get("profile", {}).get("migration", {})
                user["profile"]["migration"]["reason"] = reason
                user["profile"]["migration"]["reason_text"] = reason_text
                save_user_data(user_id, user)
                
                await query.edit_message_text(
                    f"✅ Entendido, quieres migrar por *{reason_text}*.\n\n"
                    "📊 *PASO 2 DE 5: PLAN DE VIDA*\n\n"
                    "¿Qué tipo de actividad te gustaría realizar en USA?",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("💼 Trabajar para una empresa", "flow_activity_employee")],
                        [("🏢 Tener mi propio negocio", "flow_activity_business")],
                        [("💻 Trabajo remoto (ya tengo)", "flow_activity_remote")],
                        [("🎓 Estudiar primero", "flow_activity_study")],
                    ])
                )
            
            # === HANDLERS DE ACTIVIDAD ===
            elif action.startswith("activity_"):
                activity = action[9:]  # employee, business, remote, study
                activity_texts = {
                    "employee": "trabajar para una empresa",
                    "business": "tener tu propio negocio",
                    "remote": "trabajo remoto",
                    "study": "estudiar",
                }
                activity_text = activity_texts.get(activity, "trabajar")
                
                user["profile"]["migration"]["activity"] = activity
                save_user_data(user_id, user)
                
                await query.edit_message_text(
                    f"✅ Perfecto, quieres *{activity_text}*.\n\n"
                    "🗺️ *PASO 3 DE 5: UBICACIÓN*\n\n"
                    "¿En qué región de Estados Unidos te gustaría vivir?",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("☀️ Sur (FL, TX, GA) - Cálido, latinos", "flow_region_south")],
                        [("🌃 Noreste (NY, NJ, MA) - Urbano, diverso", "flow_region_northeast")],
                        [("🌲 Oeste (CA, WA, CO) - Tech, naturaleza", "flow_region_west")],
                        [("🌾 Medio Oeste (IL, OH) - Económico", "flow_region_midwest")],
                        [("🤔 Ayúdame a elegir", "flow_region_help")],
                    ])
                )
            
            # === HANDLERS DE PREFERENCIA (TE AYUDO A ELEGIR) ===
            elif action.startswith("pref_"):
                pref = action[5:]  # warm, cheap, tech, latino
                
                # Mapeo de preferencias a regiones y estados recomendados
                pref_recommendations = {
                    "warm": {
                        "regions": ["south", "west"],
                        "states": ["Florida", "Texas", "Arizona"],
                        "emoji": "☀️",
                        "desc": "clima cálido"
                    },
                    "cheap": {
                        "regions": ["south", "midwest"],
                        "states": ["Texas", "Ohio", "Tennessee"],
                        "emoji": "💰",
                        "desc": "bajo costo de vida"
                    },
                    "tech": {
                        "regions": ["west", "northeast"],
                        "states": ["California", "Washington", "Texas"],
                        "emoji": "💼",
                        "desc": "empleos tech"
                    },
                    "latino": {
                        "regions": ["south", "west"],
                        "states": ["Florida", "Texas", "California"],
                        "emoji": "🤝",
                        "desc": "comunidad latina"
                    }
                }
                
                rec = pref_recommendations.get(pref, pref_recommendations["tech"])
                states = rec["states"]
                
                # Guardar preferencia
                user["profile"]["migration"]["preference"] = pref
                save_user_data(user_id, user)
                
                # Crear botones para estados recomendados
                buttons = []
                for state in states:
                    state_key = state.lower().replace(" ", "_")
                    buttons.append([(f"🏛️ {state}", f"flow_state_{state_key}")])
                buttons.append([("🔙 Ver todas las regiones", "flow_continue_location")])
                
                await query.edit_message_text(
                    f"{rec['emoji']} Excelente, te interesa {rec['desc']}.\n\n"
                    f"🏛️ Te recomiendo estos estados:\n\n"
                    f"¿Cuál te gustaría explorar?",
                    parse_mode='Markdown',
                    reply_markup=self._kb(buttons)
                )
            
            # === HANDLERS DE REGIÓN ===
            elif action.startswith("region_"):
                region = action[7:]  # south, northeast, west, midwest, help
                
                if region == "help":
                    await query.edit_message_text(
                        "🗺️ TE AYUDO A ELEGIR\n\n"
                        "¿Qué es más importante para ti?",
                        reply_markup=self._kb([
                            [("☀️ Clima cálido", "flow_pref_warm")],
                            [("💰 Bajo costo de vida", "flow_pref_cheap")],
                            [("💼 Muchos empleos tech", "flow_pref_tech")],
                            [("🤝 Comunidad latina grande", "flow_pref_latino")],
                        ])
                    )
                else:
                    region_states = {
                        "south": ["Florida", "Texas", "Georgia"],
                        "northeast": ["New York", "New Jersey", "Massachusetts"],
                        "west": ["California", "Washington", "Colorado"],
                        "midwest": ["Illinois", "Ohio", "Michigan"],
                    }
                    states = region_states.get(region, ["Florida"])
                    
                    user["profile"]["migration"]["region"] = region
                    save_user_data(user_id, user)
                    
                    buttons = [[(f"🏛️ {state}", f"flow_state_{state.lower().replace(' ', '_')}") for state in states[:2]]]
                    if len(states) > 2:
                        buttons.append([(f"🏛️ {state}", f"flow_state_{state.lower().replace(' ', '_')}") for state in states[2:]])
                    
                    await query.edit_message_text(
                        f"✅ Excelente elección.\n\n"
                        f"🏛️ *ESTADOS EN ESTA REGIÓN:*\n\n"
                        f"¿Cuál te interesa más?",
                        parse_mode='Markdown',
                        reply_markup=self._kb(buttons)
                    )
            
            # === HANDLERS DE ESTADO ===
            elif action.startswith("state_"):
                state_key = action[6:]  # florida, texas, etc.
                state_names = {
                    "florida": "Florida", "texas": "Texas", "georgia": "Georgia",
                    "new_york": "New York", "new_jersey": "New Jersey", "massachusetts": "Massachusetts",
                    "california": "California", "washington": "Washington", "colorado": "Colorado",
                    "illinois": "Illinois", "ohio": "Ohio", "michigan": "Michigan",
                }
                state_name = state_names.get(state_key, state_key.replace("_", " ").title())
                
                user["selected_route"] = user.get("selected_route", {})
                user["selected_route"]["state"] = state_name
                save_user_data(user_id, user)
                
                await query.edit_message_text(
                    f"✅ *{state_name}* - Excelente elección!\n\n"
                    f"🏙️ *PASO 4 DE 5: CIUDAD*\n\n"
                    f"Ahora vamos a explorar las mejores ciudades de {state_name}.\n\n"
                    f"¿Qué es más importante para ti en una ciudad?",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("💰 Costo de vida bajo", "flow_priority_cost")],
                        [("🛡️ Seguridad", "flow_priority_safety")],
                        [("💼 Oportunidades de empleo", "flow_priority_jobs")],
                        [("🎓 Buenas escuelas", "flow_priority_schools")],
                        [("⚖️ Balance de todo", "flow_priority_balanced")],
                    ])
                )
            
            # === HANDLERS DE PRIORIDAD ===
            elif action.startswith("priority_"):
                priority = action[9:]  # cost, safety, jobs, schools, balanced
                
                user["profile"]["migration"]["priority"] = priority
                save_user_data(user_id, user)
                
                # Buscar ciudades del estado seleccionado
                state = user.get("selected_route", {}).get("state", "Florida")
                cities = search_cities(state, limit=5)
                
                if cities:
                    city = cities[0]
                    user["temp_city_index"] = 0
                    user["temp_cities"] = [c.get("name") for c in cities]
                    save_user_data(user_id, user)
                    
                    # Mostrar primera ciudad
                    score = city.get("scores", {}).get("overall", 75)
                    await query.edit_message_text(
                        f"🏙️ *{city.get('name', 'Ciudad')}*, {state}\n\n"
                        f"⭐ Score: {score}/100\n"
                        f"👥 Población: {city.get('population', 'N/A'):,}\n"
                        f"💰 Costo de vida: {city.get('cost_index', 'Medio')}\n"
                        f"🛡️ Seguridad: {city.get('safety_score', 70)}/100\n"
                        f"🤝 Latinos: {city.get('latino_percentage', 15)}%\n\n"
                        f"Ciudad 1 de {len(cities)}",
                        parse_mode='Markdown',
                        reply_markup=self._kb([
                            [("❤️ Me gusta esta", f"flow_select_city_{city.get('name', '').lower().replace(' ', '_')}")],
                            [("➡️ Ver siguiente", "flow_next_city")],
                            [("📊 Ver todas", "flow_list_cities")],
                        ])
                    )
                else:
                    await query.edit_message_text(
                        f"No encontré ciudades en {state}. Usa /explorar para buscar manualmente."
                    )
            
            # === HANDLER SIGUIENTE CIUDAD ===
            elif action == "next_city":
                state = user.get("selected_route", {}).get("state", "Florida")
                cities = search_cities(state, limit=5)
                current_index = user.get("temp_city_index", 0) + 1
                
                if current_index >= len(cities):
                    current_index = 0  # Volver al inicio
                
                user["temp_city_index"] = current_index
                save_user_data(user_id, user)
                
                city = cities[current_index]
                score = city.get("scores", {}).get("overall", 75)
                
                await query.edit_message_text(
                    f"🏙️ *{city.get('name', 'Ciudad')}*, {state}\n\n"
                    f"⭐ Score: {score}/100\n"
                    f"👥 Población: {city.get('population', 'N/A'):,}\n"
                    f"💰 Costo de vida: {city.get('cost_index', 'Medio')}\n"
                    f"🛡️ Seguridad: {city.get('safety_score', 70)}/100\n"
                    f"🤝 Latinos: {city.get('latino_percentage', 15)}%\n\n"
                    f"Ciudad {current_index + 1} de {len(cities)}",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("❤️ Me gusta esta", f"flow_select_city_{city.get('name', '').lower().replace(' ', '_')}")],
                        [("➡️ Ver siguiente", "flow_next_city")],
                        [("📊 Ver todas", "flow_list_cities")],
                    ])
                )
            
            # === HANDLER SELECCIONAR CIUDAD ===
            elif action.startswith("select_city_"):
                city_key = action[12:]
                city_name = city_key.replace("_", " ").title()
                state = user.get("selected_route", {}).get("state", "")
                
                user["selected_route"]["city"] = city_name
                save_user_data(user_id, user)
                
                await query.edit_message_text(
                    f"✅ *¡Excelente!* Has elegido *{city_name}, {state}*\n\n"
                    f"📝 *PASO 5 DE 5: RUTA MIGRATORIA*\n\n"
                    f"Ahora analizaré tu perfil para recomendarte la mejor visa.\n\n"
                    f"¿Cuál es tu situación actual?",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("💼 Tengo oferta de trabajo en USA", "flow_visa_job_offer")],
                        [("🏢 Quiero invertir (>$100k)", "flow_visa_investor")],
                        [("🎓 Quiero estudiar primero", "flow_visa_student")],
                        [("👨‍👩‍👧 Tengo familia ciudadana", "flow_visa_family")],
                        [("🤔 Ninguna de las anteriores", "flow_visa_none")],
                    ])
                )
            
            # === HANDLERS DE VISA ===
            elif action.startswith("visa_"):
                # ============== V4.2 FIX: GUARD CLAUSE - PROFILE MIN COMPLETE ==============
                # Bloquear CUALQUIER transición si el perfil mínimo no está completo
                profile_ok, profile_blocking_msg = is_profile_min_complete(user)
                if not profile_ok:
                    await query.edit_message_text(
                        profile_blocking_msg,
                        parse_mode='Markdown',
                        reply_markup=self._kb([
                            [("✅ Continuar con mi perfil", "flow_continue_profile")],
                        ])
                    )
                    watchdog.mark_response_sent(user_id)
                    logger.info(f"🚫 PROFILE_MIN_GUARD | user={user_id} | blocked transition to visa")
                    return
                
                # ============== V4.0: GATING DE VISA ==============
                # Verificar con el estándar v4.0 primero (si está habilitado)
                if is_v4_enabled():
                    try:
                        v4_can_recommend, v4_blocking_msg = v4_check_gating(user_id, user)
                        if not v4_can_recommend and v4_blocking_msg:
                            await query.edit_message_text(
                                f"⚠️ {v4_blocking_msg}\n\n"
                                f"¿Quieres que continuemos con tu perfil?",
                                parse_mode='Markdown',
                                reply_markup=self._kb([
                                    [("✅ Sí, continuar", "flow_continue_profile")],
                                    [("📋 Ver mi perfil", "cmd_profile")],
                                ])
                            )
                            watchdog.mark_response_sent(user_id)
                            return
                    except Exception as e:
                        logger.warning(f"V4 gating check error (fallback to legacy): {e}")
                
                # V3.1.0: Verificar confirmación de Resumen de Entendimiento
                summary_confirmed, summary_reason = can_recommend_visa_with_summary(user_id)
                if not summary_confirmed:
                    # No se ha confirmado el resumen - mostrar mensaje y pedir confirmación
                    blocking_msg = get_visa_blocking_message(summary_reason, lang)
                    await query.edit_message_text(
                        blocking_msg,
                        parse_mode='Markdown',
                        reply_markup=self._kb([
                            [("📋 Ver resumen", "cmd_resumen")],
                        ])
                    )
                    watchdog.mark_response_sent(user_id)
                    return
                
                # SEGMENTO 2/3: Verificar datos mínimos antes de recomendar visa
                can_recommend, visa_message = can_recommend_visa(user)
                
                if not can_recommend:
                    # Faltan datos - pedir información requerida
                    next_question = get_next_visa_question(user, lang)
                    await query.edit_message_text(
                        f"⚠️ {visa_message}\n\n{next_question}",
                        parse_mode='Markdown'
                    )
                    watchdog.mark_response_sent(user_id)
                    return
                
                visa_type = action[5:]  # job_offer, investor, student, family, none
                
                visa_recommendations = {
                    "job_offer": ("H-1B", "Visa de trabajo especializado", 70),
                    "investor": ("E-2", "Visa de inversionista", 80),
                    "student": ("F-1", "Visa de estudiante", 90),
                    "family": ("CR-1/IR-1", "Visa familiar", 85),
                    "none": ("B-1/B-2 + Opciones", "Visa de turista mientras exploras opciones", 60),
                }
                
                visa, desc, prob = visa_recommendations.get(visa_type, ("Por determinar", "", 50))
                
                user["selected_route"]["visa_type"] = visa
                user["visa_probability"] = prob
                save_user_data(user_id, user)
                
                city = user.get("selected_route", {}).get("city", "")
                state = user.get("selected_route", {}).get("state", "")
                
                await query.edit_message_text(
                    f"🎉 *¡PLAN COMPLETO!*\n\n"
                    f"🗺️ *Destino:* {city}, {state}\n"
                    f"📝 *Visa recomendada:* {visa}\n"
                    f"📊 *Probabilidad:* {prob}%\n\n"
                    f"_{desc}_\n\n"
                    f"¿Qué quieres hacer ahora?",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("💳 Iniciar diagnóstico profesional ($50)", "start_diagnosis")],
                        [("🏠 Buscar viviendas en " + city, "cmd_housing")],
                        [("💼 Buscar empleos con sponsor", "cmd_jobs")],
                        [("📋 Ver checklist de documentos", "show_checklist")],
                        [("📄 Generar PDF de mi plan", "pdf_plan")],
                    ])
                )
            
            else:
                # Procesar respuesta del flujo
                ctx = flow_engine.get_context(user_id)
                next_state, error_msg = flow_engine.process_response(
                    user_id, action, selected_options=[action]
                )
                
                if error_msg:
                    await query.answer(error_msg)
                    return
                
                # Obtener siguiente pregunta
                question_data = STATE_QUESTIONS.get(next_state, {})
                if question_data:
                    name = user.get("profile", {}).get("personal", {}).get("name", "amigo")
                    ctx = flow_engine.get_context(user_id)
                    message = question_data.get("message", "").format(
                        name=name,
                        why_migrate_text=ctx.why_migrate or "tu motivación"
                    )
                    
                    options = question_data.get("options", [])
                    if options:
                        buttons = [(opt[1], f"flow_{opt[0]}") for opt in options]
                        kb = self._kb(buttons)
                    else:
                        kb = None
                    
                    progress = flow_engine.get_progress_percentage(user_id)
                    
                    await query.edit_message_text(
                        f"📊 Progreso: {progress}%\n\n{message}",
                        parse_mode='Markdown',
                        reply_markup=kb
                    )
                else:
                    # Estado sin pregunta definida - mostrar resumen
                    summary = flow_engine.get_summary(user_id)
                    await query.edit_message_text(
                        "✅ *¡Excelente progreso!*\n\n"
                        f"Estado actual: {summary.get('estado_actual')}\n"
                        f"Progreso: {summary.get('progreso')}\n\n"
                        "Usa /flujo para continuar.",
                        parse_mode='Markdown'
                    )
        
        # Command shortcuts from buttons
        elif data == "cmd_explore":
            await query.edit_message_text("🗺️ Usa /explorar para ver ciudades")
        
        elif data == "cmd_housing":
            await query.edit_message_text("🏠 Usa /viviendas para buscar viviendas")
        
        elif data == "cmd_jobs":
            await query.edit_message_text("💼 Usa /empleos para buscar trabajos")
        
        # === SHOW PROGRESS ===
        elif data == "show_progress":
            route = user.get("selected_route", {})
            profile = user.get("profile", {})
            migration = profile.get("migration", {})
            
            # Calcular progreso
            steps_completed = 0
            total_steps = 5
            
            if migration.get("reason"):
                steps_completed += 1
            if migration.get("activity"):
                steps_completed += 1
            if route.get("state"):
                steps_completed += 1
            if route.get("city"):
                steps_completed += 1
            if route.get("visa_type"):
                steps_completed += 1
            
            progress_pct = int((steps_completed / total_steps) * 100)
            progress_bar = "█" * (progress_pct // 10) + "░" * (10 - progress_pct // 10)
            
            await query.edit_message_text(
                f"📊 *TU PROGRESO*\n\n"
                f"{progress_bar} {progress_pct}%\n\n"
                f"✅ Razón de migración: {migration.get('reason_text', '❌ Pendiente')}\n"
                f"✅ Actividad: {migration.get('activity', '❌ Pendiente')}\n"
                f"✅ Estado: {route.get('state', '❌ Pendiente')}\n"
                f"✅ Ciudad: {route.get('city', '❌ Pendiente')}\n"
                f"✅ Visa: {route.get('visa_type', '❌ Pendiente')}\n\n"
                f"¿Quieres continuar?",
                parse_mode='Markdown',
                reply_markup=self._kb([
                    [("▶️ Continuar proceso", "flow_start_discovery" if steps_completed == 0 else "flow_continue_location" if not route.get('state') else "flow_continue_city" if not route.get('city') else "flow_continue_visa")],
                    [("🔄 Empezar de nuevo", "reset_profile")],
                ])
            )
        
        # ===== V5 CALLBACKS =====
        
        # Tracking callbacks
        elif data == "tracking_complete":
            user["current_stage"] = user.get("current_stage", 0) + 1
            save_user_data(user_id, user)
            await query.edit_message_text(
                "✅ *¡Etapa marcada como completada!*\n\n"
                "Usa /tracking para ver tu progreso actualizado.",
                parse_mode='Markdown'
            )
        
        elif data == "tracking_dates":
            route = user.get("selected_route", {})
            stages = get_application_stages(route.get("country", ""), route.get("visa_type", ""))
            if stages:
                timeline = calculate_timeline(stages)
                total_days = sum(30 if "mes" in s.get("duration", "") else 14 for s in stages)
                await query.edit_message_text(
                    f"📅 *FECHAS ESTIMADAS*\n\n"
                    f"Inicio: {timeline[0]['start_date']}\n"
                    f"Fin estimado: {timeline[-1]['end_date']}\n"
                    f"Duración total: ~{total_days // 30} meses\n\n"
                    "_Estos son estimados basados en tiempos promedio_",
                    parse_mode='Markdown'
                )
        
        # Mentor callbacks
        elif data.startswith("mentor_"):
            mentor_id = int(data.split("_")[1])
            mentor = next((m for m in MENTORS if m["id"] == mentor_id), None)
            if mentor:
                await query.edit_message_text(
                    f"🧑‍🏫 *{mentor['name']}*\n\n"
                    f"🌍 {mentor['country_origin']} → {mentor['country_destination']}\n"
                    f"📄 {mentor['visa_type']}\n"
                    f"💼 {mentor['profession']}\n"
                    f"⭐ {mentor['rating']} ({mentor['sessions']} sesiones)\n\n"
                    f"_{mentor['bio']}_\n\n"
                    "📅 *Para agendar una sesión:*\n"
                    "Envía un mensaje con tu disponibilidad y te conectaremos.",
                    parse_mode='Markdown'
                )
        
        elif data == "mentors_more":
            mentors = get_mentors()
            msg = "🧑‍🏫 *TODOS LOS MENTORES*\n\n"
            for m in mentors:
                msg += f"• {m['name']} - {m['country_destination']} ({m['visa_type']})\n"
            await query.edit_message_text(msg, parse_mode='Markdown')
        
        # Guide callbacks
        elif data.startswith("guide_"):
            parts = data.split("_")
            country = parts[1]
            section = "_".join(parts[2:])
            guide = get_settlement_guide(country)
            
            if guide and section in guide:
                sec = guide[section]
                msg = f"{sec['title']}\n\n"
                msg += "*Pasos:*\n"
                for step in sec['steps']:
                    msg += f"{step}\n"
                msg += "\n*Tips:*\n"
                for tip in sec.get('tips', []):
                    msg += f"{tip}\n"
                await query.edit_message_text(msg, parse_mode='Markdown')
        
        # Language callbacks
        elif data.startswith("lang_"):
            lang = data.split("_")[1]
            
            if lang == "more":
                # Show all languages
                languages = get_all_languages()
                buttons = []
                row = []
                for name, code in languages:
                    row.append((name, f"lang_{code}"))
                    if len(row) == 2:
                        buttons.append(row)
                        row = []
                if row:
                    buttons.append(row)
                
                await query.edit_message_text(
                    "🌐 *ALL LANGUAGES / TODOS LOS IDIOMAS*\n\n"
                    "Select your language:",
                    parse_mode='Markdown',
                    reply_markup=self._kb(buttons)
                )
            else:
                user["language"] = lang
                # Encrypt and save to ensure persistence
                encrypted_data = encrypt_user_data(user)
                save_user_data(user_id, encrypted_data)
                
                # Get language name
                lang_info = SUPPORTED_LANGUAGES.get(lang, {})
                lang_name = lang_info.get("native", lang)
                
                logger.info(f"Language set to {lang} for user {user_id}, persisted to disk")
                
                # v3.0.6: Iniciar ONBOARDING CONVERSACIONAL (no formulario)
                from app.services.onboarding_v306 import get_onboarding_engine, OnboardingState
                
                engine = get_onboarding_engine()
                
                # Confirmar idioma brevemente
                await query.edit_message_text(
                    f"✅ {lang_info.get('flag', '')} {lang_name}"
                )
                
                # Establecer estado de onboarding
                set_state(user_id, OnboardingState.WELCOME.value)
                
                # Pequeña pausa
                await asyncio.sleep(0.8)
                
                # PASO 1: Presentación empática
                welcome_msg = engine.get_welcome_message(lang)
                await query.message.reply_text(welcome_msg)
                
                await asyncio.sleep(1.5)
                
                # PASO 2: Pregunta abierta
                set_state(user_id, OnboardingState.OPEN_QUESTION.value)
                open_question = engine.get_open_question(lang)
                await query.message.reply_text(open_question)
        
        # Notification callbacks
        elif data.startswith("notif_"):
            parts = data.split("_")
            
            if len(parts) >= 3:
                ntype = parts[1]
                action = parts[2]
                
                # Initialize notification prefs if not exists
                if "notification_prefs" not in user:
                    user["notification_prefs"] = get_default_notification_prefs()
                
                if ntype == "all":
                    # Toggle all notifications
                    new_value = (action == "on")
                    for nt in NOTIFICATION_TYPES.keys():
                        user["notification_prefs"][nt] = new_value
                    
                    status = "✅ Activadas" if new_value else "❌ Desactivadas"
                    await query.edit_message_text(
                        f"🔔 *Notificaciones {status}*\n\n"
                        f"Todas las notificaciones han sido {status.lower()}.\n\n"
                        "Usa /notificaciones para ver la configuración.",
                        parse_mode='Markdown'
                    )
                
                elif ntype == "schedule":
                    # Show scheduled notifications
                    scheduler = get_scheduler()
                    jobs = scheduler.get_scheduled_jobs()
                    
                    msg = "📅 *PRÓXIMAS NOTIFICACIONES PROGRAMADAS*\n\n"
                    
                    if jobs:
                        for job in jobs[:10]:
                            msg += f"• *{job['name']}*\n"
                            msg += f"  Próxima: {job['next_run'] or 'N/A'}\n\n"
                    else:
                        msg += "No hay notificaciones programadas.\n"
                    
                    msg += "\n_Las notificaciones se envían automáticamente según tu configuración._"
                    
                    await query.edit_message_text(msg, parse_mode='Markdown')
                
                else:
                    # Toggle specific notification type
                    if ntype in NOTIFICATION_TYPES:
                        new_value = (action == "on")
                        user["notification_prefs"][ntype] = new_value
                        
                        info = NOTIFICATION_TYPES[ntype]
                        status = "✅ Activada" if new_value else "❌ Desactivada"
                        
                        await query.edit_message_text(
                            f"🔔 *{info['name']}*\n\n"
                            f"Estado: {status}\n\n"
                            f"_{info['description']}_\n\n"
                            "Usa /notificaciones para ver todas las opciones.",
                            parse_mode='Markdown'
                        )
                
                # Save user preferences
                encrypted_data = encrypt_user_data(user)
                save_user_data(user_id, encrypted_data)
        
        # ===== GAMIFICATION CALLBACKS =====
        elif data.startswith("game_"):
            action = data.replace("game_", "")
            engine = get_game_engine()
            
            if action == "prices":
                await query.edit_message_text(
                    get_prices_summary(),
                    parse_mode='Markdown'
                )
            
            elif action == "level":
                progress = engine.get_progress_display(user_id)
                await query.edit_message_text(progress, parse_mode='Markdown')
            
            elif action == "deliverables":
                status = engine.get_deliverables_status(user_id)
                await query.edit_message_text(status, parse_mode='Markdown')
            
            elif action == "info_diagnostic":
                await query.edit_message_text(
                    "🔍 *¿QUÉ INCLUYE EL DIAGNÓSTICO?*\n\n"
                    "• Evaluación completa de tu perfil\n"
                    "• Análisis de viabilidad migratoria\n"
                    "• Score de probabilidad de éxito\n"
                    "• Opciones de visa recomendadas\n"
                    "• Plan de mejora (si no eres viable)\n\n"
                    "💰 *Costo:* $50 USD\n"
                    "⏰ *Duración:* 24-48 horas\n\n"
                    "🔒 *Garantía:* Si no eres viable, te ayudamos a mejorar sin costo adicional.",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        ("✅ Pagar $50 y comenzar", "pay_diagnostic"),
                    ])
                )
        
        # ===== PAYMENT CALLBACKS =====
        elif data.startswith("pay_"):
            parts = data.split("_")
            method = parts[1] if len(parts) > 1 else ""
            payment_type = parts[2] if len(parts) > 2 else "diagnostic"
            
            pm = get_payment_manager()
            engine = get_game_engine()
            
            # Determinar monto
            amounts = {"diagnostic": 50, "approval": 50, "plan": 900}
            amount = amounts.get(payment_type, 50)
            
            if method == "diagnostic":
                # Mostrar opciones de pago
                await query.edit_message_text(
                    f"💳 *PAGAR DIAGNÓSTICO*\n\n"
                    f"Monto: *$50 USD*\n\n"
                    "Selecciona tu método de pago:",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("💳 Tarjeta", "pay_stripe_diagnostic"), ("🅿️ PayPal", "pay_paypal_diagnostic")],
                        [("📱 Zelle", "pay_zelle_diagnostic"), ("🏦 Transferencia", "pay_bank_diagnostic")],
                    ])
                )
            
            elif method == "zelle":
                payment_id, instructions = pm.get_payment_link(
                    user_id, 
                    PaymentType.DIAGNOSTICO if payment_type == "diagnostic" else PaymentType.APROBACION,
                    PaymentMethod.ZELLE
                )
                await query.edit_message_text(
                    instructions + f"\n\nID de pago: `{payment_id}`",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        ("✅ Ya pagué", f"pay_confirm_{payment_id}"),
                    ])
                )
            
            elif method == "bank":
                payment_id, instructions = pm.get_payment_link(
                    user_id,
                    PaymentType.DIAGNOSTICO if payment_type == "diagnostic" else PaymentType.APROBACION,
                    PaymentMethod.BANK_TRANSFER
                )
                await query.edit_message_text(
                    instructions + f"\n\nID de pago: `{payment_id}`",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        ("✅ Ya pagué", f"pay_confirm_{payment_id}"),
                    ])
                )
            
            elif method == "stripe" or method == "paypal":
                await query.edit_message_text(
                    f"💳 *PAGO CON {method.upper()}*\n\n"
                    f"Monto: ${amount} USD\n\n"
                    "⚠️ Integración en desarrollo.\n\n"
                    "Por ahora usa Zelle o Transferencia.",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        ("📱 Pagar con Zelle", f"pay_zelle_{payment_type}"),
                    ])
                )
            
            elif method == "confirm":
                payment_id = "_".join(parts[2:]) if len(parts) > 2 else ""
                success, msg = pm.confirm_payment(payment_id)
                
                if success:
                    # Actualizar nivel en gamificación
                    engine.start_diagnostic(user_id, payment_confirmed=True)
                    
                    await query.edit_message_text(
                        f"✅ *¡PAGO CONFIRMADO!*\n\n"
                        f"Gracias por tu pago.\n\n"
                        f"🔍 Iniciando diagnóstico...\n\n"
                        f"Te enviaremos los resultados en 24-48 horas.",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(f"⚠️ {msg}")
        
        # ===== REFUND CALLBACKS =====
        elif data.startswith("refund_"):
            action = data.replace("refund_", "")
            engine = get_game_engine()
            
            if action == "confirm":
                success, msg = engine.request_refund(user_id, "Solicitud del usuario")
                await query.edit_message_text(
                    f"💸 *DEVOLUCIÓN SOLICITADA*\n\n{msg}\n\n"
                    "Te contactaremos para procesar la devolución.",
                    parse_mode='Markdown'
                )
            
            elif action == "cancel":
                await query.edit_message_text(
                    "✅ Devolución cancelada.\n\n"
                    "Continuamos con tu proceso. Usa /nivel para ver tu progreso."
                )
                watchdog.mark_response_sent(user_id)
    
    async def _handle_multi_select(self, query, user_id: int, data: str, user: dict):
        """Maneja selección múltiple con botón enviar"""
        parts = data.split("_")
        action = parts[1] if len(parts) > 1 else ""
        value = "_".join(parts[2:]) if len(parts) > 2 else ""
        
        field = get_multi_select_field(user_id)
        
        if action == "toggle":
            # Toggle selección
            selected = toggle_selection(user_id, value)
            
            # Actualizar teclado con nuevas selecciones
            # Obtener opciones del campo actual
            options = self._get_multi_select_options(field)
            keyboard = build_multi_select_keyboard(options, selected, "ms")
            
            # Mostrar selecciones actuales
            sel_text = ", ".join(selected) if selected else "Ninguna"
            
            await query.edit_message_text(
                f"{get_form_header(field)}\n"
                f"Selecciona las opciones que apliquen:\n\n"
                f"📝 *Seleccionados:* {sel_text}",
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        
        elif action == "clear":
            # Limpiar selecciones
            init_multi_select(user_id, field, [])
            options = self._get_multi_select_options(field)
            keyboard = build_multi_select_keyboard(options, [], "ms")
            
            await query.edit_message_text(
                f"{get_form_header(field)}\n"
                f"Selecciona las opciones que apliquen:\n\n"
                f"📝 *Seleccionados:* Ninguna",
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        
        elif action == "submit":
            # Enviar selecciones
            selections = clear_multi_select(user_id)
            
            if not selections:
                await query.answer("⚠️ Selecciona al menos una opción", show_alert=True)
                return
            
            # Guardar en el perfil según el campo
            await self._save_multi_select(user_id, user, field, selections)
            
            # Confirmar y continuar
            sel_text = ", ".join(selections)
            await query.edit_message_text(
                f"✅ *Guardado:* {sel_text}\n\n"
                f"¿Te quedó claro o quieres cambiar algo?",
                parse_mode='Markdown'
            )
    
    def _get_multi_select_options(self, field: str) -> list:
        """Obtiene opciones para selección múltiple según el campo"""
        options_map = {
            "education_field": [
                ("💻", "Tecnología", "tech"),
                ("🏥", "Salud", "health"),
                ("📊", "Negocios", "business"),
                ("⚖️", "Derecho", "law"),
                ("🔧", "Ingeniería", "engineering"),
                ("🎨", "Artes", "arts"),
                ("📚", "Educación", "education"),
                ("🌿", "Ciencias", "science"),
            ],
            "languages": [
                ("🇬🇧", "Inglés", "english"),
                ("🇪🇸", "Español", "spanish"),
                ("🇫🇷", "Francés", "french"),
                ("🇩🇪", "Alemán", "german"),
                ("🇵🇹", "Portugués", "portuguese"),
                ("🇮🇹", "Italiano", "italian"),
                ("🇨🇳", "Chino", "chinese"),
            ],
            "interests": [
                ("💼", "Trabajo", "work"),
                ("📚", "Estudios", "study"),
                ("🏠", "Calidad de vida", "quality"),
                ("👨‍👩‍👧", "Familia", "family"),
                ("🔒", "Seguridad", "security"),
                ("🌍", "Aventura", "adventure"),
            ],
            "skills": [
                ("💻", "Programación", "programming"),
                ("📊", "Análisis de datos", "data"),
                ("🎨", "Diseño", "design"),
                ("📝", "Escritura", "writing"),
                ("🗣️", "Comunicación", "communication"),
                ("👥", "Liderazgo", "leadership"),
            ],
        }
        return options_map.get(field, [])
    
    async def _save_multi_select(self, user_id: int, user: dict, field: str, selections: list):
        """Guarda las selecciones múltiples en el perfil"""
        profile = user.get("profile", {})
        
        if field == "education_field":
            profile.setdefault("education", {})["fields"] = selections
        elif field == "languages":
            profile.setdefault("languages", {})["spoken"] = selections
        elif field == "interests":
            user.setdefault("preferences", {})["interests"] = selections
        elif field == "skills":
            profile.setdefault("work", {})["skills"] = selections
        
        # Guardar
        encrypted_data = encrypt_user_data(user)
        save_user_data(user_id, encrypted_data)
    
    # ============== EXPERTISE MULTI-SELECT ==============
    
    # Estado temporal para selecciones de expertise
    _expertise_selections: Dict[int, List[str]] = {}
    
    async def _handle_expertise_select(self, query, user_id: int, data: str, user: dict):
        """Maneja selección múltiple de áreas de expertise"""
        action = data.replace("exp_", "")
        
        # Inicializar si no existe
        if user_id not in self._expertise_selections:
            self._expertise_selections[user_id] = []
        
        selected = self._expertise_selections[user_id]
        
        options = [
            ("tech", "🤖 Tecnología / IA"),
            ("business", "💼 Negocios / Emprendimiento"),
            ("finance", "💹 Finanzas / Trading"),
            ("art", "🎨 Arte / Creatividad"),
        ]
        
        if action in ["tech", "business", "finance", "art"]:
            # Toggle selección
            if action in selected:
                selected.remove(action)
            else:
                selected.append(action)
            
            # Construir teclado actualizado
            keyboard = []
            for value, label in options:
                check = "✅" if value in selected else "⬜"
                keyboard.append([{"text": f"{check} {label}", "callback_data": f"exp_{value}"}])
            
            keyboard.append([
                {"text": "🗑️ Limpiar", "callback_data": "exp_clear"},
                {"text": "✅ Confirmar", "callback_data": "exp_submit"}
            ])
            
            # Mostrar selecciones actuales
            sel_labels = [label for value, label in options if value in selected]
            sel_text = ", ".join(sel_labels) if sel_labels else "Ninguna"
            
            from telegram import InlineKeyboardMarkup
            await query.edit_message_text(
                f"👋 Hernan, necesito completar tu perfil.\n\n"
                f"📋 *¿Cuál es tu área de expertise?*\n"
                f"(Puedes seleccionar varias)\n\n"
                f"📝 *Seleccionado:* {sel_text}",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif action == "clear":
            self._expertise_selections[user_id] = []
            
            keyboard = []
            for value, label in options:
                keyboard.append([{"text": f"⬜ {label}", "callback_data": f"exp_{value}"}])
            keyboard.append([
                {"text": "🗑️ Limpiar", "callback_data": "exp_clear"},
                {"text": "✅ Confirmar", "callback_data": "exp_submit"}
            ])
            
            from telegram import InlineKeyboardMarkup
            await query.edit_message_text(
                f"👋 Hernan, necesito completar tu perfil.\n\n"
                f"📋 *¿Cuál es tu área de expertise?*\n"
                f"(Puedes seleccionar varias)\n\n"
                f"📝 *Seleccionado:* Ninguna",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif action == "submit":
            if not selected:
                await query.answer("⚠️ Selecciona al menos una opción", show_alert=True)
                return
            
            # Guardar en el perfil
            labels_map = {"tech": "Tecnología/IA", "business": "Negocios/Emprendimiento", 
                         "finance": "Finanzas/Trading", "art": "Arte/Creatividad"}
            expertise_labels = [labels_map[s] for s in selected]
            
            user.setdefault("profile", {}).setdefault("work", {})["expertise"] = expertise_labels
            encrypted_data = encrypt_user_data(user)
            save_user_data(user_id, encrypted_data)
            
            # Limpiar estado
            del self._expertise_selections[user_id]
            
            sel_text = ", ".join(expertise_labels)
            
            # Siguiente pregunta: Logros
            await query.edit_message_text(
                f"✅ *Guardado:* {sel_text}\n\n"
                f"🏆 *Ahora, ¿qué logros destacados tienes?*\n"
                f"(Selecciona todos los que apliquen)",
                parse_mode='Markdown',
                reply_markup=self._build_logros_keyboard([])
            )
    
    def _build_logros_keyboard(self, selected: list):
        """Construye teclado de selección de logros"""
        from telegram import InlineKeyboardMarkup
        
        options = [
            ("premios", "🏆 Premios o reconocimientos"),
            ("publicaciones", "📝 Artículos o publicaciones"),
            ("membresias", "🌟 Membresías en asociaciones"),
            ("liderazgo", "👑 Roles de liderazgo"),
            ("patentes", "💡 Patentes o invenciones"),
            ("medios", "📺 Apariciones en medios"),
        ]
        
        keyboard = []
        for value, label in options:
            check = "✅" if value in selected else "⬜"
            keyboard.append([{"text": f"{check} {label}", "callback_data": f"logro_{value}"}])
        
        keyboard.append([
            {"text": "🗑️ Limpiar", "callback_data": "logro_clear"},
            {"text": "✅ Confirmar", "callback_data": "logro_submit"}
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    # Estado temporal para selecciones de logros
    _logros_selections: Dict[int, List[str]] = {}
    
    async def _handle_logros_select(self, query, user_id: int, data: str, user: dict):
        """Maneja selección múltiple de logros"""
        action = data.replace("logro_", "")
        
        # Inicializar si no existe
        if user_id not in self._logros_selections:
            self._logros_selections[user_id] = []
        
        selected = self._logros_selections[user_id]
        
        logro_options = ["premios", "publicaciones", "membresias", "liderazgo", "patentes", "medios"]
        
        if action in logro_options:
            # Toggle selección
            if action in selected:
                selected.remove(action)
            else:
                selected.append(action)
            
            await query.edit_message_text(
                f"🏆 *¿Qué logros destacados tienes?*\n"
                f"(Selecciona todos los que apliquen)\n\n"
                f"📝 *Seleccionado:* {len(selected)} logro(s)",
                parse_mode='Markdown',
                reply_markup=self._build_logros_keyboard(selected)
            )
        
        elif action == "clear":
            self._logros_selections[user_id] = []
            
            await query.edit_message_text(
                f"🏆 *¿Qué logros destacados tienes?*\n"
                f"(Selecciona todos los que apliquen)\n\n"
                f"📝 *Seleccionado:* Ninguno",
                parse_mode='Markdown',
                reply_markup=self._build_logros_keyboard([])
            )
        
        elif action == "submit":
            if not selected:
                await query.answer("⚠️ Selecciona al menos una opción", show_alert=True)
                return
            
            # Guardar en el perfil
            labels_map = {
                "premios": "Premios/Reconocimientos",
                "publicaciones": "Artículos/Publicaciones",
                "membresias": "Membresías en asociaciones",
                "liderazgo": "Roles de liderazgo",
                "patentes": "Patentes/Invenciones",
                "medios": "Apariciones en medios"
            }
            logros_labels = [labels_map[s] for s in selected]
            
            user.setdefault("profile", {}).setdefault("work", {})["logros"] = logros_labels
            encrypted_data = encrypt_user_data(user)
            save_user_data(user_id, encrypted_data)
            
            # Limpiar estado
            del self._logros_selections[user_id]
            
            sel_text = ", ".join(logros_labels)
            
            # Resumen y siguiente paso
            await query.edit_message_text(
                f"✅ *Perfil actualizado!*\n\n"
                f"🎯 *Expertise:* {', '.join(user.get('profile', {}).get('work', {}).get('expertise', []))}\n"
                f"🏆 *Logros:* {sel_text}\n\n"
                f"Con esta información puedo darte una mejor asesoría.\n\n"
                f"¿Qué te gustaría hacer ahora?",
                parse_mode='Markdown',
                reply_markup=self._kb([
                    ("🎯 Ver mi recomendación de visa", "show_recommendation"),
                    ("💰 Ver costos del proceso", "show_costs"),
                    ("▶️ Continuar con el diagnóstico", "start_diagnostic")
                ])
            )
    
    # ============== PLAN DE MIGRACIÓN INTEGRAL ==============
    
    async def _handle_migration_plan(self, query, user_id: int, data: str, user: dict):
        """Maneja las preguntas del plan de migración integral"""
        from telegram import InlineKeyboardMarkup
        
        # Manejar restart
        if data == "plan_restart":
            await self.start_migration_plan(query, user_id, user)
            return
        
        # Parsear: plan_questionid_value
        # El formato es: plan_<question_id>_<value>
        # question_id puede tener guiones bajos, así que buscamos en MIGRATION_PLAN_QUESTIONS
        
        data_without_prefix = data[5:]  # Quitar "plan_"
        
        # Encontrar qué question_id coincide
        question_id = None
        value = None
        
        for q_id in MIGRATION_PLAN_QUESTIONS:
            if data_without_prefix.startswith(q_id + "_"):
                question_id = q_id
                value = data_without_prefix[len(q_id) + 1:]  # +1 para el guion bajo
                break
        
        if not question_id or not value:
            logger.error(f"Could not parse migration plan callback: {data}")
            await query.answer("⚠️ Error procesando selección", show_alert=True)
            return
        
        # Guardar preferencia
        if "migration_preferences" not in user:
            user["migration_preferences"] = {}
        
        user["migration_preferences"][question_id] = value
        
        # Guardar en disco
        encrypted_data = encrypt_user_data(user)
        save_user_data(user_id, encrypted_data)
        
        # Obtener siguiente pregunta
        next_q = get_next_plan_question(user["migration_preferences"])
        
        if next_q:
            # Hay más preguntas
            q_text, keyboard = get_question_keyboard(next_q)
            
            # Calcular progreso
            answered = len(user["migration_preferences"])
            total = len(MIGRATION_PLAN_QUESTIONS)
            progress = create_progress_bar(answered, total)
            
            await query.edit_message_text(
                f"📍 *PLAN DE MIGRACIÓN* ({answered}/{total})\n"
                f"{progress}\n\n"
                f"{q_text}",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Todas las preguntas respondidas - mostrar resultados
            await self._show_city_recommendations(query, user_id, user)
    
    async def _show_city_recommendations(self, query, user_id: int, user: dict):
        """Muestra las ciudades recomendadas basadas en preferencias"""
        from telegram import InlineKeyboardMarkup
        
        preferences = user.get("migration_preferences", {})
        
        # Obtener top 5 ciudades
        top_cities = get_top_cities(preferences, top_n=5)
        
        # Construir mensaje
        msg = "🏆 *TUS MEJORES CIUDADES PARA VIVIR*\n\n"
        msg += "Basado en tus preferencias, estas son mis recomendaciones:\n\n"
        
        keyboard = []
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        
        for i, (city_id, city_data, score) in enumerate(top_cities):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            msg += f"{medal} *{city_data['nombre']}* - {score}% match\n"
            msg += f"   └ 💰 ${city_data['costo_vida_mensual']['total_estimado']:,}/mes | "
            msg += f"🛡️ {city_data['scores']['seguridad']}/100 | "
            msg += f"☀️ {city_data['clima'].capitalize()}\n\n"
            
            keyboard.append([{
                "text": f"{medal} Ver plan para {city_data['nombre'].split(',')[0]}",
                "callback_data": f"city_select_{city_id}"
            }])
        
        keyboard.append([{"text": "🔄 Cambiar preferencias", "callback_data": "plan_restart"}])
        keyboard.append([{"text": "📊 Comparar ciudades", "callback_data": "city_compare"}])
        
        await query.edit_message_text(
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def _handle_city_selection(self, query, user_id: int, data: str, user: dict):
        """Maneja la selección de una ciudad para ver el plan detallado"""
        from telegram import InlineKeyboardMarkup
        
        action = data.replace("city_", "")
        
        if action == "compare":
            # Mostrar comparación de top 3
            preferences = user.get("migration_preferences", {})
            top_cities = get_top_cities(preferences, top_n=3)
            city_ids = [c[0] for c in top_cities]
            
            comparison = get_city_comparison(city_ids)
            
            keyboard = []
            for city_id, city_data, score in top_cities:
                keyboard.append([{
                    "text": f"📍 Ver plan para {city_data['nombre'].split(',')[0]}",
                    "callback_data": f"city_select_{city_id}"
                }])
            keyboard.append([{"text": "⬅️ Volver", "callback_data": "city_back"}])
            
            await query.edit_message_text(
                comparison,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif action == "back":
            # Volver a recomendaciones
            await self._show_city_recommendations(query, user_id, user)
        
        elif action.startswith("select_"):
            city_id = action.replace("select_", "")
            await self._show_city_plan(query, user_id, user, city_id)
        
        elif action.startswith("plan_"):
            # Ver sección específica del plan
            parts = action.split("_")
            city_id = parts[1]
            section = parts[2] if len(parts) > 2 else "resumen"
            await self._show_plan_section(query, user_id, user, city_id, section)
        
        elif action.startswith("confirm_"):
            # Confirmar selección de ciudad
            city_id = action.replace("confirm_", "")
            await self._confirm_city_selection(query, user_id, user, city_id)
    
    async def _confirm_city_selection(self, query, user_id: int, user: dict, city_id: str):
        """Confirma la selección de ciudad y muestra opciones de vivienda, trabajo, etc."""
        from telegram import InlineKeyboardMarkup
        
        city = CITIES_DATABASE.get(city_id)
        if not city:
            await query.answer("Ciudad no encontrada", show_alert=True)
            return
        
        # Guardar ciudad seleccionada
        if "migration_preferences" not in user:
            user["migration_preferences"] = {}
        user["migration_preferences"]["selected_city"] = city_id
        user["migration_preferences"]["selected_city_name"] = city["nombre"]
        save_user_data(user_id, user)
        
        # Mensaje de confirmación con foto
        msg = f"✅ *¡EXCELENTE ELECCIÓN!*\n\n"
        msg += f"🏙️ Has seleccionado *{city['nombre']}*\n\n"
        msg += f"📸 *Foto de la ciudad:*\n"
        msg += f"{city.get('foto_url', 'https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=800')}\n\n"
        msg += f"📝 *{city.get('descripcion', 'Ciudad ideal para tu migración.')}*\n\n"
        msg += f"Ahora puedo mostrarte información REAL de:\n"
        msg += f"• 🏠 Viviendas disponibles (Zillow)\n"
        msg += f"• 💼 Ofertas de empleo para tu perfil\n"
        msg += f"• 🎓 Colegios con ratings\n"
        msg += f"• 🏪 Negocios en venta\n\n"
        msg += f"¿Qué te gustaría ver primero?"
        
        keyboard = [
            [{"text": "🏠 Ver Viviendas Reales", "callback_data": f"research_housing_{city_id}"}],
            [{"text": "💼 Ver Empleos para Mi Perfil", "callback_data": f"research_jobs_{city_id}"}],
            [{"text": "🎓 Ver Colegios", "callback_data": f"research_schools_{city_id}"}],
            [{"text": "🏪 Ver Negocios en Venta", "callback_data": f"research_business_{city_id}"}],
            [{"text": "📊 Ver Todo (Investigación Completa)", "callback_data": f"research_full_{city_id}"}],
            [{"text": "⬅️ Volver", "callback_data": f"city_select_{city_id}"}],
        ]
        
        await query.edit_message_text(
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=False
        )
    
    async def _show_city_plan(self, query, user_id: int, user: dict, city_id: str):
        """Muestra el plan detallado para una ciudad"""
        from telegram import InlineKeyboardMarkup
        
        preferences = user.get("migration_preferences", {})
        profile = user.get("profile", {})
        
        plan = generate_migration_plan(city_id, preferences, user)
        
        if "error" in plan:
            await query.answer("Ciudad no encontrada", show_alert=True)
            return
        
        # Mensaje principal
        msg = f"🏙️ *PLAN DE MIGRACIÓN: {plan['ciudad']}*\n\n"
        
        msg += f"📍 *Resumen*\n"
        msg += f"└ Población: {plan['resumen']['poblacion']:,}\n"
        msg += f"└ Clima: {plan['resumen']['clima'].capitalize()}\n"
        msg += f"└ Costo mensual: ${plan['resumen']['costo_mensual_estimado']:,}\n\n"
        
        msg += f"🏠 *Vivienda Recomendada*\n"
        msg += f"└ Tipo: {plan['vivienda']['tipo_recomendado'].capitalize()}\n"
        msg += f"└ Alquiler: ${plan['vivienda']['alquiler_estimado']:,}/mes\n"
        msg += f"└ Mejores barrios: {', '.join(plan['vivienda']['mejores_barrios'])}\n\n"
        
        msg += f"💰 *Presupuesto de Mudanza*\n"
        msg += f"└ Total estimado: *${plan['presupuesto_mudanza']['total_estimado']:,}*\n\n"
        
        msg += f"✅ *Pros:* {', '.join(plan['pros'][:3])}\n"
        msg += f"⚠️ *Contras:* {', '.join(plan['contras'][:3])}\n"
        
        keyboard = [
            [{"text": "🏠 Ver Barrios", "callback_data": f"city_plan_{city_id}_barrios"},
             {"text": "💰 Presupuesto", "callback_data": f"city_plan_{city_id}_presupuesto"}],
            [{"text": "🎓 Educación", "callback_data": f"city_plan_{city_id}_educacion"},
             {"text": "💼 Trabajo", "callback_data": f"city_plan_{city_id}_trabajo"}],
            [{"text": "📋 Primeros Pasos", "callback_data": f"city_plan_{city_id}_pasos"}],
            [{"text": "⬅️ Volver a ciudades", "callback_data": "city_back"}],
            [{"text": "✅ Elegir esta ciudad", "callback_data": f"city_confirm_{city_id}"}]
        ]
        
        await query.edit_message_text(
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def _show_plan_section(self, query, user_id: int, user: dict, city_id: str, section: str):
        """Muestra una sección específica del plan"""
        from telegram import InlineKeyboardMarkup
        
        city = CITIES_DATABASE.get(city_id)
        if not city:
            return
        
        preferences = user.get("migration_preferences", {})
        plan = generate_migration_plan(city_id, preferences, user)
        
        if section == "barrios":
            msg = f"🏠 *MEJORES BARRIOS EN {city['nombre'].upper()}*\n\n"
            for i, barrio in enumerate(city['mejores_barrios'], 1):
                msg += f"{i}. *{barrio}*\n"
            msg += f"\n💡 *Consejo:* {plan['vivienda']['consejo']}"
        
        elif section == "presupuesto":
            p = plan['presupuesto_mensual']
            pm = plan['presupuesto_mudanza']
            msg = f"💰 *PRESUPUESTO PARA {city['nombre'].upper()}*\n\n"
            msg += f"*Presupuesto Mensual:*\n"
            msg += f"└ 🏠 Alquiler: ${p['alquiler']:,}\n"
            msg += f"└ 💡 Utilities: ${p['utilities']:,}\n"
            msg += f"└ 🛒 Groceries: ${p['groceries']:,}\n"
            msg += f"└ 🚗 Transporte: ${p['transporte']:,}\n"
            msg += f"└ 🏥 Salud: ${p['salud']:,}\n"
            msg += f"└ 📝 Otros: ${p['otros']:,}\n"
            msg += f"*TOTAL: ${p['total']:,}/mes*\n\n"
            msg += f"*Presupuesto de Mudanza:*\n"
            msg += f"└ ✈️ Vuelos: ${pm['vuelos_familia']:,}\n"
            msg += f"└ 💵 Depósito: ${pm['deposito_apartamento']:,}\n"
            msg += f"└ 🛋️ Muebles: ${pm['muebles_basicos']:,}\n"
            msg += f"└ 🚗 Carro: ${pm['carro_usado']:,}\n"
            msg += f"└ 💰 Emergencia: ${pm['emergencia_3_meses']:,}\n"
            msg += f"*TOTAL MUDANZA: ${pm['total_estimado']:,}*"
        
        elif section == "educacion":
            msg = f"🎓 *EDUCACIÓN EN {city['nombre'].upper()}*\n\n"
            msg += f"*Mejores Escuelas:*\n"
            for esc in plan['educacion']['mejores_escuelas']:
                msg += f"• {esc}\n"
            msg += f"\n*Universidades:*\n"
            for uni in plan['educacion']['universidades']:
                msg += f"• {uni}\n"
        
        elif section == "trabajo":
            msg = f"💼 *TRABAJO EN {city['nombre'].upper()}*\n\n"
            msg += f"*Industrias Fuertes:*\n"
            for ind in plan['trabajo']['industrias_fuertes']:
                msg += f"• {ind.capitalize()}\n"
            msg += f"\n💡 *Consejo:* {plan['trabajo']['consejo']}"
        
        elif section == "pasos":
            msg = f"📋 *PRIMEROS PASOS EN {city['nombre'].upper()}*\n\n"
            for paso in plan['primeros_pasos']:
                msg += f"{paso}\n"
        
        else:
            msg = "Sección no encontrada"
        
        keyboard = [
            [{"text": "⬅️ Volver al plan", "callback_data": f"city_select_{city_id}"}]
        ]
        
        await query.edit_message_text(
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def _handle_research(self, query, user_id: int, data: str, user: dict):
        """Maneja la investigación de viviendas, empleos, colegios y negocios"""
        from telegram import InlineKeyboardMarkup
        
        # Parsear el callback: research_TYPE_CITYID
        parts = data.replace("research_", "").split("_")
        research_type = parts[0]
        city_id = parts[1] if len(parts) > 1 else ""
        
        city = CITIES_DATABASE.get(city_id)
        if not city:
            await query.answer("Ciudad no encontrada", show_alert=True)
            return
        
        city_name = city["nombre"].split(",")[0]
        state_code = city["estado"]
        
        # Obtener el motor de investigación
        research = get_research_engine()
        
        if research_type == "housing":
            await self._show_housing_research(query, user_id, user, city_id, city, research)
        elif research_type == "jobs":
            await self._show_jobs_research(query, user_id, user, city_id, city, research)
        elif research_type == "schools":
            await self._show_schools_research(query, user_id, user, city_id, city, research)
        elif research_type == "business":
            await self._show_business_research(query, user_id, user, city_id, city, research)
        elif research_type == "full":
            await self._show_full_research(query, user_id, user, city_id, city, research)
    
    async def _show_housing_research(self, query, user_id: int, user: dict, city_id: str, city: dict, research):
        """Muestra viviendas reales de la ciudad"""
        from telegram import InlineKeyboardMarkup
        
        city_name = city["nombre"].split(",")[0]
        state_code = city["estado"]
        
        # Obtener preferencias del usuario
        prefs = user.get("migration_preferences", {})
        max_rent = prefs.get("max_rent", 2500)
        bedrooms = prefs.get("bedrooms", 2)
        
        # Buscar propiedades
        properties = await research.search_properties(
            city=city_name,
            state=state_code,
            listing_type="rent",
            max_price=max_rent,
            bedrooms=bedrooms,
            limit=5
        )
        
        msg = f"🏠 *VIVIENDAS EN {city['nombre'].upper()}*\n\n"
        msg += f"📍 Mostrando opciones de alquiler\n"
        msg += f"💰 Presupuesto: hasta ${max_rent:,}/mes\n"
        msg += f"🛏️ Habitaciones: {bedrooms}+\n\n"
        
        if properties:
            for i, prop in enumerate(properties, 1):
                msg += f"*{i}. {prop.address}*\n"
                msg += f"   💰 ${prop.price:,}/mes\n"
                msg += f"   🛏️ {prop.bedrooms} hab | 🚿 {prop.bathrooms} baños | 📐 {prop.sqft:,} sqft\n"
                msg += f"   🚶 Walk: {prop.walk_score} | 🚇 Transit: {prop.transit_score}\n"
                msg += f"   🔗 [Ver en Zillow]({prop.zillow_url})\n\n"
        else:
            msg += "⚠️ No se encontraron propiedades con esos criterios.\n\n"
        
        msg += f"\n💡 *Tip:* Los mejores barrios son: {', '.join(city['mejores_barrios'][:3])}"
        
        keyboard = [
            [{"text": "💼 Ver Empleos", "callback_data": f"research_jobs_{city_id}"}],
            [{"text": "🎓 Ver Colegios", "callback_data": f"research_schools_{city_id}"}],
            [{"text": "🏪 Ver Negocios", "callback_data": f"research_business_{city_id}"}],
            [{"text": "⬅️ Volver", "callback_data": f"city_confirm_{city_id}"}],
        ]
        
        await query.edit_message_text(
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    
    async def _show_jobs_research(self, query, user_id: int, user: dict, city_id: str, city: dict, research):
        """Muestra empleos reales para el perfil del usuario"""
        from telegram import InlineKeyboardMarkup
        
        city_name = city["nombre"].split(",")[0]
        state_code = city["estado"]
        
        # Obtener profesión del usuario
        profile = user.get("profile", {})
        work = profile.get("work", {})
        profession = work.get("profession", "software engineer")
        
        # Buscar empleos
        jobs = await research.search_jobs(
            query=profession,
            location=f"{city_name}, {state_code}",
            limit=5
        )
        
        msg = f"💼 *EMPLEOS EN {city['nombre'].upper()}*\n\n"
        msg += f"🔍 Búsqueda: {profession}\n\n"
        
        if jobs:
            for i, job in enumerate(jobs, 1):
                salary_str = f"${job.salary_min:,} - ${job.salary_max:,}/año" if job.salary_min else "Salario no especificado"
                remote_str = "🏠 Remoto" if job.remote else "🏢 Presencial"
                visa_str = "✅ Patrocina visa" if job.visa_sponsorship else ""
                
                msg += f"*{i}. {job.title}*\n"
                msg += f"   🏢 {job.company}\n"
                msg += f"   💰 {salary_str}\n"
                msg += f"   {remote_str} {visa_str}\n"
                msg += f"   🔗 [Aplicar]({job.apply_url})\n\n"
        else:
            msg += "⚠️ No se encontraron empleos para tu perfil.\n\n"
        
        msg += f"\n💡 *Industrias fuertes:* {', '.join(city['industrias_fuertes'][:4])}"
        
        keyboard = [
            [{"text": "🏠 Ver Viviendas", "callback_data": f"research_housing_{city_id}"}],
            [{"text": "🎓 Ver Colegios", "callback_data": f"research_schools_{city_id}"}],
            [{"text": "🏪 Ver Negocios", "callback_data": f"research_business_{city_id}"}],
            [{"text": "⬅️ Volver", "callback_data": f"city_confirm_{city_id}"}],
        ]
        
        await query.edit_message_text(
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    
    async def _show_schools_research(self, query, user_id: int, user: dict, city_id: str, city: dict, research):
        """Muestra colegios de la ciudad"""
        from telegram import InlineKeyboardMarkup
        
        city_name = city["nombre"].split(",")[0]
        state_code = city["estado"]
        
        # Buscar colegios
        schools = await research.search_schools(
            city=city_name,
            state=state_code,
            limit=5
        )
        
        msg = f"🎓 *COLEGIOS EN {city['nombre'].upper()}*\n\n"
        
        if schools:
            for i, school in enumerate(schools, 1):
                stars = "⭐" * int(school.rating / 2)
                type_emoji = {"🏫": "public", "🎒": "private", "📚": "charter"}.get(school.school_type, "🏫")
                
                msg += f"*{i}. {school.name}*\n"
                msg += f"   📊 Rating: {school.rating}/10 {stars}\n"
                msg += f"   📚 Grados: {school.grade_range}\n"
                msg += f"   👨‍🎓 {school.student_count:,} estudiantes\n"
                msg += f"   🌟 Programas: {', '.join(school.programs[:3])}\n"
                msg += f"   🔗 [Sitio web]({school.website})\n\n"
        else:
            msg += "⚠️ No se encontraron colegios.\n\n"
        
        msg += f"\n💡 *Mejores escuelas de la zona:* {', '.join(city['mejores_escuelas'][:3])}"
        
        keyboard = [
            [{"text": "🏠 Ver Viviendas", "callback_data": f"research_housing_{city_id}"}],
            [{"text": "💼 Ver Empleos", "callback_data": f"research_jobs_{city_id}"}],
            [{"text": "🏪 Ver Negocios", "callback_data": f"research_business_{city_id}"}],
            [{"text": "⬅️ Volver", "callback_data": f"city_confirm_{city_id}"}],
        ]
        
        await query.edit_message_text(
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    
    async def _show_business_research(self, query, user_id: int, user: dict, city_id: str, city: dict, research):
        """Muestra negocios en venta"""
        from telegram import InlineKeyboardMarkup
        
        city_name = city["nombre"].split(",")[0]
        state_code = city["estado"]
        
        # Buscar negocios
        businesses = await research.search_businesses(
            location=f"{city_name}, {state_code}",
            max_price=300000,
            limit=5
        )
        
        msg = f"🏪 *NEGOCIOS EN VENTA EN {city['nombre'].upper()}*\n\n"
        msg += f"💰 Due Diligence disponible por $100 USD\n\n"
        
        if businesses:
            for i, biz in enumerate(businesses, 1):
                roi = (biz.annual_profit / biz.asking_price * 100) if biz.asking_price > 0 else 0
                
                msg += f"*{i}. {biz.name}*\n"
                msg += f"   💰 Precio: ${biz.asking_price:,}\n"
                msg += f"   📈 Ingresos: ${biz.annual_revenue:,}/año\n"
                msg += f"   💵 Ganancia: ${biz.annual_profit:,}/año\n"
                msg += f"   📊 ROI: {roi:.1f}%\n"
                msg += f"   👥 {biz.employees} empleados | 📅 {biz.years_established} años\n"
                msg += f"   🔗 [Ver detalles]({biz.listing_url})\n\n"
        else:
            msg += "⚠️ No se encontraron negocios en venta.\n\n"
        
        msg += f"\n💡 *Tip:* Con visa E-2 puedes invertir y manejar tu propio negocio."
        
        keyboard = [
            [{"text": "🏠 Ver Viviendas", "callback_data": f"research_housing_{city_id}"}],
            [{"text": "💼 Ver Empleos", "callback_data": f"research_jobs_{city_id}"}],
            [{"text": "🎓 Ver Colegios", "callback_data": f"research_schools_{city_id}"}],
            [{"text": "⬅️ Volver", "callback_data": f"city_confirm_{city_id}"}],
        ]
        
        await query.edit_message_text(
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    
    async def _show_full_research(self, query, user_id: int, user: dict, city_id: str, city: dict, research):
        """Muestra investigación completa de la ciudad"""
        from telegram import InlineKeyboardMarkup
        
        city_name = city["nombre"].split(",")[0]
        state_code = city["estado"]
        
        # Obtener información de comunidad
        community = await research.get_community_info(city_name, state_code)
        
        msg = f"📊 *INVESTIGACIÓN COMPLETA: {city['nombre'].upper()}*\n\n"
        
        # Foto de la ciudad
        msg += f"📸 *Foto:* {city.get('foto_url', '')}\n\n"
        
        # Descripción
        msg += f"📝 *{city.get('descripcion', '')}*\n\n"
        
        # Comunidad
        msg += f"👥 *COMUNIDAD:*\n"
        msg += f"• Población latina: {community.latino_population_pct:.1f}%\n"
        msg += f"• Ingreso medio: ${community.median_income:,}/año\n"
        msg += f"• Alquiler medio: ${community.median_rent:,}/mes\n"
        msg += f"• Seguridad: {100 - community.crime_index}/100\n"
        msg += f"• Restaurantes latinos: {community.restaurants_latino}\n"
        msg += f"• Iglesias en español: {community.churches_spanish}\n\n"
        
        # Scores
        msg += f"📊 *SCORES:*\n"
        msg += f"• 🚶 Walk Score: {community.walk_score}\n"
        msg += f"• 🚇 Transit Score: {community.transit_score}\n"
        msg += f"• 🚴 Bike Score: {community.bike_score}\n\n"
        
        # Costos
        costs = city["costo_vida_mensual"]
        msg += f"💰 *COSTOS MENSUALES:*\n"
        msg += f"• Alquiler 2BR: ${costs['alquiler_2br']:,}\n"
        msg += f"• Utilities: ${costs['utilities']:,}\n"
        msg += f"• Comida: ${costs['groceries']:,}\n"
        msg += f"• Transporte: ${costs['transporte']:,}\n"
        msg += f"• *TOTAL: ${costs['total_estimado']:,}/mes*\n\n"
        
        # Pros y Contras
        msg += f"✅ *PROS:* {', '.join(city['pros'][:3])}\n"
        msg += f"⚠️ *CONTRAS:* {', '.join(city['contras'][:3])}"
        
        keyboard = [
            [{"text": "🏠 Ver Viviendas", "callback_data": f"research_housing_{city_id}"}],
            [{"text": "💼 Ver Empleos", "callback_data": f"research_jobs_{city_id}"}],
            [{"text": "🎓 Ver Colegios", "callback_data": f"research_schools_{city_id}"}],
            [{"text": "🏪 Ver Negocios", "callback_data": f"research_business_{city_id}"}],
            [{"text": "⬅️ Volver", "callback_data": f"city_confirm_{city_id}"}],
        ]
        
        await query.edit_message_text(
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=False
        )
    
    async def start_migration_plan(self, query_or_update, user_id: int, user: dict):
        """Inicia el flujo del plan de migración integral"""
        from telegram import InlineKeyboardMarkup
        
        # Resetear preferencias anteriores
        user["migration_preferences"] = {}
        encrypted_data = encrypt_user_data(user)
        save_user_data(user_id, encrypted_data)
        
        # Primera pregunta
        first_q = MIGRATION_PLAN_QUESTIONS[0]
        q_text, keyboard = get_question_keyboard(first_q)
        
        msg = (
            "🌎 *PLAN INTEGRAL DE MIGRACIÓN*\n\n"
            "Vamos a encontrar la ciudad perfecta para ti.\n"
            "Te haré algunas preguntas sobre tus preferencias.\n\n"
            f"{q_text}"
        )
        
        if hasattr(query_or_update, 'edit_message_text'):
            await query_or_update.edit_message_text(
                msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query_or_update.message.reply_text(
                msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    async def _ask_migration_reason(self, query):
        await query.edit_message_text(
            "🎯 *FASE 3: Objetivos*\n\n"
            "¿Principal razón para migrar?",
            parse_mode='Markdown',
            reply_markup=self._kb([
                ("💼 Trabajo", "Trabajo"),
                ("📚 Estudios", "Estudios"),
                ("🏠 Calidad de vida", "Calidad de vida"),
                ("👨‍👩‍👧 Familia", "Familia"),
                ("🔒 Seguridad", "Seguridad")
            ])
        )
    
    # ============== V2.1 INTENT ACTION EXECUTOR ==============
    
    async def _execute_intent_action(self, update, context, detected: DetectedIntent, user: dict) -> bool:
        """
        Ejecuta una acción basada en la intención detectada.
        Retorna True si se ejecutó una acción, False si debe continuar con IA.
        """
        user_id = update.effective_user.id
        intent = detected.intent
        entities = detected.entities
        
        try:
            # EXPLORACIÓN DE CIUDADES
            if intent == Intent.EXPLORE_CITIES:
                await self._cmd_explore(update, context)
                return True
            
            elif intent == Intent.EXPLORE_STATE:
                state_code = entities.get("state")
                if state_code:
                    user["selected_route"] = user.get("selected_route", {})
                    user["selected_route"]["state"] = state_code
                    save_user_data(user_id, encrypt_user_data(user))
                    await self._show_cities_for_state(update, user_id, state_code)
                    return True
            
            # BÚSQUEDA DE VIVIENDAS
            elif intent == Intent.SEARCH_HOUSING:
                city = entities.get("city")
                if city:
                    user["selected_route"] = user.get("selected_route", {})
                    user["selected_route"]["city"] = city
                    # Intentar detectar estado
                    for c in CITIES_TOP_1000.values():
                        if c["name"].lower() == city.lower():
                            user["selected_route"]["state"] = c["state_code"]
                            break
                    save_user_data(user_id, encrypt_user_data(user))
                await self._cmd_housing(update, context)
                return True
            
            # BÚSQUEDA DE EMPLEOS
            elif intent == Intent.SEARCH_JOBS:
                await self._cmd_jobs(update, context)
                return True
            
            # BÚSQUEDA DE ESCUELAS
            elif intent == Intent.SEARCH_SCHOOLS:
                await self._cmd_schools(update, context)
                return True
            
            # BÚSQUEDA DE UNIVERSIDADES
            elif intent == Intent.SEARCH_UNIVERSITIES:
                await self._cmd_universities(update, context)
                return True
            
            # COMPARAR CIUDADES
            elif intent == Intent.COMPARE_CITIES:
                city1 = entities.get("city1")
                city2 = entities.get("city2")
                if city1 and city2:
                    await self._compare_cities_action(update, city1, city2)
                    return True
            
            # INFORMACIÓN DE CIUDAD
            elif intent == Intent.INFO_CITY:
                city_name = entities.get("city")
                if city_name:
                    await self._show_city_info(update, city_name)
                    return True
            
            # INFORMACIÓN DE VISA
            elif intent == Intent.INFO_VISA:
                await self._cmd_score(update, context)
                return True
            
            # COSTOS
            elif intent == Intent.INFO_COSTS:
                await self._cmd_costs(update, context)
                return True
            
            # INICIAR FLUJO
            elif intent == Intent.START_FLOW:
                await self._cmd_flow(update, context)
                return True
            
            # VER PROGRESO
            elif intent == Intent.CHECK_PROGRESS:
                await self._cmd_status(update, context)
                return True
            
            # VER PERFIL
            elif intent == Intent.VIEW_PROFILE:
                await self._cmd_profile(update, context)
                return True
            
            # PRECIOS
            elif intent == Intent.VIEW_PRICES:
                await self._cmd_prices(update, context)
                return True
            
            # AYUDA
            elif intent == Intent.HELP:
                await self._cmd_help(update, context)
                return True
            
            # SOS
            elif intent == Intent.SOS:
                await self._cmd_sos(update, context)
                return True
            
            # SALUDOS - Responder de forma PROACTIVA, guiando al usuario
            elif intent == Intent.GREETING:
                name = user.get("profile", {}).get("personal", {}).get("name", "")
                flow_state = user.get("flow_state", "")
                has_profile = bool(user.get("profile", {}).get("personal", {}).get("country_origin"))
                
                # Si es usuario NUEVO o sin perfil -> Iniciar flujo de descubrimiento
                if not has_profile:
                    greeting = f"¡Hola{' ' + name if name else ''}! 👋" if name else "¡Hola! 👋"
                    await update.message.reply_text(
                        f"{greeting}\n\n"
                        "Soy MigPAL, tu consultor de migración. 🌍\n\n"
                        "Voy a guiarte paso a paso en tu proceso de migración. "
                        "Mi filosofía es simple:\n\n"
                        "💡 *\"La visa es el VEHÍCULO, no el DESTINO\"*\n\n"
                        "Primero vamos a definir tu plan de vida en USA, "
                        "y luego encontraremos la mejor ruta migratoria para ti.\n\n"
                        "¿Empezamos?",
                        parse_mode='Markdown',
                        reply_markup=self._kb([
                            [("✅ Sí, empecemos", "flow_start_discovery")],
                            [("ℹ️ Primero cuéntame más", "flow_explain_process")],
                        ])
                    )
                else:
                    # Usuario con perfil -> Retomar donde quedó
                    greeting = f"¡Hola de nuevo, {name}! 👋" if name else "¡Hola de nuevo! 👋"
                    
                    # Determinar en qué fase está
                    route = user.get("selected_route", {})
                    city = route.get("city", "")
                    state = route.get("state", "")
                    visa = route.get("visa_type", "")
                    
                    if not state:
                        next_step = "Continuemos definiendo tu ubicación ideal en USA."
                        next_action = "flow_continue_location"
                        next_label = "🗺️ Elegir ubicación"
                    elif not city:
                        next_step = f"Ya elegiste {state}. Ahora vamos a explorar ciudades."
                        next_action = "flow_continue_city"
                        next_label = "🏙️ Explorar ciudades"
                    elif not visa:
                        next_step = f"Ya elegiste {city}, {state}. Ahora analicemos tu mejor ruta de visa."
                        next_action = "flow_continue_visa"
                        next_label = "📝 Analizar visa"
                    else:
                        next_step = f"Tu plan: {city}, {state} con visa {visa}. ¿Listo para el siguiente paso?"
                        next_action = "flow_continue_execution"
                        next_label = "🚀 Continuar proceso"
                    
                    await update.message.reply_text(
                        f"{greeting}\n\n"
                        f"{next_step}",
                        parse_mode='Markdown',
                        reply_markup=self._kb([
                            [(next_label, next_action)],
                            [("📊 Ver mi progreso", "show_progress")],
                        ])
                    )
                return True
            
            # AGRADECIMIENTOS
            elif intent == Intent.THANKS:
                await update.message.reply_text(
                    "¡De nada! 😊 Estoy aquí para ayudarte.\n\n"
                    "¿Hay algo más en lo que pueda asistirte?"
                )
                return True
        
        except Exception as e:
            logger.error(f"Error executing intent action: {e}")
        
        # No se ejecutó ninguna acción, continuar con IA
        return False
    
    async def _cmd_schools(self, update, context):
        """Buscar escuelas"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        route = user.get("selected_route", {})
        
        city = route.get("city", "")
        state = route.get("state", "")
        
        if not city:
            await update.message.reply_text(
                "🏫 *BÚSQUEDA DE ESCUELAS*\n\n"
                "Primero necesitas seleccionar una ciudad.\n\n"
                "Usa /explorar para elegir tu ciudad destino.",
                parse_mode='Markdown'
            )
            return
        
        # Buscar escuelas
        schools = search_schools(city, state, limit=10)
        
        if not schools:
            await update.message.reply_text(
                f"⚠️ No encontramos escuelas en {city}.\n"
                "Intenta con otra ciudad."
            )
            return
        
        msg = f"🏫 *ESCUELAS EN {city.upper()}*\n\n"
        
        for i, school in enumerate(schools[:5], 1):
            stars = star_rating(school.overall_rating * 10)
            category = "🏢" if school.category.value == "public" else "🏛️"
            
            msg += f"{i}. {category} *{school.name}*\n"
            msg += f"   {stars} {school.overall_rating}/10\n"
            msg += f"   📚 Grados: {school.grades}\n"
            msg += f"   👥 {school.students} estudiantes\n"
            
            programs = []
            if school.has_esl:
                programs.append("🌐 ESL")
            if school.has_gifted:
                programs.append("🧠 Gifted")
            if school.has_stem:
                programs.append("🔬 STEM")
            if programs:
                msg += f"   {' '.join(programs)}\n"
            msg += "\n"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def _cmd_universities(self, update, context):
        """Buscar universidades"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        route = user.get("selected_route", {})
        
        state = route.get("state", "")
        
        # Buscar universidades
        if state:
            universities = search_universities(state=state, limit=10)
        else:
            universities = search_universities(limit=10)
        
        if not universities:
            await update.message.reply_text(
                "⚠️ No encontramos universidades.\n"
                "Intenta seleccionar un estado primero con /explorar."
            )
            return
        
        msg = "🎓 *UNIVERSIDADES*\n\n"
        if state:
            msg = f"🎓 *UNIVERSIDADES EN {state}*\n\n"
        
        for i, uni in enumerate(universities[:5], 1):
            public_str = "🏢 Pública" if uni.is_public else "🏛️ Privada"
            
            msg += f"{i}. *{uni.name}*\n"
            msg += f"   🏆 Ranking: #{uni.national_rank}\n"
            msg += f"   {public_str}\n"
            msg += f"   💰 Tuition: ${uni.tuition_out_state:,}/año\n"
            msg += f"   🎯 Aceptación: {uni.acceptance_rate}%\n"
            msg += f"   💼 Salario egresados: ${uni.avg_starting_salary:,}\n\n"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def _compare_cities_action(self, update, city1_name: str, city2_name: str):
        """Compara dos ciudades con gráfico interactivo"""
        # Buscar ciudades
        city1_results = search_cities(city1_name)
        city2_results = search_cities(city2_name)
        
        if not city1_results:
            await update.message.reply_text(f"⚠️ No encontré la ciudad '{city1_name}'")
            return
        
        if not city2_results:
            await update.message.reply_text(f"⚠️ No encontré la ciudad '{city2_name}'")
            return
        
        city1 = city1_results[0]
        city2 = city2_results[0]
        
        # Comparar
        result = compare_cities(city1, city2)
        
        # Enviar mensaje de texto primero
        await update.message.reply_text(
            result.formatted_message,
            parse_mode='Markdown'
        )
        
        # Generar y enviar gráfico de comparación
        try:
            city1_scores = city1.get("scores", {})
            city2_scores = city2.get("scores", {})
            city1_display = city1.get("name", city1_name)
            city2_display = city2.get("name", city2_name)
            
            chart_bytes = generate_comparison_chart(
                city1_display, city1_scores,
                city2_display, city2_scores
            )
            
            if chart_bytes:
                from io import BytesIO
                photo = BytesIO(chart_bytes)
                photo.name = "comparison_chart.png"
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"📊 Gráfico comparativo: {city1_display} vs {city2_display}"
                )
        except Exception as e:
            logger.warning(f"No se pudo generar gráfico de comparación: {e}")
    
    async def _show_city_info(self, update, city_name: str):
        """Muestra información completa de una ciudad con gráfico radar"""
        # Buscar ciudad
        results = search_cities(city_name)
        
        if not results:
            await update.message.reply_text(f"⚠️ No encontré la ciudad '{city_name}'")
            return
        
        city = results[0]
        
        # Formatear información completa
        messages = format_city_full(city)
        
        # Enviar cada mensaje
        for msg in messages:
            await update.message.reply_text(msg, parse_mode='Markdown')
            await asyncio.sleep(0.3)  # Pequeña pausa entre mensajes
        
        # Generar y enviar gráfico radar de la ciudad
        try:
            city_scores = city.get("scores", {})
            city_display = city.get("name", city_name)
            
            radar_bytes = generate_radar_chart(city_display, city_scores)
            
            if radar_bytes:
                from io import BytesIO
                photo = BytesIO(radar_bytes)
                photo.name = "city_radar.png"
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"📊 Perfil de {city_display}"
                )
        except Exception as e:
            logger.warning(f"No se pudo generar gráfico radar: {e}")
    
    @safe_async_handler
    async def _cmd_compare(self, update, context):
        """Comando /comparar - Compara dos ciudades"""
        user_id = update.effective_user.id
        
        # Obtener argumentos del comando
        args = context.args if context.args else []
        
        if len(args) < 2:
            await update.message.reply_text(
                "⚔️ *COMPARAR CIUDADES*\n\n"
                "Uso: /comparar [ciudad1] [ciudad2]\n\n"
                "Ejemplos:\n"
                "• /comparar Miami Orlando\n"
                "• /comparar Austin Dallas\n"
                "• /comparar Seattle Denver\n\n"
                "O simplemente escribe:\n"
                "_\"Compara Miami con Orlando\"_",
                parse_mode='Markdown'
            )
            return
        
        city1_name = args[0]
        city2_name = args[1] if args[1].lower() not in ["con", "vs", "y", "and"] else args[2] if len(args) > 2 else args[1]
        
        await self._compare_cities_action(update, city1_name, city2_name)
    
    @safe_async_handler
    async def _cmd_pdf(self, update, context):
        """Comando /pdf - Genera reportes PDF"""
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        
        await update.message.reply_text(
            "📄 *GENERAR REPORTE PDF*\n\n"
            "Selecciona el tipo de reporte:",
            parse_mode='Markdown',
            reply_markup=self._kb([
                [("📊 Diagnóstico", "pdf_diagnostic"), ("🏙️ Ciudad", "pdf_city")],
                [("⚔️ Comparación", "pdf_comparison"), ("🗺️ Plan Migración", "pdf_plan")],
                [("📋 Checklist Docs", "pdf_checklist")],
            ])
        )
    
    async def _generate_and_send_pdf(self, update, pdf_type: str, user: dict):
        """Genera y envía un PDF"""
        user_id = update.effective_user.id
        
        try:
            pdf_bytes = None
            filename = "reporte.pdf"
            
            if pdf_type == "diagnostic":
                # Generar PDF de diagnóstico
                client_name = user.get("profile", {}).get("personal", {}).get("name", "Cliente")
                visa_analysis = {
                    "recommended_visa": user.get("selected_route", {}).get("visa_type", "Por determinar"),
                    "probability": user.get("visa_probability", 50),
                    "timeline": "6-12 meses",
                }
                recommendations = [
                    "Completar el perfilamiento detallado",
                    "Reunir documentos base según checklist",
                    "Definir ciudad destino",
                    "Evaluar opciones de visa",
                ]
                pdf_bytes = generate_diagnostic_pdf(client_name, user, visa_analysis, recommendations)
                filename = f"diagnostico_{client_name.replace(' ', '_')}.pdf"
            
            elif pdf_type == "city":
                # Generar PDF de ciudad
                route = user.get("selected_route", {})
                city_name = route.get("city", "")
                
                if not city_name:
                    await update.message.reply_text(
                        "⚠️ Primero selecciona una ciudad con /explorar"
                    )
                    return
                
                city_results = search_cities(city_name)
                if city_results:
                    pdf_bytes = generate_city_pdf(city_results[0])
                    filename = f"ciudad_{city_name.replace(' ', '_')}.pdf"
            
            elif pdf_type == "comparison":
                # Necesita dos ciudades guardadas
                favorites = user.get("favorites", {}).get("cities", [])
                if len(favorites) < 2:
                    await update.message.reply_text(
                        "⚠️ Necesitas al menos 2 ciudades favoritas.\n"
                        "Usa /explorar y marca ciudades con ❤️"
                    )
                    return
                
                city1 = search_cities(favorites[0])
                city2 = search_cities(favorites[1])
                if city1 and city2:
                    pdf_bytes = generate_comparison_pdf(city1[0], city2[0])
                    filename = f"comparacion_{favorites[0]}_{favorites[1]}.pdf"
            
            elif pdf_type == "plan":
                # Plan de migración completo
                client_name = user.get("profile", {}).get("personal", {}).get("name", "Cliente")
                route = user.get("selected_route", {})
                city_name = route.get("city", "")
                
                if not city_name:
                    await update.message.reply_text(
                        "⚠️ Primero completa tu perfil y selecciona una ciudad."
                    )
                    return
                
                city_results = search_cities(city_name)
                city_data = city_results[0] if city_results else {}
                
                visa_info = {
                    "type": route.get("visa_type", "Por determinar"),
                    "probability": user.get("visa_probability", 50),
                    "processing_time": "6-12 meses",
                    "cost": 5000,
                }
                
                timeline = [
                    {"phase": "1. Diagnóstico", "description": "Evaluación inicial", "duration": "1 semana"},
                    {"phase": "2. Perfilamiento", "description": "Definición de perfil", "duration": "2 semanas"},
                    {"phase": "3. Documentos", "description": "Recopilación", "duration": "1-2 meses"},
                    {"phase": "4. Aplicación", "description": "Envío de visa", "duration": "Variable"},
                    {"phase": "5. Establecimiento", "description": "Llegada y setup", "duration": "1-3 meses"},
                ]
                
                pdf_bytes = generate_migration_plan_pdf(client_name, user, city_data, visa_info, timeline)
                filename = f"plan_migracion_{client_name.replace(' ', '_')}.pdf"
            
            if pdf_bytes:
                # Enviar el PDF
                from telegram import InputFile
                await update.message.reply_document(
                    document=InputFile(io.BytesIO(pdf_bytes), filename=filename),
                    caption=f"📄 *{filename}*\n\nGenerado por MigPAL",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "⚠️ No se pudo generar el PDF. Intenta de nuevo."
                )
        
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            await update.message.reply_text(
                f"⚠️ Error al generar PDF: {str(e)[:100]}"
            )
    
    # ============== FORM STATE HANDLER ==============
    
    async def _handle_form_state(self, update, user_id: int, user: dict, state: str, text: str) -> bool:
        """
        Procesa estados de formulario directamente.
        Retorna True si el estado fue manejado, False si no.
        """
        # Get user's language for translations
        lang = user.get("language", "en")
        
        try:
            # === NAME ===
            if state == STATE_NAME:
                # V3.0.3 - Use NameValidator for improved validation
                is_valid, result = NameValidator.is_valid_name(text)
                
                if not is_valid:
                    if result == "too_short":
                        await update.message.reply_text(get_text("name_too_short", lang))
                    elif result == "empty":
                        await update.message.reply_text(get_text("name_too_short", lang))
                    elif result == "not_a_name":
                        # V3.0.9 - ANTI-LOOP: Texto que no parece un nombre
                        if lang == "es":
                            await update.message.reply_text(
                                "🙏 Por favor, escribe tu nombre completo.\n\n"
                                "Ejemplo: *Juan Carlos Pérez*",
                                parse_mode='Markdown'
                            )
                        else:
                            await update.message.reply_text(
                                "🙏 Please write your full name.\n\n"
                                "Example: *John Michael Smith*",
                                parse_mode='Markdown'
                            )
                    else:
                        await update.message.reply_text(get_text("name_too_short", lang))
                    return True
                
                name = result  # Cleaned name
                
                # V3.0.3 - DEDUPE: Check if same name already exists
                existing_name = user.get("profile", {}).get("personal", {}).get("name", "")
                if NameValidator.is_duplicate(name, existing_name):
                    # Same name, skip confirmation and continue
                    await update.message.reply_text(
                        get_text("name_skip_confirm", lang).format(name=name),
                        parse_mode='Markdown'
                    )
                    # Continue to next step
                    set_state(user_id, STATE_BIRTH_DATE)
                    await update.message.reply_text(get_text("ask_birthdate_full", lang))
                    return True
                
                # V3.0.3 - SIMPLIFIED 1-CLICK CONFIRMATION
                # Skip confirmation if name looks well-formatted
                if NameValidator.should_skip_confirmation(name):
                    # Auto-confirm well-formatted names
                    user["profile"]["personal"]["name"] = name
                    encrypted_data = encrypt_user_data(user)
                    save_user_data(user_id, encrypted_data)
                    
                    # Log transition
                    get_transition_logger().log_transition(
                        user_id, STATE_NAME, STATE_BIRTH_DATE, 
                        "name_auto_confirmed", {"name": name}
                    )
                    
                    # Show confirmation and continue
                    await update.message.reply_text(
                        get_text("name_skip_confirm", lang).format(name=name),
                        parse_mode='Markdown'
                    )
                    set_state(user_id, STATE_BIRTH_DATE)
                    await update.message.reply_text(get_text("ask_birthdate_full", lang))
                    return True
                
                # Guardar nombre pendiente para confirmación
                user["_pending_name"] = name
                encrypted_data = encrypt_user_data(user)
                save_user_data(user_id, encrypted_data)
                
                # V3.0.3 - SIMPLIFIED 1-CLICK CONFIRMATION with inline buttons
                confirm_text = get_text("name_1click_confirm", lang).format(name=name)
                yes_text = get_text("yes_correct", lang)
                no_text = get_text("no_change", lang)
                
                await update.message.reply_text(
                    confirm_text,
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [(yes_text, "confirm_name_yes"), (no_text, "confirm_name_no")]
                    ])
                )
                set_state(user_id, "confirm_name")
                return True
            
            # === CONFIRM NAME (nuevo estado) ===
            elif state == "confirm_name":
                # V3.0.9 - ANTI-LOOP: Detectar si el texto es una pregunta/confusión
                # en lugar de un nombre real
                text_lower = text.lower().strip()
                
                # Patrones que indican confusión, no un nombre
                confusion_patterns = [
                    '?', 'qué', 'que', 'cual', 'como', 'por qué', 'porque',
                    'ajá', 'aja', 'hola', 'si', 'no', 'ok', 'vale', 'bueno',
                    'entiendo', 'explica', 'dime', 'cuál', 'cómo', 'what',
                    'why', 'how', 'yes', 'hello', 'hi', 'perfil', 'visa'
                ]
                
                is_confusion = any(p in text_lower for p in confusion_patterns)
                is_too_short = len(text.strip()) < 3
                is_single_word_question = text_lower.endswith('?')
                
                if is_confusion or is_too_short or is_single_word_question:
                    # El usuario está confundido, recordarle que use los botones
                    pending_name = user.get("_pending_name", "")
                    if not pending_name:
                        pending_name = user.get("profile", {}).get("personal", {}).get("name", "")
                    
                    if pending_name:
                        # Mostrar de nuevo la confirmación con botones
                        yes_text = get_text("yes_correct", lang)
                        no_text = get_text("no_change", lang)
                        
                        await update.message.reply_text(
                            f"👆 Por favor usa los botones de arriba.\n\n"
                            f"¿Tu nombre es *{pending_name}*?",
                            parse_mode='Markdown',
                            reply_markup=self._kb([
                                [(yes_text, "confirm_name_yes"), (no_text, "confirm_name_no")]
                            ])
                        )
                    else:
                        # No hay nombre pendiente, pedir nombre de nuevo
                        set_state(user_id, STATE_NAME)
                        await update.message.reply_text(
                            get_text("ask_name", lang)
                        )
                    return True
                
                # Si parece un nombre real, procesarlo como nuevo nombre
                return await self._handle_form_state(update, user_id, user, STATE_NAME, text)
            
            # === BIRTH DATE ===
            elif state == STATE_BIRTH_DATE:
                user["profile"]["personal"]["birth_date"] = text
                save_user_data(user_id, user)
                set_state(user_id, STATE_NATIONALITY)
                await update.message.reply_text(
                    "¿Cuál es tu nacionalidad?",
                    reply_markup=self._kb([
                        [("🇨🇴 Colombiano", "Colombiano"), ("🇲🇽 Mexicano", "Mexicano")],
                        [("🇻🇪 Venezolano", "Venezolano"), ("🇦🇷 Argentino", "Argentino")],
                        [("🇵🇪 Peruano", "Peruano"), ("🇪🇨 Ecuatoriano", "Ecuatoriano")],
                        [("🌎 Otra", "Otra")]
                    ])
                )
                return True
            
            # === CURRENT CITY ===
            elif state == STATE_CURRENT_CITY:
                user["profile"]["personal"]["current_city"] = text
                save_user_data(user_id, user)
                set_state(user_id, STATE_EMAIL)
                await update.message.reply_text("📧 ¿Cuál es tu correo electrónico?")
                return True
            
            # === EMAIL ===
            elif state == STATE_EMAIL:
                user["profile"]["personal"]["email"] = text
                save_user_data(user_id, user)
                set_state(user_id, STATE_PHONE)
                await update.message.reply_text("📱 ¿Tu número de teléfono? (con código de país)")
                return True
            
            # === PHONE ===
            elif state == STATE_PHONE:
                user["profile"]["personal"]["phone"] = text
                save_user_data(user_id, user)
                set_state(user_id, STATE_EDUCATION_LEVEL)
                await update.message.reply_text(
                    "🎓 ¿Cuál es tu nivel educativo más alto?",
                    reply_markup=self._kb([
                        [("📚 Bachillerato", "Bachillerato"), ("📖 Técnico", "Técnico")],
                        [("🎓 Universitario", "Universitario"), ("📜 Especialización", "Especialización")],
                        [("🏅 Maestría", "Maestría"), ("🏆 Doctorado", "Doctorado")]
                    ])
                )
                return True
            
            # === EDUCATION CAREER ===
            elif state == STATE_EDUCATION_CAREER:
                user["profile"]["education"]["career"] = text
                save_user_data(user_id, user)
                set_state(user_id, STATE_WORK_STATUS)
                await update.message.reply_text(
                    "¿Cuál es tu situación laboral actual?",
                    reply_markup=self._kb([
                        ("👔 Empleado", "Empleado"),
                        ("🏢 Independiente/Freelance", "Independiente"),
                        ("🚀 Empresario/Dueño", "Empresario"),
                        ("📚 Estudiante", "Estudiante"),
                        ("🔍 Buscando empleo", "Desempleado")
                    ])
                )
                return True
            
            # === PROFESSION ===
            elif state == STATE_PROFESSION:
                user["profile"]["work"]["profession"] = text
                save_user_data(user_id, user)
                set_state(user_id, STATE_WORK_EXPERIENCE)
                await update.message.reply_text(
                    "¿Cuántos años de experiencia tienes?",
                    reply_markup=self._kb([
                        [("< 1 año", "<1"), ("1-3 años", "1-3"), ("3-5 años", "3-5")],
                        [("5-10 años", "5-10"), ("10-15 años", "10-15"), ("> 15 años", ">15")]
                    ])
                )
                return True
            
            # === LINKEDIN ===
            elif state == STATE_LINKEDIN:
                if text.lower() not in ["omitir", "no", "skip", "-"]:
                    user["profile"]["work"]["linkedin"] = text
                save_user_data(user_id, user)
                # Continuar con el flujo proactivo
                await update.message.reply_text(
                    "✅ *¡Perfil básico completado!*\n\n"
                    "Ahora vamos a definir tu plan de migración.\n\n"
                    "¿Empezamos?",
                    parse_mode='Markdown',
                    reply_markup=self._kb([
                        [("✅ Sí, empecemos", "flow_start_discovery")],
                    ])
                )
                set_state(user_id, STATE_START)
                return True
            
            # === COMPANY ===
            elif state == STATE_COMPANY:
                user["profile"]["work"]["company"] = text
                save_user_data(user_id, user)
                set_state(user_id, STATE_SALARY)
                await update.message.reply_text(
                    "¿Cuál es tu salario mensual aproximado (en USD)?",
                    reply_markup=self._kb([
                        [("< $1,000", "<1000"), ("$1,000-$2,000", "1000-2000")],
                        [("$2,000-$5,000", "2000-5000"), ("$5,000-$10,000", "5000-10000")],
                        [("> $10,000", ">10000"), ("🔒 Prefiero no decir", "private")]
                    ])
                )
                return True
            
            # === SALARY ===
            elif state == STATE_SALARY:
                user["profile"]["work"]["salary"] = text
                save_user_data(user_id, user)
                # Continuar con flujo
                await update.message.reply_text(
                    "✅ Información guardada.\n\n"
                    "Continuemos con tu plan de migración.",
                    reply_markup=self._kb([
                        [("▶️ Continuar", "flow_start_discovery")],
                    ])
                )
                set_state(user_id, STATE_START)
                return True
            
            # === OTROS ESTADOS ===
            # Para estados no manejados explícitamente, guardar y continuar
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error handling form state {state}: {e}")
            return False
    
    # ============== MESSAGE HANDLER ==============
    
    @global_error_handler
    async def _handle_message(self, update, context):
        """Handler principal de mensajes - COMANDOS INVISIBLES + IA"""
        # ============== SEGMENTO 2/4: NEVER SILENT WRAPPER ==============
        # REGLA: El bot NUNCA se queda callado. SIEMPRE responde.
        never_silent_wrapper = get_never_silent()
        health_check = get_health_check()
        health_check.record_update()  # Registrar actividad para healthcheck
        
        user_id = update.effective_user.id
        text = update.message.text.strip() if update.message.text else ""
        state = get_state(user_id)
        user = get_user_data(user_id)
        lang = user.get("language", "es")  # Default español para MigPAL
        
        # ============== V4.0: MIGPAL USA STANDARD MIDDLEWARE ==============
        # Feature flag: MIGPAL_USA_STANDARD_V4=1 (default enabled)
        v4_info = None
        if is_v4_enabled():
            try:
                v4_info = v4_pre_process(user_id, text, state, user)
                if v4_info:
                    logger.debug(f"V4 pre-process: phase={v4_info.get('current_phase')}, turn={v4_info.get('turn_count')}")
            except Exception as e:
                logger.warning(f"V4 middleware pre-process error (fallback to legacy): {e}")
        
        # ============== V3.2.1: CONVERSATION RECORDER ==============
        # Grabar TODOS los mensajes para auditoría
        conversation_recorder = get_conversation_recorder()
        
        # Detectar fricción y determinar si bloquear datos
        friction_tags, should_block_data = conversation_recorder.record_user_message(
            user_id=user_id,
            text=text,
            state=state,
            intent="",  # Se actualizará después de detectar intent
            extracted_fields={},  # Se actualizará después de extraer
            warnings=[],
            metadata={"lang": lang}
        )
        
        # REGLA CRÍTICA: Si loop/confusion 2 veces seguidas, forzar clarify_question
        if should_block_data:
            clarify_msg = conversation_recorder.get_clarify_question(user_id, lang)
            await update.message.reply_text(clarify_msg, parse_mode='Markdown')
            
            # Grabar respuesta del bot
            conversation_recorder.record_bot_message(
                user_id=user_id,
                text=clarify_msg,
                state=state,
                intent="clarify_forced",
                warnings=["Data blocked due to consecutive friction"]
            )
            
            logger.warning(f"🚫 DATA_BLOCKED | user={user_id} | friction={[t.value for t in friction_tags]}")
            return  # NO continuar procesando, NO guardar datos
        
        # ============== SEGMENTO 1/3: DISPONIBILIDAD GARANTIZADA ==============
        # REGLA: Todo input DEBE generar respuesta. NUNCA quedarse callado.
        
        # 1. Registrar input para tracking de respuesta
        response_tracker = get_response_tracker()
        response_tracker.record_input(user_id, "message", text[:50])
        
        # 2. Iniciar watchdog de 3 segundos
        watchdog = get_watchdog()
        
        async def send_watchdog_message(msg: str):
            try:
                await update.message.reply_text(msg)
            except Exception as e:
                logger.error(f"Watchdog send failed: {e}")
        
        # V4.2.1: Pasar estado actual para deshabilitar watchdog en estados con IA intensiva
        await watchdog.start_watchdog(user_id, send_watchdog_message, lang, state)
        
        # V3.0.3 - Enhanced logging
        transition_logger = get_transition_logger()
        transition_logger.log_message_received(user_id, state, "text", text)
        
        # V3.0.3 - Record activity for stall detection
        stall_detector = get_stall_detector()
        stall_detector.record_activity(user_id, state, text)
        
        # V3.0.3 - Check for stall and send reminder if needed
        stall_result = check_and_handle_stall(user_id, lang)
        if stall_result:
            stall_msg, stall_buttons = stall_result
            await update.message.reply_text(
                stall_msg,
                parse_mode='Markdown',
                reply_markup=self._kb(stall_buttons)
            )
            watchdog.mark_response_sent(user_id)
            response_tracker.record_response(user_id)
            return
        
        logger.info(f"MSG: {user_id} | {state} | {text[:50]}")
        
        # ============== V3.2.0: PRIORIZACIÓN DE INTENTS ==============
        # REGLA CRÍTICA: Las preguntas, confusión, preocupaciones y reclamos del usuario
        # tienen PRIORIDAD ABSOLUTA sobre cualquier flujo interno del bot.
        # Esto debe ejecutarse ANTES de cualquier otro procesamiento.
        
        priority_handler = get_priority_intent_handler()
        should_interrupt, intent_type, empathic_response = priority_handler.should_interrupt_flow(text)
        
        if should_interrupt:
            logger.info(f"🚨 PRIORITY INTENT | user={user_id} | type={intent_type} | text={text[:50]}")
            
            # V4.2 FIX: Para confusión/emociones, NO avanzar fase ni evaluar gating
            # Solo responder con contención + 1 pregunta de clarificación
            if intent_type == "confusion":
                # Guardar estado anterior para poder volver
                previous_state = state
                user["_previous_state_before_emotion"] = previous_state
                save_user_data(user_id, user)
                
                # Cambiar a estado de clarificación emocional
                set_state(user_id, STATE_EMOTION_CLARIFICATION)
                
                # Respuesta empática de contención + 1 pregunta de clarificación
                containment_response = (
                    f"{empathic_response}\n\n"
                    "💭 ¿Qué parte te genera más dudas? Cuéntame y te ayudo a entenderlo mejor."
                ) if lang == "es" else (
                    f"{empathic_response}\n\n"
                    "💭 What part is most confusing? Tell me and I'll help you understand it better."
                )
                
                await update.message.reply_text(containment_response)
                watchdog.mark_response_sent(user_id)
                response_tracker.record_response(user_id)
                
                logger.info(f"💭 EMOTION_CLARIFICATION | user={user_id} | prev_state={previous_state} | NO phase advance, NO gating")
                return  # IMPORTANTE: NO continuar, NO avanzar fase, NO evaluar gating
            
            # 1. Responder empáticamente primero (para otros intents)
            await update.message.reply_text(empathic_response)
            watchdog.mark_response_sent(user_id)
            
            # 2. Si es pregunta, intentar responder con IA
            if intent_type == "question":
                try:
                    ai_response = await self._process_with_ai_brain(text, user, state)
                    if ai_response:
                        await update.message.reply_text(ai_response, parse_mode='Markdown')
                except Exception as e:
                    logger.warning(f"AI response failed for priority intent: {e}")
                    # Fallback: ofrecer ayuda
                    fallback = (
                        "¿Hay algo específico que te gustaría que te explique mejor? 🤔"
                        if lang == "es" else
                        "Is there something specific you'd like me to explain better? 🤔"
                    )
                    await update.message.reply_text(fallback)
            
            # 3. Si es frustración o queja, ofrecer opciones de ayuda
            elif intent_type in ["frustration", "complaint"]:
                help_options = (
                    "¿Cómo puedo ayudarte mejor?\n\n"
                    "• Escribe tu pregunta y te respondo\n"
                    "• Usa /ayuda para ver opciones\n"
                    "• Usa /reiniciar si quieres empezar de nuevo"
                ) if lang == "es" else (
                    "How can I help you better?\n\n"
                    "• Type your question and I'll answer\n"
                    "• Use /help to see options\n"
                    "• Use /restart if you want to start over"
                )
                await update.message.reply_text(help_options)
            
            response_tracker.record_response(user_id)
            return  # IMPORTANTE: No continuar con el flujo normal
        
        # V4.2 FIX: Handler para STATE_EMOTION_CLARIFICATION
        # Cuando el usuario está en estado de clarificación emocional, responder con empatía
        # y volver al estado anterior cuando esté listo
        if state == STATE_EMOTION_CLARIFICATION:
            # Obtener estado anterior
            previous_state = user.get("_previous_state_before_emotion", STATE_START)
            
            # Detectar si el usuario indica que ya entendió o quiere continuar
            continue_patterns = [
                r"entiendo", r"entendí", r"ya entendí", r"ahora entiendo",
                r"ok", r"okay", r"vale", r"listo", r"continuar", r"seguir",
                r"understand", r"got it", r"i see", r"continue", r"next",
                r"sí", r"si", r"yes", r"claro", r"perfecto"
            ]
            
            text_lower = text.lower().strip()
            wants_to_continue = any(re.search(p, text_lower) for p in continue_patterns)
            
            # V4.2.1 FIX: Detectar si el usuario está dando información útil de perfil
            # En ese caso, salir de clarificación y procesar normalmente
            profile_info_patterns = [
                r"soy\s+(ingenier|doctor|abogad|profesor|contador|enferm|programador|diseñador)",
                r"trabajo\s+(como|en|de)",
                r"tengo\s+\d+\s+(años|meses)\s+(de\s+)?experiencia",
                r"mi\s+(profesión|trabajo|carrera)",
                r"quiero\s+(ir|migrar|vivir)\s+(a|en)",
                r"(estados\s+unidos|usa|canada|españa|alemania|australia)",
                r"presupuesto\s+(es|de|tengo)",
                r"\$?\d+[,.]?\d*\s*(dólares|dolares|euros|usd|eur)",
                r"i\s+(am|work|have)\s+",
                r"my\s+(profession|job|budget)",
            ]
            is_giving_profile_info = any(re.search(p, text_lower) for p in profile_info_patterns)
            
            if wants_to_continue or is_giving_profile_info:
                # Limpiar el estado temporal
                if "_previous_state_before_emotion" in user:
                    del user["_previous_state_before_emotion"]
                    save_user_data(user_id, user)
                
                # V4.2.1 FIX: Si el usuario da info de perfil, NO volver a start
                # En su lugar, dejar que CorrectionNLU lo procese correctamente
                if is_giving_profile_info:
                    # Detectar qué tipo de info está dando
                    is_occupation = any(re.search(p, text_lower) for p in [
                        r"soy\s+(ingenier|doctor|abogad|profesor|contador|enferm|programador|diseñador)",
                        r"trabajo\s+(como|en|de)",
                        r"mi\s+(profesión|trabajo|carrera)",
                    ])
                    is_destination = any(re.search(p, text_lower) for p in [
                        r"quiero\s+(ir|migrar|vivir)\s+(a|en)",
                        r"(estados\s+unidos|usa|canada|españa|alemania|australia)",
                    ])
                    is_budget = any(re.search(p, text_lower) for p in [
                        r"presupuesto\s+(es|de|tengo)",
                        r"\$?\d+[,.]?\d*\s*(dólares|dolares|euros|usd|eur)",
                    ])
                    
                    logger.info(f"✅ EMOTION_RESOLVED | user={user_id} | profile_info=True | occupation={is_occupation} | destination={is_destination} | budget={is_budget}")
                    
                    # NO cambiar estado aquí - dejar que CorrectionNLU lo maneje
                    # Solo actualizar la variable local para que continúe el flujo
                    state = STATE_NAME if is_occupation else previous_state
                    # NO hacer return - dejar que continúe el flujo normal
                    pass
                else:
                    # Solo quiere continuar - mostrar mensaje y prompt
                    transition_msg = (
                        "¡Perfecto! 😊 Continuemos donde estabamos."
                        if lang == "es" else
                        "Perfect! 😊 Let's continue where we were."
                    )
                    await update.message.reply_text(transition_msg)
                    watchdog.mark_response_sent(user_id)
                    
                    # Obtener el prompt del estado anterior
                    current_prompt = self._get_state_prompt(previous_state, user, lang)
                    if current_prompt:
                        await update.message.reply_text(current_prompt, parse_mode='Markdown')
                    
                    response_tracker.record_response(user_id)
                    return
            else:
                # Seguir en modo de clarificación - responder con empatía
                clarification_response = (
                    "Entiendo. 🤔 Déjame explicarte de otra forma...\n\n"
                    "Si tienes más dudas, pregúntame. Cuando estés listo para continuar, "
                    "solo dime 'listo' o 'continuar'."
                ) if lang == "es" else (
                    "I understand. 🤔 Let me explain it differently...\n\n"
                    "If you have more questions, just ask. When you're ready to continue, "
                    "just say 'ready' or 'continue'."
                )
                
                # Intentar responder con IA si es posible
                try:
                    ai_response = await self._process_with_ai_brain(text, user, previous_state)
                    if ai_response:
                        await update.message.reply_text(ai_response, parse_mode='Markdown')
                        await update.message.reply_text(
                            "👉 Cuando estés listo, dime 'continuar'." if lang == "es" else 
                            "👉 When you're ready, say 'continue'."
                        )
                    else:
                        await update.message.reply_text(clarification_response)
                except Exception as e:
                    logger.warning(f"AI response failed in emotion clarification: {e}")
                    await update.message.reply_text(clarification_response)
                
                watchdog.mark_response_sent(user_id)
                response_tracker.record_response(user_id)
                logger.info(f"💭 EMOTION_CLARIFICATION_CONTINUE | user={user_id} | still clarifying")
                return
        
        # === V3.0.5: NLU DE CORRECCIÓN ===
        # Detectar si el usuario quiere corregir un campo mientras está en otro prompt
        try:
            from app.services.ux_v305 import CorrectionNLU, CorrectionType
            
            correction = CorrectionNLU.detect_correction(text)
            if correction and correction.confidence >= 0.6:
                # Actualizar el campo correspondiente
                field_updated = False
                field_name = ""
                
                if correction.type == CorrectionType.EMAIL:
                    user["profile"]["personal"]["email"] = correction.value
                    field_updated = True
                    field_name = "correo" if lang == "es" else "email"
                elif correction.type == CorrectionType.PHONE:
                    user["profile"]["personal"]["phone"] = correction.value
                    field_updated = True
                    field_name = "teléfono" if lang == "es" else "phone"
                elif correction.type == CorrectionType.NAME:
                    user["profile"]["personal"]["name"] = correction.value
                    field_updated = True
                    field_name = "nombre" if lang == "es" else "name"
                # V4.2.1 FIX: Manejar OCCUPATION - guardar y pedir nombre
                elif correction.type == CorrectionType.OCCUPATION:
                    if "professional" not in user["profile"]:
                        user["profile"]["professional"] = {}
                    user["profile"]["professional"]["profession"] = correction.value
                    save_user_data(user_id, user)
                    logger.info(f"✅ OCCUPATION_DETECTED | user={user_id} | profession={correction.value}")
                    
                    # Transicionar a pedir nombre (profile_collect)
                    set_state(user_id, STATE_NAME)
                    
                    # Mensaje de confirmación + pedir nombre
                    confirm_msg = CorrectionNLU.get_confirmation_message(correction, lang)
                    await update.message.reply_text(confirm_msg)
                    watchdog.mark_response_sent(user_id)
                    return
                
                if field_updated:
                    save_user_data(user_id, user)
                    logger.info(f"✏️ CORRECTION | user={user_id} | field={correction.type.value} | value={correction.value}")
                    
                    # Confirmar la corrección y re-preguntar el campo pendiente
                    confirm_msg = CorrectionNLU.get_confirmation_message(correction, lang)
                    
                    # Obtener el prompt del estado actual
                    current_prompt = self._get_state_prompt(state, user, lang)
                    
                    await update.message.reply_text(
                        f"{confirm_msg}\n\n{current_prompt}",
                        parse_mode='Markdown'
                    )
                    return
        except Exception as e:
            logger.warning(f"Error en NLU de corrección: {e}")
        
        # === V5.0: ONBOARDING CONVERSACIONAL SIMPLE ===
        # Estado "conversing" = el bot está en modo conversacional
        # Extrae info naturalmente, pregunta UNA cosa a la vez
        
        if state == "conversing" or state in ["start", "onboarding_welcome", "onboarding_question", "onboarding_listening", "onboarding_explain", "onboarding_consent", "onboarding_name"]:
            # Usar el nuevo motor conversacional
            try:
                response, updated_user = process_conversational_message(text, user, lang)

                # Guardar datos actualizados
                user_data[user_id] = updated_user
                save_user_data(user_id, updated_user)

                # Enviar respuesta conversacional
                await update.message.reply_text(response, parse_mode='Markdown')

                # Marcar respuesta enviada
                watchdog.mark_response_sent(user_id)
                response_tracker.record_response(user_id)

                # Si hay una pregunta pendiente de IA, procesarla asíncronamente
                if updated_user.get("pending_ai_question"):
                    try:
                        # Mostrar indicador de "typing"
                        await update.message.chat.send_action("typing")

                        # Importar y procesar con IA
                        from app.services.ai_brain import process_with_ai

                        conversation_history = updated_user.get("conversation_history", [])
                        ai_result = await process_with_ai(
                            updated_user["pending_ai_question"],
                            updated_user,
                            conversation_history
                        )

                        if ai_result.get("success") and ai_result.get("response"):
                            # Enviar respuesta de IA
                            await update.message.reply_text(ai_result["response"], parse_mode='Markdown')

                            # Actualizar historial
                            if "conversation_history" not in updated_user:
                                updated_user["conversation_history"] = []
                            updated_user["conversation_history"].append({
                                "role": "user",
                                "content": updated_user["pending_ai_question"]
                            })
                            updated_user["conversation_history"].append({
                                "role": "assistant",
                                "content": ai_result["response"]
                            })

                            # Limpiar la pregunta pendiente
                            del updated_user["pending_ai_question"]
                            if "pending_reflections" in updated_user:
                                del updated_user["pending_reflections"]
                            if "has_reflections" in updated_user:
                                del updated_user["has_reflections"]

                            # Guardar cambios
                            user_data[user_id] = updated_user
                            save_user_data(user_id, updated_user)

                            logger.info(f"🤖 AI RESPONSE | user={user_id} | answered user question")

                    except Exception as e:
                        logger.error(f"Error procesando pregunta con IA: {e}")
                        # En caso de error, continuar con una pregunta del flujo
                        from app.services.conversational_onboarding import get_conversational_engine
                        engine = get_conversational_engine()
                        profile = engine._get_or_create_profile(updated_user)
                        next_q = engine.question_gen.get_next_question(profile, lang)
                        if next_q:
                            _, question = next_q
                            await update.message.reply_text(question)

                logger.info(f"💬 CONVERSATIONAL | user={user_id} | extracted info from natural conversation")
                return
            except Exception as e:
                logger.error(f"Conversational engine error: {e}")
                # Fallback: respuesta empática simple
                fallback = (
                    "Entiendo. Cuéntame más sobre tu situación. 💭"
                    if lang == "es" else
                    "I understand. Tell me more about your situation. 💭"
                )
                await update.message.reply_text(fallback)
                watchdog.mark_response_sent(user_id)
                response_tracker.record_response(user_id)
                return
        
        # ============== SEGMENTO 2/3: GOBIERNO DEL FLUJO (ANTI-BOT) ==============
        # La conversación manda, no los formularios ni los states.
        
        # 1. INTERPRETAR el input del usuario (NUNCA ignorar)
        interpreted = interpret_user_input(text, state)
        logger.info(f"INTERPRETED | type={interpreted.input_type.value} | conf={interpreted.confidence:.2f} | data={interpreted.extracted_data}")
        
        # ============== SEGMENTO 3/3: MEMORIA, PERFILADO Y DECISIÓN ==============
        # Extracción ≠ decisión. Todo dato se guarda y se reutiliza.
        
        # 1. GUARDAR TODO lo que dice el usuario (memoria persistente)
        data_memory = get_data_memory()
        data_memory.store_raw_input(user_id, text, context=state)
        
        # 2. EXTRAER datos del texto y guardarlos en el perfil
        extracted_data = store_user_input(user_id, text, user)
        if extracted_data:
            save_user_data(user_id, user)
            logger.info(f"🧠 MEMORY | user={user_id} | extracted={extracted_data}")
        
        # 3. DETECTAR si es una corrección (si corrige, NO avanzar de fase)
        is_correction, corrected_field = detect_correction(text)
        if is_correction:
            correction_tracker = get_correction_tracker()
            logger.info(f"✏️ CORRECTION DETECTED | user={user_id} | field={corrected_field}")
            
            # Registrar la corrección
            if corrected_field and corrected_field in extracted_data:
                old_value = user.get("profile", {}).get("personal", {}).get(corrected_field, "")
                correction_tracker.register_correction(user_id, corrected_field, old_value, extracted_data[corrected_field])
            
            # Confirmar la corrección y NO avanzar
            confirm_msg = "Entendido, actualizo esa información. ✏️" if lang == "es" else "Got it, I'll update that. ✏️"
            await update.message.reply_text(confirm_msg)
            watchdog.mark_response_sent(user_id)
            return
        
        # 4. Verificar si hay correcciones pendientes (bloquea avance de fase)
        correction_tracker = get_correction_tracker()
        can_advance, correction_msg = correction_tracker.can_advance_phase(user_id)
        if not can_advance:
            await update.message.reply_text(correction_msg)
            watchdog.mark_response_sent(user_id)
            return
        
        # 2. Registrar interacción para throttling de formularios
        form_throttler = get_form_throttler()
        conversation_director = get_conversation_director()
        
        # 3. Si el usuario hace pregunta, expresa preocupación o frustración, RESPONDER PRIMERO
        if interpreted.input_type in [InputType.QUESTION, InputType.CONCERN, InputType.FRUSTRATION]:
            # Responder empáticamente antes de continuar con el flujo
            contextual_response = InputInterpreter.get_contextual_response(interpreted, lang)
            await update.message.reply_text(contextual_response)
            watchdog.mark_response_sent(user_id)
            
            # Si es pregunta, intentar responder con IA
            if interpreted.input_type == InputType.QUESTION:
                try:
                    ai_response = await self._process_with_ai_brain(text, user, state)
                    if ai_response:
                        await update.message.reply_text(ai_response, parse_mode='Markdown')
                except:
                    pass
            return
        
        # 4. V3.1.0 - HARDENED: Solo guardar datos extraidos con confirmación
        # REGLA: NO guardar nombre fuera del estado ask_name sin señal fuerte
        if interpreted.extracted_data:
            from app.services.ux_improvements import NameValidator
            
            for field, value in interpreted.extracted_data.items():
                # V3.1.0 - NOMBRE: Solo guardar si estamos en estado correcto O hay señal fuerte
                if field == "name" and value:
                    is_name_state = state in [STATE_NAME, 'ask_name', 'NAME_REQUEST', 'confirm_name']
                    has_strong_signal = NameValidator.has_strong_name_signal(text)
                    
                    if is_name_state or has_strong_signal:
                        # Validar con NameValidator hardened
                        is_valid, result = NameValidator.is_valid_name(value, state)
                        if is_valid:
                            user["profile"]["personal"]["name"] = result
                            logger.info(f"🔒 NAME SAVED | user={user_id} | name={result} | state={state}")
                        else:
                            logger.info(f"🚫 NAME BLOCKED | user={user_id} | reason={result} | value={value}")
                    else:
                        # NO guardar nombre fuera de contexto - evitar datos fantasma
                        logger.info(f"🚫 NAME BLOCKED (wrong state) | user={user_id} | state={state} | value={value}")
                        continue
                elif field == "age" and value:
                    user["profile"]["personal"]["age"] = value
                elif field == "profession" and value:
                    user["profile"]["work"]["profession"] = value
                elif field == "country" and value:
                    user["profile"]["personal"]["nationality"] = value
            
            # Solo guardar si hay datos válidos
            if any(f != "name" for f in interpreted.extracted_data.keys()) or \
               ("name" in interpreted.extracted_data and user.get("profile", {}).get("personal", {}).get("name")):
                save_user_data(user_id, user)
                logger.info(f"💾 EXTRACTED DATA SAVED | user={user_id} | data={list(interpreted.extracted_data.keys())}")
            else:
                logger.info(f"🚫 NO DATA SAVED | user={user_id} | blocked fields")
        
        
        # 5. Verificar si se puede mostrar formulario (máx 1 cada 5 interacciones)
        can_show_form_now, form_reason = should_show_form(user_id, state)
        form_throttler.record_interaction(user_id, is_form=False)  # Registrar esta interacción
        
        # === ESTADOS DE FORMULARIO ===
        # P0 FIX: Solo incluir estados que están definidos y tienen handlers
        FORM_STATES = [
            STATE_NAME, "confirm_name", STATE_BIRTH_DATE, STATE_CURRENT_CITY, STATE_EMAIL, STATE_PHONE,
            STATE_EDUCATION_CAREER, STATE_PROFESSION, STATE_LINKEDIN,
            STATE_TIMELINE, STATE_BUDGET_INITIAL, STATE_SAVINGS,
            STATE_FAMILY_MEMBER_NAME, STATE_FAMILY_MEMBER_BIRTH
        ]
        
        if state in FORM_STATES:
            # SEGMENTO 2/3: Si no se puede mostrar formulario, usar enfoque conversacional
            if not can_show_form_now:
                logger.info(f"FORM THROTTLED | user={user_id} | reason={form_reason}")
                # Usar enfoque conversacional en lugar de formulario
                alternative = form_throttler.get_alternative_approach(user_id, state, lang)
                await update.message.reply_text(alternative)
                watchdog.mark_response_sent(user_id)
                return
            
            # Registrar que mostramos formulario
            form_throttler.record_interaction(user_id, is_form=True)
            
            # Procesar el estado de formulario directamente
            handled = await self._handle_form_state(update, user_id, user, state, text)
            if handled:
                watchdog.mark_response_sent(user_id)
                return
        
        # V2.1 - DETECTAR INTENCIÓN DEL MENSAJE (Comandos Invisibles)
        detected = detect_intent(text)
        logger.info(f"Intent: {detected.intent.value} | Confidence: {detected.confidence:.2f}")
        
        # Si la confianza es alta, ejecutar acción directamente
        if detected.confidence >= 0.5 and detected.intent != Intent.UNKNOWN:
            action_executed = await self._execute_intent_action(update, context, detected, user)
            if action_executed:
                return  # Acción ejecutada, no continuar con IA
        
        # Mostrar indicador de "pensando" con banner de avión
        # Obtener país de origen del usuario
        origin = user.get("profile", {}).get("personal", {}).get("current_country", "🌎")
        dest = user.get("preferences", {}).get("destination", "USA")
        
        # Banderas
        flags = {
            "Colombia": "🇨🇴", "Venezuela": "🇻🇪", "Mexico": "🇲🇽", "México": "🇲🇽",
            "Argentina": "🇦🇷", "Peru": "🇵🇪", "Perú": "🇵🇪", "Chile": "🇨🇱",
            "Ecuador": "🇪🇨", "Brasil": "🇧🇷", "USA": "🇺🇸", "Canada": "🇨🇦",
            "España": "🇪🇸", "Alemania": "🇩🇪"
        }
        origin_flag = flags.get(origin, "🌎")
        dest_flag = flags.get(dest, "🇺🇸")
        
        # V4.2.1 FIX: Evitar animaciones duplicadas
        import time
        current_time = time.time()
        last_animation = _animation_tracker.get(user_id, 0)
        should_animate = (current_time - last_animation) > ANIMATION_COOLDOWN
        
        thinking_msg = None
        if should_animate:
            _animation_tracker[user_id] = current_time
            thinking_msg = await update.message.reply_text(f"{origin_flag} ✈️ · · · · · · · · {dest_flag}")
        
        try:
            # Animar el avión viajando (solo si no hay cooldown)
            async def animate_thinking():
                frames = [
                    f"{origin_flag} ✈️ · · · · · · · · {dest_flag}",
                    f"{origin_flag} · ✈️ · · · · · · · {dest_flag}",
                    f"{origin_flag} · · ✈️ · · · · · · {dest_flag}",
                    f"{origin_flag} · · · ✈️ · · · · · {dest_flag}",
                    f"{origin_flag} · · · · ✈️ · · · · {dest_flag}",
                    f"{origin_flag} · · · · · ✈️ · · · {dest_flag}",
                    f"{origin_flag} · · · · · · ✈️ · · {dest_flag}",
                    f"{origin_flag} · · · · · · · ✈️ · {dest_flag}",
                    f"{origin_flag} · · · · · · · · ✈️ {dest_flag}",
                ]
                i = 0
                while True:
                    try:
                        await thinking_msg.edit_text(frames[i % len(frames)])
                        i += 1
                        await asyncio.sleep(0.5)
                    except:
                        break
            
            # Iniciar animación en background (solo si hay mensaje)
            animation_task = None
            if thinking_msg:
                animation_task = asyncio.create_task(animate_thinking())
            
            # Procesar con IA
            ai_response = await self._process_with_ai_brain(text, user, state)
            
            # Detener animación (si existe)
            if animation_task:
                animation_task.cancel()
                try:
                    await animation_task
                except asyncio.CancelledError:
                    pass
            
            # Eliminar mensaje de "pensando" (si existe)
            if thinking_msg:
                try:
                    await thinking_msg.delete()
                except:
                    pass
            
            # V4.2.1 FIX C: SIEMPRE enviar respuesta de texto, nunca dejar solo animación
            if ai_response:
                await update.message.reply_text(ai_response, parse_mode='Markdown')
                # SEGMENTO 2/3: Registrar intercambio conversacional
                conversation_director.record_exchange(user_id, text, ai_response[:200], was_form=False, state=state)
                watchdog.mark_response_sent(user_id)
            else:
                # V4.2.1 FIX: Fallback cuando IA no responde - NUNCA dejar sin respuesta
                fallback_msg = (
                    "Entiendo. Cuéntame más sobre ti para poder ayudarte mejor. 😊\n\n"
                    "¿Cuál es tu nombre?"
                ) if lang == "es" else (
                    "I understand. Tell me more about yourself so I can help you better. 😊\n\n"
                    "What's your name?"
                )
                await update.message.reply_text(fallback_msg)
                set_state(user_id, STATE_NAME)
                watchdog.mark_response_sent(user_id)
                logger.warning(f"⚠️ AI_FALLBACK | user={user_id} | No AI response, using fallback")
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            if thinking_msg:
                try:
                    await thinking_msg.delete()
                except:
                    pass
            
            # v3.0.8: NUNCA mostrar error - usar IA conversacional
            try:
                from app.services.conversational_ai import get_conversational_ai
                conv_ai = get_conversational_ai()
                response = await conv_ai.process_free_text(text, user, state, lang)
                
                # v3.0.9: Guardar datos extraídos por la IA
                if response.extracted_data:
                    data = response.extracted_data
                    if "name" in data:
                        user["profile"]["personal"]["name"] = data["name"]
                    if "profession" in data:
                        user["profile"]["professional"]["profession"] = data["profession"]
                    if "experience_years" in data:
                        user["profile"]["professional"]["experience_years"] = data["experience_years"]
                    if "salary" in data:
                        user["profile"]["financial"] = user.get("profile", {}).get("financial", {})
                        user["profile"]["financial"]["current_salary"] = data["salary"]
                    if "savings" in data:
                        user["profile"]["financial"] = user.get("profile", {}).get("financial", {})
                        user["profile"]["financial"]["savings"] = data["savings"]
                    if "motivation" in data:
                        user["profile"]["migration"] = user.get("profile", {}).get("migration", {})
                        user["profile"]["migration"]["motivation"] = data["motivation"]
                    
                    save_user_data(user_id, user)
                    logger.info(f"💾 Datos guardados: {list(data.keys())}")
                
                if response.suggested_actions:
                    await update.message.reply_text(
                        response.message,
                        parse_mode='Markdown',
                        reply_markup=self._kb(response.suggested_actions)
                    )
                else:
                    await update.message.reply_text(response.message, parse_mode='Markdown')
            except Exception as ai_error:
                logger.error(f"Conversational AI error: {ai_error}")
                # Fallback amigable - NUNCA mostrar "error"
                name = user.get("profile", {}).get("personal", {}).get("name", "amigo/a")
                fallback_msg = (
                    f"Gracias por compartir eso, {name}. 😊\n\n"
                    "Cuéntame más sobre lo que necesitas. "
                    "Estoy aquí para ayudarte."
                ) if lang == "es" else (
                    f"Thanks for sharing that, {name}. 😊\n\n"
                    "Tell me more about what you need. "
                    "I'm here to help you."
                )
                await update.message.reply_text(fallback_msg)
        
        # La IA ya respondió al usuario de forma natural
        return
        
        # ===== LEGACY: Solo se usa si la IA falla =====
        # ===== NAME =====
        if state == STATE_NAME:
            user["profile"]["personal"]["name"] = text
            set_state(user_id, STATE_BIRTH_DATE)
            await update.message.reply_text(
                f"¡Hola {text}! 😊\n\n"
                "¿Fecha de nacimiento?\n(DD/MM/AAAA)"
            )
        
        # ===== BIRTH DATE =====
        elif state == STATE_BIRTH_DATE:
            user["profile"]["personal"]["birth_date"] = text
            set_state(user_id, STATE_NATIONALITY)
            await update.message.reply_text(
                "¿Nacionalidad?",
                reply_markup=self._kb([
                    [("🇨🇴 Colombiano", "Colombiano"), ("🇲🇽 Mexicano", "Mexicano")],
                    [("🇻🇪 Venezolano", "Venezolano"), ("🇦🇷 Argentino", "Argentino")],
                    [("🌎 Otra", "Otra")]
                ])
            )
        
        # ===== CURRENT CITY =====
        elif state == STATE_CURRENT_CITY:
            user["profile"]["personal"]["current_city"] = text
            set_state(user_id, STATE_EMAIL)
            await update.message.reply_text("📧 ¿Tu correo electrónico?")
        
        # ===== EMAIL =====
        elif state == STATE_EMAIL:
            user["profile"]["personal"]["email"] = text
            set_state(user_id, STATE_PHONE)
            await update.message.reply_text("📱 ¿Tu teléfono? (con código de país)")
        
        # ===== PHONE =====
        elif state == STATE_PHONE:
            user["profile"]["personal"]["phone"] = text
            set_state(user_id, STATE_EDUCATION_LEVEL)
            await update.message.reply_text(
                "🎓 ¿Cuál es tu nivel educativo más alto?",
                reply_markup=self._kb([
                    [("📚 Bachillerato", "Bachillerato"), ("📖 Técnico/Tecnológico", "Técnico")],
                    [("🎓 Universitario", "Universitario"), ("📜 Especialización", "Especialización")],
                    [("🎖️ Maestría", "Maestría"), ("🏆 Doctorado", "Doctorado")]
                ])
            )
        
        # ===== EDUCATION CAREER =====
        elif state == STATE_EDUCATION_CAREER:
            user["profile"]["education"]["career"] = text
            set_state(user_id, STATE_WORK_STATUS)
            await update.message.reply_text(
                "¿Cuál es tu situación laboral actual?",
                reply_markup=self._kb([
                    ("👔 Empleado", "Empleado"),
                    ("🏢 Independiente/Freelance", "Independiente"),
                    ("🚀 Empresario/Dueño", "Empresario"),
                    ("📚 Estudiante", "Estudiante"),
                    ("🔍 Buscando empleo", "Desempleado")
                ])
            )
        
        # ===== PROFESSION =====
        elif state == STATE_PROFESSION:
            user["profile"]["work"]["profession"] = text
            set_state(user_id, STATE_WORK_EXPERIENCE)
            await update.message.reply_text(
                "¿Años de experiencia?",
                reply_markup=self._kb([
                    [("< 1", "<1"), ("1-3", "1-3"), ("3-5", "3-5")],
                    [("5-10", "5-10"), ("10-15", "10-15"), ("> 15", ">15")]
                ])
            )
        
        # ===== LINKEDIN =====
        elif state == STATE_LINKEDIN:
            if text.lower() in ["omitir", "no", "skip"]:
                user["profile"]["work"]["linkedin"] = "No proporcionado"
            else:
                user["profile"]["work"]["linkedin"] = text
            
            set_state(user_id, STATE_VISA_HISTORY)
            await update.message.reply_text(
                "🛂 ¿Has tenido visas de otros países?",
                reply_markup=self._kb([
                    ("✅ Sí", "Sí"),
                    ("❌ No", "No")
                ])
            )
        
        # ===== VISA DETAILS =====
        elif state == STATE_VISA_DETAILS:
            user["profile"]["history"]["visas"] = text
            set_state(user_id, STATE_VISA_REJECTIONS)
            await update.message.reply_text(
                "¿Has tenido rechazos de visa?",
                reply_markup=self._kb([
                    ("❌ No", "No"),
                    ("⚠️ Sí", "Sí")
                ])
            )
        
        # ===== FAMILY MEMBER NAME =====
        elif state == STATE_FAMILY_MEMBER_NAME:
            idx = user["current_family_index"]
            user["family_members"][idx]["name"] = text
            set_state(user_id, STATE_FAMILY_MEMBER_BIRTH)
            await update.message.reply_text(f"¿Fecha de nacimiento de {text}? (DD/MM/AAAA)")
        
        # ===== FAMILY MEMBER BIRTH =====
        elif state == STATE_FAMILY_MEMBER_BIRTH:
            idx = user["current_family_index"]
            user["family_members"][idx]["birth_date"] = text
            relation = user["family_members"][idx]["relation"]
            name = user["family_members"][idx]["name"]
            
            set_state(user_id, STATE_FAMILY_MEMBER_EDUCATION)
            if relation == "Hijo/a":
                await update.message.reply_text(
                    f"¿En qué nivel educativo está {name}?",
                    reply_markup=self._kb([
                        [("📒 Preescolar", "Preescolar"), ("📕 Primaria", "Primaria")],
                        [("📗 Secundaria", "Secundaria"), ("📘 Universidad", "Universidad")],
                        [("✅ Ya terminó estudios", "Terminado")]
                    ])
                )
            else:
                await update.message.reply_text(
                    f"¿Nivel educativo de {name}?",
                    reply_markup=self._kb([
                        [("📚 Bachillerato", "Bachillerato"), ("📖 Técnico", "Técnico")],
                        [("🎓 Universitario", "Universitario"), ("📜 Posgrado", "Posgrado")]
                    ])
                )
        
        # ===== FAMILY MEMBER STUDY STATUS =====
        elif state == STATE_FAMILY_MEMBER_STUDY_STATUS:
            idx = user["current_family_index"]
            user["family_members"][idx]["studying"] = text
            name = user["family_members"][idx]["name"]
            set_state(user_id, STATE_FAMILY_MEMBER_ENGLISH)
            await update.message.reply_text(
                f"¿Nivel de inglés de {name}?",
                reply_markup=self._kb([
                    [("🔴 Ninguno", "Ninguno"), ("🟠 Básico", "Básico")],
                    [("🟡 Intermedio", "Intermedio"), ("🟢 Avanzado", "Avanzado")]
                ])
            )
        
        # ===== DOCUMENT UPLOAD =====
        elif state == STATE_DOCUMENT_UPLOAD:
            await update.message.reply_text(
                "📤 Envía documentos como archivos o fotos.\n"
                "Cuando termines, escribe /listo"
            )
        
        # ===== CONSULTING =====
        elif state == STATE_CONSULTING:
            await update.message.chat.send_action("typing")
            response = await self._get_ai_response(text, user)
            await update.message.reply_text(response)
            watchdog.mark_response_sent(user_id)
        
        else:
            # SEGMENTO 1/3: Fallback empático en lugar de mensaje genérico
            fallback_msg = EmpathicFallback.get_phase_fallback(lang, state)
            await update.message.reply_text(fallback_msg)
            watchdog.mark_response_sent(user_id)
    
    # ============== DOCUMENT HANDLERS ==============
    
    async def _handle_document(self, update, context):
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        state = get_state(user_id)
        doc = update.message.document
        
        # Save document
        doc_info = {
            "file_id": doc.file_id,
            "file_name": doc.file_name,
            "mime_type": doc.mime_type,
            "uploaded_at": datetime.now().isoformat()
        }
        user["documents"].append(doc_info)
        
        # Process with OCR if possible
        ocr_text = await self._process_document_ocr(doc, context)
        if ocr_text:
            doc_info["ocr_text"] = ocr_text[:1000]  # Store first 1000 chars
        
        await update.message.reply_text(
            f"✅ *{doc.file_name}* recibido\n\n"
            f"📎 Total: {len(user['documents'])} documento(s)\n\n"
            "Envía más o escribe /listo",
            parse_mode='Markdown'
        )
        
        # If in LinkedIn state, move to next
        if state == STATE_LINKEDIN:
            user["profile"]["work"]["cv"] = doc.file_name
            set_state(user_id, STATE_VISA_HISTORY)
            await update.message.reply_text(
                "🛂 ¿Has tenido visas de otros países?",
                reply_markup=self._kb([
                    ("✅ Sí", "Sí"),
                    ("❌ No", "No")
                ])
            )
    
    async def _handle_photo(self, update, context):
        user_id = update.effective_user.id
        user = get_user_data(user_id)
        state = get_state(user_id)
        photo = update.message.photo[-1]
        
        doc_info = {
            "file_id": photo.file_id,
            "type": "photo",
            "uploaded_at": datetime.now().isoformat()
        }
        user["documents"].append(doc_info)
        
        # Process with OCR
        ocr_text = await self._process_photo_ocr(photo, context)
        if ocr_text:
            doc_info["ocr_text"] = ocr_text[:1000]
        
        await update.message.reply_text(
            f"✅ Foto recibida\n\n"
            f"📎 Total: {len(user['documents'])} documento(s)\n\n"
            "Envía más o escribe /listo"
        )
        
        # If in LinkedIn state, move to next
        if state == STATE_LINKEDIN:
            user["profile"]["work"]["cv"] = "Foto de CV"
            set_state(user_id, STATE_VISA_HISTORY)
            await update.message.reply_text(
                "🛂 ¿Has tenido visas de otros países?",
                reply_markup=self._kb([
                    ("✅ Sí", "Sí"),
                    ("❌ No", "No")
                ])
            )
    
    async def _process_document_ocr(self, doc, context) -> Optional[str]:
        """Process document with OCR using vision model"""
        try:
            # Download file
            file = await context.bot.get_file(doc.file_id)
            file_path = f"/tmp/{doc.file_name}"
            await file.download_to_drive(file_path)
            
            # For now, just log - full OCR would need additional setup
            logger.info(f"Document saved: {file_path}")
            
            # If it's a supported format, try to extract text
            if doc.mime_type == "application/pdf":
                # Would need PyPDF2 or similar
                pass
            
            return None
        except Exception as e:
            logger.error(f"OCR Error: {e}")
            return None
    
    async def _process_photo_ocr(self, photo, context) -> Optional[str]:
        """Process photo with OCR using vision model"""
        try:
            file = await context.bot.get_file(photo.file_id)
            file_path = f"/tmp/photo_{photo.file_id}.jpg"
            await file.download_to_drive(file_path)
            
            # Use qwen3-vl for OCR if available
            ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
            
            # Read image as base64
            import base64
            with open(file_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # Call vision model
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": "qwen3-vl:latest",
                        "prompt": "Extract all text from this document image. Return only the text content.",
                        "images": [image_data],
                        "stream": False
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
            
            return None
        except Exception as e:
            logger.error(f"Photo OCR Error: {e}")
            return None
    
    # ============== HELPERS ==============
    
    async def _show_options(self, query, user_id):
        user = get_user_data(user_id)
        dest = user["preferences"].get("destination", "Abierto")
        
        if dest == "Abierto":
            options = [
                [("🇺🇸 USA", "USA"), ("🇨🇦 Canadá", "Canadá")],
                [("🇪🇸 España", "España"), ("🇩🇪 Alemania", "Alemania")]
            ]
        else:
            options = [(f"✅ {dest}", dest)]
        
        # V3.2.0: Usar intro validado
        user_id = query.from_user.id
        user = get_user_data(user_id)
        lang = user.get("language", "es")
        profile_intro = get_profile_based_intro(user_id, user, lang)
        
        await query.edit_message_text(
            f"🎯 *FASE 4: Opciones*\n\n{profile_intro}, selecciona país:",
            parse_mode='Markdown',
            reply_markup=self._kb(options)
        )
    
    def _get_visa_explanations(self, country: str, user: dict) -> str:
        """Get detailed visa explanations for a country"""
        profile = user.get("profile", {})
        education = profile.get("education", {}).get("level", "")
        profession = profile.get("work", {}).get("profession", "")
        experience = profile.get("work", {}).get("experience", "")
        english = profile.get("languages", {}).get("english", "")
        reason = user.get("preferences", {}).get("reason", "")
        
        # V3.2.0: Validar si el perfil está confirmado antes de usar "basado en tu perfil"
        user_id = user.get("user_id", 0)
        lang = user.get("language", "es")
        profile_intro = get_profile_based_intro(user_id, user, lang)
        
        # Construir descripción del perfil solo si hay datos
        profile_desc = ""
        if profession and education:
            profile_desc = f" ({profession}, {education})"
        elif profession:
            profile_desc = f" ({profession})"
        elif education:
            profile_desc = f" ({education})"
        
        explanations = {
            "USA": f"""
🇺🇸 *OPCIONES DE VISA PARA ESTADOS UNIDOS*

{profile_intro}{profile_desc}:

💼 *H-1B - Trabajo Especializado*
• Para profesionales con título universitario
• Requiere oferta de trabajo de empresa americana
• Proceso por lotería (abril cada año)
• Duración: 3 años, renovable a 6
• {'✅ Podrías calificar' if education in ['Universitario', 'Maestría', 'Doctorado', 'Especialización'] else '⚠️ Requiere título universitario'}

📚 *F-1 - Estudiante*
• Para estudiar en universidad americana
• Permite trabajar 20hrs/semana
• Opción OPT después de graduarte
• {'✅ Buena opción' if reason == 'Estudios' else '💡 Considera si quieres estudiar'}

🏢 *L-1 - Transferencia Intracompany*
• Para empleados de multinacionales
• Requiere 1 año en la empresa
• No requiere lotería
• {'✅ Explora si trabajas en multinacional' if 'Empleado' in str(profile.get('work', {}).get('status', '')) else '⚠️ Requiere empleo en multinacional'}

🎲 *Lotería de Visas (DV)*
• 50,000 visas anuales por sorteo
• Gratis participar
• Requiere bachillerato mínimo
• ✅ Puedes aplicar (inscripción oct-nov)
""",
            "Canadá": f"""
🇨🇦 *OPCIONES DE MIGRACIÓN A CANADÁ*

{profile_intro}{' (inglés ' + english + ')' if english else ''}:

⚡ *Express Entry*
• Sistema de puntos (CRS)
• Valora: edad, educación, experiencia, idiomas
• Proceso: 6-12 meses
• Residencia permanente directa
• {'✅ Buen candidato' if english in ['Avanzado', 'Nativo', 'Intermedio'] else '⚠️ Mejorar inglés aumentaría puntos'}

🏢 *Provincial Nominee (PNP)*
• Cada provincia tiene sus programas
• Algunos no requieren oferta de trabajo
• Suma puntos a Express Entry
• ✅ Explora programas de diferentes provincias

📚 *Study Permit*
• Estudiar en Canadá
• Permiso trabajo 20hrs/semana
• PGWP después de graduarte
• Ruta a residencia permanente
• {'✅ Excelente opción' if reason == 'Estudios' else '💡 Considera para mejorar perfil'}
""",
            "España": f"""
🇪🇸 *OPCIONES DE VISA PARA ESPAÑA*

{profile_intro}{profile_desc}:

💼 *Visa de Trabajo*
• Requiere oferta de trabajo en España
• Empresa debe demostrar que no hay candidato local
• Proceso: 3-6 meses
• {'✅ Viable con oferta laboral' if reason == 'Trabajo' else '💡 Necesitas oferta de empresa española'}

📚 *Visa de Estudiante*
• Para estudios superiores
• Permite trabajar 20hrs/semana
• Renovable mientras estudies
• {'✅ Buena opción' if reason == 'Estudios' else '💡 Considera máster o especialización'}

💻 *Visa Nómada Digital*
• Para trabajadores remotos
• Ingresos mínimos: €2,500/mes
• No puedes trabajar para empresa española
• {'✅ Ideal si trabajas remoto' if 'Independiente' in str(profile.get('work', {}).get('status', '')) else '💡 Requiere trabajo remoto'}

💰 *Golden Visa*
• Inversión inmobiliaria €500,000+
• Residencia para toda la familia
• {'⚠️ Requiere alta inversión'}
""",
            "Alemania": f"""
🇩🇪 *OPCIONES DE VISA PARA ALEMANIA*

{profile_intro}{profile_desc}:

💳 *Blue Card EU*
• Para profesionales altamente calificados
• Requiere título universitario + oferta laboral
• Salario mínimo: €45,300/año
• Ruta rápida a residencia permanente
• {'✅ Excelente opción' if education in ['Universitario', 'Maestría', 'Doctorado'] else '⚠️ Requiere título universitario'}

💼 *Visa de Trabajo*
• Para empleos que no califican Blue Card
• Requiere oferta de trabajo
• Proceso: 2-4 meses

📚 *Visa de Estudiante*
• Muchos programas en inglés
• Universidades públicas casi gratis
• Permiso trabajo 120 días/año
• {'✅ Muy buena opción' if reason == 'Estudios' else '💡 Considera para especializarte'}
"""
        }
        
        return explanations.get(country, f"🌍 *Opciones para {country}*\n\nConsultando información...")
    
    def _get_visas(self, country: str) -> list:
        visas = {
            "USA": [
                ("💼 H-1B Trabajo", "H-1B"),
                ("📚 F-1 Estudiante", "F-1"),
                ("🏢 L-1 Transferencia", "L-1"),
                ("🎲 Lotería DV", "DV Lottery")
            ],
            "Canadá": [
                ("⚡ Express Entry", "Express Entry"),
                ("🏢 Provincial PNP", "PNP"),
                ("📚 Estudiante", "Study Permit")
            ],
            "España": [
                ("💼 Trabajo", "Trabajo"),
                ("📚 Estudiante", "Estudiante"),
                ("💻 Nómada Digital", "Nómada Digital")
            ],
            "Alemania": [
                ("💳 Blue Card", "Blue Card"),
                ("💼 Trabajo", "Trabajo"),
                ("📚 Estudiante", "Estudiante")
            ]
        }
        return visas.get(country, [("📋 Consultar", "consultar")])
    
    def _get_states(self, country: str) -> list:
        states = {
            "USA": [
                [("🌴 Florida", "Florida"), ("🤠 Texas", "Texas")],
                [("☀️ California", "California"), ("🗽 New York", "New York")]
            ],
            "Canadá": [
                [("🍁 Ontario", "Ontario"), ("⚜️ Quebec", "Quebec")],
                [("🏔️ BC", "BC"), ("🌾 Alberta", "Alberta")]
            ],
            "España": [
                [("🏛️ Madrid", "Madrid"), ("🌊 Cataluña", "Cataluña")],
                [("☀️ Valencia", "Valencia"), ("🌴 Andalucía", "Andalucía")]
            ],
            "Alemania": [
                [("🏛️ Baviera", "Baviera"), ("🌆 Berlín", "Berlín")],
                [("🏭 NRW", "NRW"), ("🌲 Baden-W", "Baden-W")]
            ]
        }
        return states.get(country, [[("📍 Principal", "Principal")]])
    
    def _get_cities(self, state: str) -> list:
        cities = {
            "Florida": [("🌴 Miami", "Miami"), ("🎢 Orlando", "Orlando"), ("🏖️ Tampa", "Tampa")],
            "Texas": [("🤠 Houston", "Houston"), ("🎸 Austin", "Austin"), ("🏙️ Dallas", "Dallas")],
            "California": [("🌉 San Francisco", "SF"), ("🎬 Los Angeles", "LA"), ("🌴 San Diego", "SD")],
            "New York": [("🗽 NYC", "NYC"), ("🏛️ Albany", "Albany")],
            "Ontario": [("🏙️ Toronto", "Toronto"), ("🏛️ Ottawa", "Ottawa")],
            "Madrid": [("🏛️ Madrid", "Madrid")],
            "Cataluña": [("🌊 Barcelona", "Barcelona")]
        }
        return cities.get(state, [("🏙️ Principal", "Principal")])
    
    async def _show_documents(self, query, user_id):
        user = get_user_data(user_id)
        route = user.get("selected_route", {})
        visa = route.get("visa_type", "")
        
        docs = [
            "📕 Pasaporte vigente",
            "📸 Fotos pasaporte",
            "📄 Certificado nacimiento",
            "📜 Antecedentes penales",
            "🎓 Títulos académicos",
            "💼 Certificados laborales",
            "💰 Extractos bancarios"
        ]
        
        await query.edit_message_text(
            f"📋 *FASE 6: Documentos*\n\n"
            f"Para *{visa}* necesitas:\n\n" +
            "\n".join(docs) + "\n\n"
            "¿Quieres subir documentos ahora?",
            parse_mode='Markdown',
            reply_markup=self._kb([
                ("📤 Subir ahora", "start_upload"),
                ("⏰ Después", "skip_docs")
            ])
        )
    
    async def _get_info(self, info_type: str, user: dict) -> str:
        route = user.get("selected_route", {})
        country = route.get("country", "N/A")
        visa = route.get("visa_type", "N/A")
        
        if info_type == "req_visa":
            return (
                f"📄 *Requisitos {visa} - {country}*\n\n"
                "• Pasaporte vigente (6+ meses)\n"
                "• Formulario de solicitud\n"
                "• Fotos recientes\n"
                "• Prueba de fondos\n"
                "• Documentos de respaldo"
            )
        elif info_type == "req_costs":
            return (
                f"💰 *Costos {country}*\n\n"
                "• Visa: $160-$500\n"
                "• Trámites: $200-$500\n"
                "• Vuelos: $500-$1,500\n"
                "• Primeros meses: $3,000-$8,000\n\n"
                "*Total: $4,000-$10,000 USD*"
            )
        elif info_type == "req_time":
            return (
                f"⏱️ *Tiempos {visa}*\n\n"
                "• Preparación: 1-2 meses\n"
                "• Solicitud: 2-6 meses\n"
                "• Aprobación: 1-3 meses\n\n"
                "*Total: 4-12 meses*"
            )
        return "Info no disponible"
    
    async def _process_with_ai_brain(self, message: str, user: dict, state: str) -> str:
        """
        Procesa TODOS los mensajes con IA.
        La IA SIEMPRE continúa el proceso - nunca lo deja tirado.
        Responde la pregunta Y luego continúa con el proceso.
        AHORA incluye el historial de conversación para contexto.
        """
        try:
            from app.services.ai_brain import process_with_ai, extract_data_from_message
            
            user_id = user.get("user_id", 0)
            
            # CARGAR HISTORIAL DE CONVERSACIÓN para contexto
            conversation_history = []
            if user_id:
                conversation_history = load_conversations(user_id, limit=10)
                logger.info(f"Loaded {len(conversation_history)} previous messages for context")
            
            # Procesar con IA - AHORA CON HISTORIAL
            result = await process_with_ai(message, user, conversation_history)
            
            if result.get("success"):
                response = result.get("response", "")
                
                # ============== V4.0: POST-PROCESO DE RESPUESTA ==============
                # Aplicar reglas del estándar v4.0 (micro-checks, tono suave, etc.)
                if is_v4_enabled() and response:
                    try:
                        formatted_response = v4_post_process(user_id, response, is_form=False)
                        if formatted_response:
                            response = formatted_response
                            logger.debug(f"V4 post-process applied to response")
                    except Exception as e:
                        logger.warning(f"V4 post-process error (using original): {e}")
                
                # Extraer datos del perfil del mensaje
                extracted = result.get("extracted_data", {})
                if not extracted:
                    extracted = extract_data_from_message(message, user)
                
                if extracted:
                    self._update_profile_from_extracted(user, extracted)
                    # Guardar cambios
                    if user_id:
                        encrypted_data = encrypt_user_data(user)
                        save_user_data(user_id, encrypted_data)
                    logger.info(f"Extracted and saved: {extracted}")
                
                # Guardar conversación DESPUÉS de procesar
                save_conversation(
                    user_id,
                    message,
                    response,
                    role="user"
                )
                
                return response
            else:
                # Fallback a respuesta simple
                return await self._get_ai_response(message, user)
                
        except Exception as e:
            logger.error(f"AI Brain Error: {e}")
            # Fallback con continuación del proceso
            return await self._fallback_with_continuation(message, user)
    
    def _update_profile_from_extracted(self, user: dict, extracted: dict):
        """Actualiza el perfil del usuario con datos extraídos por la IA"""
        profile = user.get("profile", {})
        
        field_mapping = {
            "name": ("personal", "name"),
            "nationality": ("personal", "nationality"),
            "current_country": ("personal", "current_country"),
            "current_city": ("personal", "current_city"),
            "email": ("personal", "email"),
            "phone": ("personal", "phone"),
            "birth_date": ("personal", "birth_date"),
            "education_level": ("education", "level"),
            "education_field": ("education", "field"),
            "profession": ("work", "profession"),
            "work_experience": ("work", "experience"),
            "english_level": ("languages", "english"),
            "destination_country": None,  # Goes to selected_route
            "migration_reason": None,  # Goes to preferences
        }
        
        for field, value in extracted.items():
            if field in field_mapping and field_mapping[field]:
                section, key = field_mapping[field]
                if section not in profile:
                    profile[section] = {}
                profile[section][key] = value
                logger.info(f"Updated profile: {section}.{key} = {value}")
            elif field == "destination_country":
                user["selected_route"] = user.get("selected_route", {})
                user["selected_route"]["country"] = value
            elif field == "migration_reason":
                user["preferences"] = user.get("preferences", {})
                user["preferences"]["reason"] = value
    
    async def _fallback_with_continuation(self, message: str, user: dict) -> str:
        """
        Respuesta de fallback que SIEMPRE continúa el proceso.
        Nunca deja al usuario sin siguiente paso.
        """
        from app.services.ai_brain import get_next_question
        
        profile = user.get("profile", {})
        personal = profile.get("personal", {})
        name = personal.get("name", "")
        
        # Construir respuesta básica
        response = ""
        if name:
            response = f"Entiendo, {name}. "
        else:
            response = "Entiendo. "
        
        # Respuesta basada en palabras clave
        message_lower = message.lower()
        
        if "visa" in message_lower or "probabilidad" in message_lower:
            education = profile.get("education", {}).get("level", "")
            response += "\n\n📊 *Análisis de opciones de visa:*\n\n"
            
            if education in ["Universitario", "Maestría", "Doctorado"]:
                response += "✅ Tu nivel educativo te da buenas opciones:\n"
                response += "• H-1B (USA) - Para profesionales\n"
                response += "• Express Entry (Canadá) - Alta probabilidad\n"
                response += "• Blue Card (Alemania) - Excelente opción\n"
            else:
                response += "📝 Tus opciones principales:\n"
                response += "• Visa de trabajo con sponsor\n"
                response += "• Visa de estudiante\n"
                response += "• Programas de trabajador calificado\n"
        
        elif "costo" in message_lower or "dinero" in message_lower:
            response += "\n\n💰 *Costos aproximados:*\n"
            response += "• Visa y trámites: $500-$2,000\n"
            response += "• Primeros meses: $5,000-$15,000\n"
        
        else:
            response += "Estoy aquí para ayudarte con tu proceso de migración."
        
        # SIEMPRE agregar siguiente pregunta
        next_q = get_next_question(user)
        if next_q:
            response += f"\n\n📝 *Para continuar:* {next_q}"
        else:
            response += "\n\n✅ Tu perfil está completo. ¿Quieres que te dé recomendaciones específicas de visas?"
        
        return response
    
    async def _get_ai_response(self, question: str, user: dict) -> str:
        try:
            from app.utils.ai_assistant import chat_with_ai
            
            profile = user.get("profile", {})
            route = user.get("selected_route", {})
            
            context = f"""
Usuario: {profile.get('personal', {}).get('name', 'Usuario')}
Destino: {route.get('country', 'N/A')} - {route.get('visa_type', 'N/A')}
Ciudad: {route.get('city', 'N/A')}
"""
            
            result = await chat_with_ai(
                message=f"{context}\n\nPregunta: {question}",
                context={"profile": profile, "route": route}
            )
            
            return result.get("response", "No pude procesar tu pregunta.")
        except Exception as e:
            logger.error(f"AI Error: {e}")
            return "Error procesando. Intenta de nuevo."


# ============== BOT INSTANCE ==============

_bot_instance: Optional[MigPALBot] = None

def get_bot() -> MigPALBot:
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = MigPALBot()
    return _bot_instance

async def start_bot():
    bot = get_bot()
    await bot.start()
    return bot

async def stop_bot():
    global _bot_instance
    if _bot_instance:
        await _bot_instance.stop()
        _bot_instance = None

def run_bot():
    async def main():
        bot = await start_bot()
        try:
            while bot._running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            await stop_bot()
    asyncio.run(main())

if __name__ == "__main__":
    run_bot()
