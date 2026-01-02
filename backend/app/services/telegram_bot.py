"""
MigPAL Telegram Bot Service - V5.1 GLOBAL
Bot GLOBAL para migrantes de TODO EL MUNDO

Características:
- Soporte para 25+ idiomas
- Cobertura global de países destino
- Perfilamiento en 7 fases
- OCR para documentos
- Score de probabilidad de éxito
- Calculadora de costos
- Sistema de emergencias /sos
- Comunidad de migrantes
- Persistencia de datos
- Checklist inteligente de documentos
- Tracking de aplicación
- Mensajes motivacionales
- Sistema de mentores
- Directorio de abogados
- Bolsa de trabajo
- Guía de establecimiento
- Generación de reportes
"""

import os
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
    os.environ["AI_MODEL"] = "qwen2.5:7b"
    os.environ["OLLAMA_URL"] = "http://127.0.0.1:11434"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8243325921:AAFTkOmUG9emaDVa6dBPdxpey1rUxkSdLOA")

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

# In-memory cache (loaded from disk)
user_data: Dict[int, Dict[str, Any]] = {}

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


def get_user_data(user_id: int) -> Dict[str, Any]:
    """Get or create user data - loads from disk if exists"""
    if user_id not in user_data:
        # Try to load from disk first
        saved_data = load_user_data(user_id)
        if saved_data:
            user_data[user_id] = saved_data
            logger.info(f"Loaded existing case for user {user_id}")
        else:
            # Create new case
            user_data[user_id] = {
                "state": STATE_START,
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
                "created_at": datetime.now().isoformat()
            }
    return user_data[user_id]


def set_state(user_id: int, state: str):
    """Set state and auto-save to disk for persistence"""
    data = get_user_data(user_id)
    data["state"] = state
    # Auto-save to disk for persistence
    save_user_data(user_id, data)
    logger.info(f"State changed for {user_id}: {state} (saved to disk)")


def get_state(user_id: int) -> str:
    return get_user_data(user_id).get("state", STATE_START)


