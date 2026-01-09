"""
MigPAL Integration Module - Integración de Todos los Módulos
============================================================
Este módulo integra todos los componentes del sistema MigPAL revolucionario:
- Progress Tracker (Barra de progreso)
- Detailed Profiling (Perfilamiento exhaustivo)
- Family Profiling (Invitación familiar)
- Lawyer Referral (Referidos a bufetes)
- Document Checklist (Checklist de documentos)
- Visa Analyzer (Analizador de visas)
- Interview Simulator (Simulador de entrevista)
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import logging

# Importar todos los módulos
from app.services.progress_tracker import (
    ProgressTracker, ProcessStage, STAGES_INFO, PHASES_INFO,
    create_progress_tracker, format_progress_for_telegram,
    format_compact_progress, format_next_steps, format_roadmap
)

from app.services.detailed_profiling import (
    DetailedProfiler, ProfileSection, FieldType, ProfileField,
    PROFILE_FIELDS, get_all_sections, get_section_name,
    get_field_count, get_required_field_count
)

from app.services.family_profiling import (
    FamilyProfiler, FamilyRole, FamilyMember, FamilyInvitation,
    InvitationStatus, FAMILY_MEMBER_FIELDS,
    create_family_profiler, format_family_summary,
    get_role_name, get_role_emoji, FamilyInvitationHandler
)

from app.services.lawyer_referral import (
    LawyerReferralSystem, LawyerSpecialty, VisaCategory as LawyerVisaCategory,
    LawFirm, LawyerReferral, PARTNER_LAW_FIRMS,
    ALWAYS_NEED_LAWYER, RECOMMEND_LAWYER,
    create_lawyer_referral_system, get_visa_category_name
)

from app.services.document_checklist import (
    DocumentChecklist, DocumentCategory, DocumentStatus, DocumentPriority,
    DocumentRequirement, DOCUMENT_REQUIREMENTS,
    create_document_checklist, get_documents_for_visa
)

from app.services.visa_analyzer import (
    VisaAnalyzer, VisaType, VisaInfo, VisaRecommendation,
    VISA_DATABASE, create_visa_analyzer, get_visa_info, get_all_visa_types
)

from app.services.interview_simulator import (
    InterviewSimulator, InterviewType, InterviewQuestion,
    SimulationSession, INTERVIEW_QUESTIONS,
    create_interview_simulator, get_interview_tips, get_all_interview_types
)

logger = logging.getLogger(__name__)


class MigPALClient:
    """
    Cliente integrado de MigPAL que maneja todos los módulos para un usuario.
    """
    
    def __init__(self, user_id: int, case_storage=None, bot_username: str = "MigPAL_Bot"):
        self.user_id = user_id
        self.case_storage = case_storage
        self.bot_username = bot_username
        
        # Inicializar todos los módulos
        self.progress = create_progress_tracker(user_id, case_storage)
        self.profiler = DetailedProfiler(user_id, case_storage)
        self.family = create_family_profiler(user_id, case_storage, bot_username)
        self.lawyer_system = create_lawyer_referral_system(case_storage)
        self.document_checklist: Optional[DocumentChecklist] = None
        self.visa_analyzer: Optional[VisaAnalyzer] = None
        self.interview_sim: Optional[InterviewSimulator] = None
        
        # Estado actual
        self.current_visa_type: Optional[str] = None
        self.recommended_visa: Optional[VisaRecommendation] = None
    
    # =========================================================================
    # PROGRESO
    # =========================================================================
    
    def get_progress_status(self) -> str:
        """Obtener estado de progreso completo"""
        return format_progress_for_telegram(self.progress)
    
    def get_compact_status(self) -> str:
        """Obtener estado compacto para mostrar en cada mensaje"""
        return format_compact_progress(self.progress)
    
    def get_roadmap(self) -> str:
        """Obtener roadmap visual"""
        return format_roadmap(self.progress)
    
    def get_next_steps(self) -> str:
        """Obtener próximos pasos"""
        return format_next_steps(self.progress)
    
    def get_what_to_send(self) -> Dict[str, Any]:
        """Obtener qué debe enviar el cliente para continuar"""
        return self.progress.get_what_to_send_next()
    
    # =========================================================================
    # PERFILAMIENTO
    # =========================================================================
    
    def get_profile_completion(self) -> Tuple[int, int, float]:
        """Obtener completitud del perfil"""
        return self.profiler.get_overall_completion()
    
    def get_profile_summary(self) -> str:
        """Obtener resumen del perfil"""
        return self.profiler.generate_full_summary()
    
    def get_next_profile_field(self) -> Optional[ProfileField]:
        """Obtener siguiente campo a completar"""
        return self.profiler.get_next_field_to_complete()
    
    def get_profile_question(self, field: ProfileField) -> str:
        """Generar pregunta para un campo"""
        return self.profiler.generate_question_for_field(field)
    
    def set_profile_field(self, field_id: str, value: Any) -> Tuple[bool, str]:
        """Establecer valor de un campo del perfil"""
        success, message = self.profiler.set_field(field_id, value)
        
        if success:
            # Actualizar progreso
            task_id = f"profile_{field_id}"
            self.progress.complete_task(task_id, {"value": value})
        
        return success, message
    
    def get_section_summary(self, section: ProfileSection) -> str:
        """Obtener resumen de una sección del perfil"""
        return self.profiler.generate_section_summary(section)
    
    def get_pending_profile_fields(self, section: Optional[ProfileSection] = None) -> List[ProfileField]:
        """Obtener campos pendientes del perfil"""
        return self.profiler.get_pending_fields(section)
    
    # =========================================================================
    # FAMILIA
    # =========================================================================
    
    def get_family_summary(self) -> str:
        """Obtener resumen de la familia"""
        return format_family_summary(self.family)
    
    def add_family_member(self, role: FamilyRole, name: str, relationship: str) -> FamilyMember:
        """Agregar miembro de familia"""
        return self.family.add_family_member(role, name, relationship)
    
    def generate_family_invitation(self, member_id: str) -> str:
        """Generar link de invitación para un familiar"""
        return self.family.generate_invitation_link(member_id)
    
    def get_invitation_message(self, member_id: str) -> str:
        """Obtener mensaje de invitación para compartir"""
        return self.family.generate_invitation_message(member_id)
    
    def validate_family_invitation(self, token: str) -> Optional[FamilyInvitation]:
        """Validar una invitación familiar"""
        return self.family.validate_invitation(token)
    
    def accept_family_invitation(self, token: str, telegram_id: int) -> Optional[FamilyMember]:
        """Aceptar una invitación familiar"""
        return self.family.accept_invitation(token, telegram_id)
    
    def get_family_member_fields(self, member_id: str) -> List[Dict]:
        """Obtener campos para un miembro de familia"""
        return self.family.get_member_fields(member_id)
    
    def update_family_member_field(self, member_id: str, field_id: str, value: Any) -> bool:
        """Actualizar campo de un miembro de familia"""
        return self.family.update_member_field(member_id, field_id, value)
    
    def get_family_member_completion(self, member_id: str) -> Dict:
        """Obtener completitud de un miembro de familia"""
        return self.family.get_member_completion(member_id)
    
    # =========================================================================
    # ABOGADOS
    # =========================================================================
    
    def needs_lawyer(self, visa_category: LawyerVisaCategory) -> Dict[str, Any]:
        """Determinar si necesita abogado"""
        return self.lawyer_system.needs_lawyer(visa_category)
    
    def get_recommended_lawyers(self, visa_category: LawyerVisaCategory, location: Optional[str] = None) -> List[LawFirm]:
        """Obtener bufetes recomendados"""
        return self.lawyer_system.get_recommended_firms(visa_category, location)
    
    def create_lawyer_referral(self, law_firm_id: str, visa_category: LawyerVisaCategory) -> LawyerReferral:
        """Crear referido a abogado"""
        return self.lawyer_system.create_referral(self.user_id, law_firm_id, visa_category)
    
    def get_lawyer_recommendation_message(self, visa_category: LawyerVisaCategory, location: Optional[str] = None) -> str:
        """Obtener mensaje de recomendación de abogados"""
        return self.lawyer_system.generate_lawyer_recommendation_message(visa_category, location)
    
    def format_law_firm_card(self, firm: LawFirm) -> str:
        """Formatear tarjeta de bufete"""
        return self.lawyer_system.format_firm_card(firm)
    
    # =========================================================================
    # DOCUMENTOS
    # =========================================================================
    
    def init_document_checklist(self, visa_type: str):
        """Inicializar checklist de documentos"""
        self.current_visa_type = visa_type
        self.document_checklist = create_document_checklist(self.user_id, visa_type, self.case_storage)
    
    def get_document_checklist_message(self) -> str:
        """Obtener mensaje de checklist de documentos"""
        if not self.document_checklist:
            return "⚠️ Primero necesitas seleccionar un tipo de visa."
        return self.document_checklist.generate_checklist_message()
    
    def get_document_detail(self, doc_id: str) -> str:
        """Obtener detalle de un documento"""
        if not self.document_checklist:
            return "⚠️ Primero necesitas seleccionar un tipo de visa."
        return self.document_checklist.generate_document_detail(doc_id)
    
    def update_document_status(self, doc_id: str, status: DocumentStatus, file_path: Optional[str] = None):
        """Actualizar estado de un documento"""
        if self.document_checklist:
            self.document_checklist.update_status(doc_id, status, file_path)
    
    def get_pending_critical_documents(self) -> List[DocumentRequirement]:
        """Obtener documentos críticos pendientes"""
        if not self.document_checklist:
            return []
        return self.document_checklist.get_pending_critical()
    
    def get_next_document(self) -> Optional[DocumentRequirement]:
        """Obtener siguiente documento a completar"""
        if not self.document_checklist:
            return None
        return self.document_checklist.get_next_document()
    
    # =========================================================================
    # ANÁLISIS DE VISAS
    # =========================================================================
    
    def analyze_visas(self) -> List[VisaRecommendation]:
        """Analizar visas disponibles según el perfil"""
        self.visa_analyzer = create_visa_analyzer(self.profiler.profile_data)
        recommendations = self.visa_analyzer.analyze()
        
        if recommendations:
            self.recommended_visa = recommendations[0]
        
        return recommendations
    
    def get_visa_comparison(self, top_n: int = 5) -> str:
        """Obtener comparación de visas"""
        if not self.visa_analyzer:
            self.analyze_visas()
        
        if self.visa_analyzer:
            return self.visa_analyzer.generate_comparison_table(top_n)
        return "⚠️ No se pudo analizar las visas. Completa más información de tu perfil."
    
    def get_visa_detail(self, visa_type: VisaType) -> str:
        """Obtener detalle de una visa"""
        if not self.visa_analyzer:
            self.analyze_visas()
        
        if self.visa_analyzer:
            return self.visa_analyzer.generate_detailed_recommendation(visa_type)
        return "⚠️ No se pudo obtener información de la visa."
    
    def get_best_visa_recommendation(self) -> Optional[VisaRecommendation]:
        """Obtener mejor recomendación de visa"""
        if not self.visa_analyzer:
            self.analyze_visas()
        
        return self.recommended_visa
    
    # =========================================================================
    # SIMULADOR DE ENTREVISTA
    # =========================================================================
    
    def start_interview_simulation(self, interview_type: InterviewType) -> SimulationSession:
        """Iniciar simulación de entrevista"""
        self.interview_sim = create_interview_simulator(
            self.user_id, 
            interview_type, 
            self.profiler.profile_data
        )
        return self.interview_sim.start_session()
    
    def get_next_interview_question(self) -> Optional[InterviewQuestion]:
        """Obtener siguiente pregunta de entrevista"""
        if not self.interview_sim:
            return None
        return self.interview_sim.get_next_question()
    
    def submit_interview_answer(self, question_id: str, answer: str) -> Dict[str, Any]:
        """Enviar respuesta de entrevista"""
        if not self.interview_sim:
            return {"error": "No hay simulación activa"}
        return self.interview_sim.submit_answer(question_id, answer)
    
    def end_interview_simulation(self) -> Dict[str, Any]:
        """Finalizar simulación de entrevista"""
        if not self.interview_sim:
            return {"error": "No hay simulación activa"}
        return self.interview_sim.end_session()
    
    def format_interview_question(self, question: InterviewQuestion, show_english: bool = True) -> str:
        """Formatear pregunta de entrevista"""
        if not self.interview_sim:
            return "Error"
        return self.interview_sim.format_question_for_telegram(question, show_english)
    
    def get_interview_tips(self, interview_type: InterviewType) -> str:
        """Obtener tips de entrevista"""
        return get_interview_tips(interview_type)
    
    # =========================================================================
    # DASHBOARD COMPLETO
    # =========================================================================
    
    def generate_dashboard(self) -> str:
        """Generar dashboard completo del cliente"""
        # Progreso general
        progress_pct = self.progress.get_overall_percentage()
        
        # Perfil
        profile_completed, profile_total, profile_pct = self.get_profile_completion()
        
        # Familia
        family_count = len(self.family.family_members)
        family_completed = sum(1 for m in self.family.family_members.values() if m.profile_completed)
        
        # Documentos
        doc_stats = None
        if self.document_checklist:
            doc_stats = self.document_checklist.get_completion_stats()
        
        # Visa recomendada
        visa_rec = self.recommended_visa
        
        # Generar mensaje
        msg = f"""
╔══════════════════════════════════════════╗
║       🌟 TU DASHBOARD MIGPAL 🌟          ║
╚══════════════════════════════════════════╝

📊 **PROGRESO GENERAL**
{self._generate_progress_bar(progress_pct, 20)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **PERFIL PERSONAL**
{self._generate_progress_bar(profile_pct, 15)} {profile_completed}/{profile_total}
"""
        
        if family_count > 0:
            msg += f"""
👨‍👩‍👧‍👦 **FAMILIA**
Miembros: {family_count} | Completos: {family_completed}
"""
        
        if doc_stats:
            msg += f"""
📁 **DOCUMENTOS**
{self._generate_progress_bar(doc_stats['percentage'], 15)} {doc_stats['completed']}/{doc_stats['total']}
"""
        
        if visa_rec:
            msg += f"""
🎯 **VISA RECOMENDADA**
{VISA_DATABASE[visa_rec.visa_type].emoji} {VISA_DATABASE[visa_rec.visa_type].name}
Probabilidad: {visa_rec.probability:.0f}%
"""
        
        # Próximo paso
        next_field = self.get_next_profile_field()
        if next_field:
            msg += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 **PRÓXIMO PASO:**
{next_field.emoji} Completar: {next_field.name}

Usa /perfil para continuar
"""
        
        return msg
    
    def _generate_progress_bar(self, percentage: float, width: int = 10) -> str:
        """Generar barra de progreso"""
        filled = int(width * percentage / 100)
        empty = width - filled
        bar = "▓" * filled + "░" * empty
        return f"[{bar}] {percentage:.0f}%"
    
    # =========================================================================
    # MENSAJES DE ESTADO
    # =========================================================================
    
    def get_status_footer(self) -> str:
        """Obtener footer de estado para agregar a mensajes"""
        progress_pct = self.progress.get_overall_percentage()
        stage_info = STAGES_INFO[self.progress.progress.current_stage]
        
        pending = self.progress.get_pending_items()
        pending_count = len(pending)
        
        footer = f"\n━━━━━━━━━━━━━━━━━━━━\n"
        footer += f"📊 {progress_pct:.0f}% | {stage_info.emoji} {stage_info.name}"
        
        if pending_count > 0:
            footer += f" | 📋 {pending_count} pendiente(s)"
        
        return footer
    
    def get_pending_items_message(self) -> str:
        """Obtener mensaje de items pendientes"""
        pending = self.progress.get_pending_items()
        
        if not pending:
            return "✅ ¡No tienes items pendientes en esta etapa!"
        
        msg = "📋 **PENDIENTE POR COMPLETAR:**\n\n"
        
        for i, item in enumerate(pending, 1):
            action = self.progress._get_action_for_item(item)
            msg += f"{i}. ⬜ **{item}**\n"
            msg += f"   _{action['description']}_\n"
            msg += f"   Comando: `{action['command']}`\n\n"
        
        return msg


# =========================================================================
# FUNCIONES DE UTILIDAD GLOBALES
# =========================================================================

# Cache de clientes
_client_cache: Dict[int, MigPALClient] = {}


def get_migpal_client(user_id: int, case_storage=None, bot_username: str = "MigPAL_Bot") -> MigPALClient:
    """Obtener o crear cliente MigPAL para un usuario"""
    if user_id not in _client_cache:
        _client_cache[user_id] = MigPALClient(user_id, case_storage, bot_username)
    return _client_cache[user_id]


def clear_client_cache(user_id: Optional[int] = None):
    """Limpiar cache de clientes"""
    global _client_cache
    if user_id:
        if user_id in _client_cache:
            del _client_cache[user_id]
    else:
        _client_cache = {}


def handle_family_invitation_start(token: str, telegram_id: int) -> Tuple[bool, str, Optional[int]]:
    """
    Manejar cuando un usuario inicia el bot con un token de invitación familiar.
    Retorna: (success, message, principal_user_id)
    """
    # Buscar la invitación en todos los clientes
    for principal_id, client in _client_cache.items():
        invitation = client.validate_family_invitation(token)
        if invitation:
            member = client.accept_family_invitation(token, telegram_id)
            if member:
                return (
                    True,
                    f"✅ ¡Bienvenido/a {member.full_name}!\n\n"
                    f"Has sido invitado/a por tu familiar para completar tu perfil migratorio.\n\n"
                    f"Vamos a hacerte algunas preguntas para tu caso.",
                    principal_id
                )
    
    # Buscar en el handler global
    inv_info = FamilyInvitationHandler.get_invitation_info(token)
    if inv_info:
        return (
            True,
            f"✅ ¡Bienvenido/a {inv_info['name']}!\n\n"
            f"Has sido invitado/a para completar tu perfil migratorio.\n\n"
            f"Vamos a hacerte algunas preguntas.",
            inv_info['case_id']
        )
    
    return (False, "❌ El enlace de invitación no es válido o ha expirado.", None)


# =========================================================================
# CONSTANTES EXPORTADAS
# =========================================================================

# Precios del sistema
MIGPAL_PRICES = {
    "phase_0": 0,  # Registro y consulta - GRATIS
    "phase_1": 50,  # Diagnóstico
    "phase_2": 100,  # Perfilamiento completo
    "phase_3": 200,  # Plan de migración
    "lawyer_referral": 50,  # Referido a abogado (se descuenta de consulta)
    "total_basic": 350,  # Total sin plan de migración
    "total_complete": 350,  # Total completo
}

# Mensajes del sistema
SYSTEM_MESSAGES = {
    "welcome": """
🌟 **¡Bienvenido a MigPAL!** 🌟

Tu asistente inteligente para migrar a Estados Unidos.

📊 **¿Qué puedo hacer por ti?**
• Evaluar tus opciones de visa
• Crear tu perfil migratorio completo
• Conectarte con abogados especializados
• Prepararte para tu entrevista consular
• Guiarte paso a paso en todo el proceso

💰 **Nuestros precios:**
• Consulta inicial: GRATIS
• Diagnóstico completo: $50 USD
• Perfilamiento exhaustivo: $100 USD
• Plan de migración: $200 USD

🚀 **¿Listo para comenzar?**
Usa /perfil para empezar tu perfilamiento.
""",
    
    "lawyer_needed": """
⚖️ **IMPORTANTE: Tu caso requiere abogado**

El tipo de visa que necesitas requiere representación legal profesional.

💡 **¿Cómo funciona con MigPAL?**
1. Pagas solo **$50 USD** a MigPAL
2. Te conectamos con bufetes especializados
3. Tu primera consulta es **GRATIS**
4. Los $50 se descuentan si contratas el caso

✨ **Beneficio:** Ahorras $100-$350 en la consulta inicial

Usa /abogado para ver los bufetes recomendados.
""",
    
    "profile_complete": """
🎉 **¡Felicidades!**

Has completado tu perfil migratorio.

📊 **Próximos pasos:**
1. Revisa tu análisis de visas con /visas
2. Prepárate para tu entrevista con /entrevista
3. Revisa tu checklist de documentos con /documentos

¿Tienes preguntas? Estoy aquí para ayudarte.
""",
}


__all__ = [
    # Clase principal
    'MigPALClient',
    
    # Funciones de utilidad
    'get_migpal_client',
    'clear_client_cache',
    'handle_family_invitation_start',
    
    # Constantes
    'MIGPAL_PRICES',
    'SYSTEM_MESSAGES',
    
    # Re-exportar módulos
    'ProgressTracker', 'ProcessStage', 'STAGES_INFO', 'PHASES_INFO',
    'DetailedProfiler', 'ProfileSection', 'ProfileField', 'PROFILE_FIELDS',
    'FamilyProfiler', 'FamilyRole', 'FamilyMember', 'FAMILY_MEMBER_FIELDS',
    'LawyerReferralSystem', 'LawyerVisaCategory', 'LawFirm', 'PARTNER_LAW_FIRMS',
    'DocumentChecklist', 'DocumentStatus', 'DOCUMENT_REQUIREMENTS',
    'VisaAnalyzer', 'VisaType', 'VisaRecommendation', 'VISA_DATABASE',
    'InterviewSimulator', 'InterviewType', 'INTERVIEW_QUESTIONS',
]