class MigPALBot:
    """MigPAL Telegram Bot V3.1"""
    
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
        
        self.application = Application.builder().token(self.token).build()
        
        # Handlers
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("help", self._cmd_help))
        self.application.add_handler(CommandHandler("nuevo", self._cmd_new))
        self.application.add_handler(CommandHandler("perfil", self._cmd_profile))
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
        self.application.add_handler(CommandHandler("idioma", self._cmd_language))
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self._handle_document))
        self.application.add_handler(MessageHandler(filters.PHOTO, self._handle_photo))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        logger.info("🤖 MigPAL Bot V5.1 GLOBAL starting...")
        self._running = True
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        logger.info("✅ MigPAL Bot V5.1 GLOBAL is running!")
        
    async def stop(self):
        if self.application and self._running:
            self._running = False
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
    
    # ============== COMMANDS ==============
    
    async def _cmd_start(self, update, context):
        user_id = update.effective_user.id
        user_data[user_id] = get_user_data(user_id)
        user_data[user_id]["state"] = STATE_START
        user_data[user_id]["profile"]["personal"]["telegram_name"] = update.effective_user.first_name
        
        # Get user's language or default to showing language selection
        lang = user_data[user_id].get("language", "en")
        
        await update.message.reply_text(
            "🌍 *Welcome to MigPAL!* / *¡Bienvenido a MigPAL!*\n\n"
            "Your GLOBAL migration assistant.\n"
            "Tu asistente de migración GLOBAL.\n\n"
            "🌐 We help migrants from ALL OVER THE WORLD\n"
            "🌐 Ayudamos a migrantes de TODO EL MUNDO\n\n"
            "I will guide you step by step to:\n"
            "Te guiaré paso a paso para:\n\n"
            "✅ Evaluate your options / Evaluar tus opciones\n"
            "✅ Plan your process / Planificar tu proceso\n"
            "✅ Manage documents / Gestionar documentos\n\n"
            "_First, select your language:_\n"
            "_Primero, selecciona tu idioma:_",
            parse_mode='Markdown',
            reply_markup=self._kb([
                [("🇬🇧 English", "lang_en"), ("🇪🇸 Español", "lang_es")],
                [("🇧🇷 Português", "lang_pt"), ("🇫🇷 Français", "lang_fr")],
                [("🇩🇪 Deutsch", "lang_de"), ("🇨🇳 中文", "lang_zh")],
                [("🇯🇵 日本語", "lang_ja"), ("🇰🇷 한국어", "lang_ko")],
                [("🇷🇺 Русский", "lang_ru"), ("🇸🇦 العربية", "lang_ar")],
                [("🌐 More languages / Más idiomas", "lang_more")]
            ])
        )
    
    async def _cmd_help(self, update, context):
        user_id = update.effective_user.id
        lang = get_user_data(user_id).get("language", "en")
        
        await update.message.reply_text(
            "🆘 *MigPAL Help V5.1 GLOBAL*\n\n"
            "*📝 Process / Proceso:*\n"
            "/start - Start / Iniciar\n"
            "/nuevo - Restart / Reiniciar\n"
            "/perfil - Profile / Perfil\n"
            "/estado - Progress / Progreso\n\n"
            "*📊 Analysis / Análisis:*\n"
            "/score - Success probability\n"
            "/costos - Cost calculator\n"
            "/checklist - Required documents\n"
            "/tracking - Application tracking\n\n"
            "*👥 Support / Apoyo:*\n"
            "/mentores - Connect with mentors\n"
            "/abogados - Lawyer directory\n"
            "/comunidad - Support groups\n"
            "/motivacion - Motivational message\n\n"
            "*💼 Resources / Recursos:*\n"
            "/empleos - Job board\n"
            "/guia - Settlement guide\n"
            "/reporte - Generate report\n\n"
            "*🆘 Emergency / Emergencia:*\n"
            "/sos - Urgent help\n\n"
            "*⚙️ Settings / Configuración:*\n"
            "/idioma - Change language (25+ languages)\n"
            "/listo - Finish document upload\n\n"
            "_🌍 MigPAL helps migrants from ALL OVER THE WORLD_",
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
    
    # ============== CALLBACK HANDLER ==============
    
    async def _handle_callback(self, update, context):
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        state = get_state(user_id)
        user = get_user_data(user_id)
        
        logger.info(f"CB: {user_id} | {state} | {data}")
        
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
            await query.message.reply_text(
                "👆 Basado en tu perfil, ¿cuál te interesa explorar?",
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
                save_user_data(user_id, user)
                
                # Get language name
                lang_info = SUPPORTED_LANGUAGES.get(lang, {})
                lang_name = lang_info.get("native", lang)
                
                # Continue to profile after language selection
                set_state(user_id, STATE_NAME)
                
                # Get translated text
                welcome_text = get_text("welcome", lang)
                ask_name = get_text("ask_name", lang)
                
                await query.edit_message_text(
                    f"✅ {lang_info.get('flag', '')} {lang_name}\n\n"
                    f"{welcome_text}\n\n"
                    f"📝 *PHASE 1: Your Profile*\n\n"
                    f"{ask_name}",
                    parse_mode='Markdown'
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
    
    # ============== MESSAGE HANDLER ==============
    
    async def _handle_message(self, update, context):
        user_id = update.effective_user.id
        text = update.message.text.strip()
        state = get_state(user_id)
        user = get_user_data(user_id)
        
        logger.info(f"MSG: {user_id} | {state} | {text[:30]}")
        
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
        
        else:
            await update.message.reply_text(
                "Usa los botones o /start para comenzar."
            )
    
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
        
        await query.edit_message_text(
            "🎯 *FASE 4: Opciones*\n\n"
            "Basado en tu perfil, selecciona país:",
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
        
        explanations = {
            "USA": f"""
🇺🇸 *OPCIONES DE VISA PARA ESTADOS UNIDOS*

Basado en tu perfil ({profession}, {education}):

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

Basado en tu perfil ({profession}, inglés {english}):

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

Basado en tu perfil ({profession}):

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

Basado en tu perfil ({profession}, {education}):

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
