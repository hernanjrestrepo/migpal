#!/usr/bin/env python3
"""
MigPAL Understanding Summary v3.1.0
====================================
REGLA CRÍTICA: Prohibido recomendar visa o mostrar "pasos" sin un
Resumen de Entendimiento confirmado por el usuario.

Este módulo implementa:
1. Generación de resumen de lo que MigPAL ha entendido del usuario
2. Solicitud de confirmación explícita antes de avanzar
3. Bloqueo de recomendaciones de visa sin confirmación
4. Tracking de qué información ha sido confirmada

Flujo:
1. Usuario proporciona información (conversacional o formulario)
2. MigPAL extrae y guarda datos
3. Antes de recomendar visa → mostrar Resumen de Entendimiento
4. Usuario confirma o corrige
5. Solo después de confirmación → mostrar recomendaciones

"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ConfirmationStatus(Enum):
    """Estado de confirmación del resumen"""

    NOT_SHOWN = "not_shown"  # Nunca se ha mostrado resumen
    PENDING = "pending"  # Se mostró pero no se confirmó
    CONFIRMED = "confirmed"  # Usuario confirmó
    NEEDS_CORRECTION = "correction"  # Usuario indicó que hay errores


@dataclass
class UnderstandingSummary:
    """Resumen de lo que MigPAL ha entendido del usuario"""

    user_id: int
    status: ConfirmationStatus = ConfirmationStatus.NOT_SHOWN
    last_shown: datetime | None = None
    last_confirmed: datetime | None = None
    confirmed_sections: list[str] = field(default_factory=list)
    pending_corrections: list[str] = field(default_factory=list)

    # Datos confirmados
    personal_confirmed: bool = False
    education_confirmed: bool = False
    work_confirmed: bool = False
    family_confirmed: bool = False
    motivation_confirmed: bool = False
    restrictions_confirmed: bool = False


class UnderstandingSummaryManager:
    """
    Gestiona los resúmenes de entendimiento.
    REGLA: Sin confirmación, no hay recomendación de visa.
    """

    _instance = None
    _summaries: dict[int, UnderstandingSummary] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._summaries = {}
        return cls._instance

    def get_summary(self, user_id: int) -> UnderstandingSummary:
        """Obtiene o crea el resumen de un usuario"""
        if user_id not in self._summaries:
            self._summaries[user_id] = UnderstandingSummary(user_id=user_id)
        return self._summaries[user_id]

    def generate_summary_text(
        self, user_data: dict[str, Any], lang: str = "es"
    ) -> tuple[str, list[tuple[str, str]]]:
        """
        Genera el texto del resumen de entendimiento.

        Returns:
            Tuple[str, List[Tuple[str, str]]]: (texto_resumen, botones)
        """
        profile = user_data.get("profile", {})
        personal = profile.get("personal", {})
        education = profile.get("education", {})
        work = profile.get("work", {})
        migration = profile.get("migration", {})
        history = profile.get("history", {})
        preferences = user_data.get("preferences", {})
        family_members = user_data.get("family_members", [])

        if lang == "es":
            # Construir resumen en español
            summary = "📋 *RESUMEN DE LO QUE ENTENDÍ*\n\n"
            summary += (
                "Antes de darte recomendaciones, quiero asegurarme de que entendí bien tu situación:\n\n"
            )

            # Datos personales
            summary += "👤 *SOBRE TI:*\n"
            name = personal.get("name", "")
            if name:
                summary += f"• Nombre: {name}\n"
            age = personal.get("age") or personal.get("birth_date", "")
            if age:
                summary += f"• Edad/Nacimiento: {age}\n"
            nationality = personal.get("nationality", "")
            if nationality:
                summary += f"• Nacionalidad: {nationality}\n"
            current_city = personal.get("current_city", "")
            current_country = personal.get("current_country", "")
            if current_city or current_country:
                summary += f"• Ubicación actual: {current_city}, {current_country}\n"

            # Educación
            edu_level = education.get("level", "")
            edu_career = education.get("career", "")
            if edu_level or edu_career:
                summary += "\n🎓 *EDUCACIÓN:*\n"
                if edu_level:
                    summary += f"• Nivel: {edu_level}\n"
                if edu_career:
                    summary += f"• Carrera: {edu_career}\n"

            # Trabajo
            profession = work.get("profession", "")
            experience = work.get("experience", "")
            if profession or experience:
                summary += "\n💼 *TRABAJO:*\n"
                if profession:
                    summary += f"• Profesión: {profession}\n"
                if experience:
                    summary += f"• Experiencia: {experience}\n"

            # Familia
            family_status = user_data.get("family_status", "")
            if family_status or family_members:
                summary += "\n👨‍👩‍👧 *FAMILIA:*\n"
                if family_status:
                    summary += f"• Estado: {family_status}\n"
                if family_members:
                    summary += f"• Miembros: {len(family_members)} persona(s)\n"
                    for member in family_members[:3]:  # Mostrar máx 3
                        relation = member.get("relation", "")
                        name = member.get("name", "")
                        if relation and name:
                            summary += f"  - {relation}: {name}\n"

            # Motivación
            reason = migration.get("reason_text") or preferences.get("migration_reason", "")
            if reason:
                summary += "\n🎯 *MOTIVACIÓN:*\n"
                summary += f"• Razón para migrar: {reason}\n"

            # Historial
            has_visas = history.get("has_visas", "")
            rejections = history.get("rejections", "")
            criminal = history.get("criminal_record", "")
            if has_visas or rejections or criminal:
                summary += "\n📋 *HISTORIAL:*\n"
                if has_visas:
                    summary += f"• Visas previas: {has_visas}\n"
                if rejections:
                    summary += f"• Rechazos: {rejections}\n"
                if criminal:
                    summary += f"• Antecedentes: {criminal}\n"

            # Destino preferido
            route = user_data.get("selected_route", {})
            dest_country = route.get("country", "")
            dest_state = route.get("state", "")
            dest_city = route.get("city", "")
            if dest_country or dest_state or dest_city:
                summary += "\n🗺️ *DESTINO PREFERIDO:*\n"
                if dest_country:
                    summary += f"• País: {dest_country}\n"
                if dest_state:
                    summary += f"• Estado: {dest_state}\n"
                if dest_city:
                    summary += f"• Ciudad: {dest_city}\n"

            summary += "\n" + "─" * 30 + "\n\n"
            summary += "¿Esta información es correcta? 🤔"

            buttons = [
                ("✅ Sí, todo correcto", "summary_confirm"),
                ("✏️ Necesito corregir algo", "summary_correct"),
                ("➕ Falta información", "summary_add_info"),
            ]

        else:
            # English version
            summary = "📋 *SUMMARY OF WHAT I UNDERSTOOD*\n\n"
            summary += "Before giving you recommendations, I want to make sure I understood your situation correctly:\n\n"

            # Personal data
            summary += "👤 *ABOUT YOU:*\n"
            name = personal.get("name", "")
            if name:
                summary += f"• Name: {name}\n"
            age = personal.get("age") or personal.get("birth_date", "")
            if age:
                summary += f"• Age/Birth: {age}\n"
            nationality = personal.get("nationality", "")
            if nationality:
                summary += f"• Nationality: {nationality}\n"
            current_city = personal.get("current_city", "")
            current_country = personal.get("current_country", "")
            if current_city or current_country:
                summary += f"• Current location: {current_city}, {current_country}\n"

            # Education
            edu_level = education.get("level", "")
            edu_career = education.get("career", "")
            if edu_level or edu_career:
                summary += "\n🎓 *EDUCATION:*\n"
                if edu_level:
                    summary += f"• Level: {edu_level}\n"
                if edu_career:
                    summary += f"• Career: {edu_career}\n"

            # Work
            profession = work.get("profession", "")
            experience = work.get("experience", "")
            if profession or experience:
                summary += "\n💼 *WORK:*\n"
                if profession:
                    summary += f"• Profession: {profession}\n"
                if experience:
                    summary += f"• Experience: {experience}\n"

            # Family
            family_status = user_data.get("family_status", "")
            if family_status or family_members:
                summary += "\n👨‍👩‍👧 *FAMILY:*\n"
                if family_status:
                    summary += f"• Status: {family_status}\n"
                if family_members:
                    summary += f"• Members: {len(family_members)} person(s)\n"

            # Motivation
            reason = migration.get("reason_text") or preferences.get("migration_reason", "")
            if reason:
                summary += "\n🎯 *MOTIVATION:*\n"
                summary += f"• Reason to migrate: {reason}\n"

            summary += "\n" + "─" * 30 + "\n\n"
            summary += "Is this information correct? 🤔"

            buttons = [
                ("✅ Yes, all correct", "summary_confirm"),
                ("✏️ I need to correct something", "summary_correct"),
                ("➕ Missing information", "summary_add_info"),
            ]

        return summary, buttons

    def mark_shown(self, user_id: int):
        """Marca que se mostró el resumen"""
        summary = self.get_summary(user_id)
        summary.status = ConfirmationStatus.PENDING
        summary.last_shown = datetime.now()

    def mark_confirmed(self, user_id: int):
        """Marca que el usuario confirmó el resumen"""
        summary = self.get_summary(user_id)
        summary.status = ConfirmationStatus.CONFIRMED
        summary.last_confirmed = datetime.now()
        logger.info(f"✅ SUMMARY CONFIRMED | user={user_id}")

    def mark_needs_correction(self, user_id: int, field: str = ""):
        """Marca que el usuario necesita corregir algo"""
        summary = self.get_summary(user_id)
        summary.status = ConfirmationStatus.NEEDS_CORRECTION
        if field and field not in summary.pending_corrections:
            summary.pending_corrections.append(field)

    def can_recommend_visa(self, user_id: int) -> tuple[bool, str]:
        """
        Verifica si se puede recomendar visa.
        REGLA: Solo si el resumen ha sido confirmado.

        Returns:
            Tuple[bool, str]: (puede_recomendar, mensaje_si_no)
        """
        summary = self.get_summary(user_id)

        if summary.status == ConfirmationStatus.CONFIRMED:
            return True, ""

        if summary.status == ConfirmationStatus.NOT_SHOWN:
            return False, "need_summary"

        if summary.status == ConfirmationStatus.PENDING:
            return False, "pending_confirmation"

        if summary.status == ConfirmationStatus.NEEDS_CORRECTION:
            return False, "pending_correction"

        return False, "unknown"

    def get_blocking_message(self, reason: str, lang: str = "es") -> str:
        """Obtiene el mensaje de bloqueo según la razón"""
        messages = {
            "es": {
                "need_summary": (
                    "⚠️ Antes de recomendarte una visa, necesito asegurarme de que "
                    "entendí bien tu situación.\n\n"
                    "Usa /resumen para ver lo que he entendido y confirmarlo."
                ),
                "pending_confirmation": (
                    "⏳ Aún no has confirmado el resumen de tu información.\n\n"
                    "Por favor, revisa el resumen y confirma que es correcto "
                    "antes de continuar con las recomendaciones."
                ),
                "pending_correction": (
                    "✏️ Indicaste que hay información que corregir.\n\n"
                    "Por favor, dime qué necesitas cambiar para poder "
                    "darte las mejores recomendaciones."
                ),
            },
            "en": {
                "need_summary": (
                    "⚠️ Before recommending a visa, I need to make sure I "
                    "understood your situation correctly.\n\n"
                    "Use /resumen to see what I understood and confirm it."
                ),
                "pending_confirmation": (
                    "⏳ You haven't confirmed the summary of your information yet.\n\n"
                    "Please review the summary and confirm it's correct "
                    "before continuing with recommendations."
                ),
                "pending_correction": (
                    "✏️ You indicated there's information to correct.\n\n"
                    "Please tell me what you need to change so I can "
                    "give you the best recommendations."
                ),
            },
        }

        lang_messages = messages.get(lang, messages["es"])
        return lang_messages.get(reason, lang_messages["need_summary"])

    def reset_confirmation(self, user_id: int):
        """Resetea la confirmación (cuando hay cambios significativos)"""
        summary = self.get_summary(user_id)
        summary.status = ConfirmationStatus.NOT_SHOWN
        summary.pending_corrections = []
        logger.info(f"🔄 SUMMARY RESET | user={user_id}")

    def should_show_summary(self, user_id: int, user_data: dict[str, Any]) -> bool:
        """
        Determina si se debe mostrar el resumen.
        Se muestra cuando hay suficiente información y no se ha confirmado.
        """
        summary = self.get_summary(user_id)

        # Si ya está confirmado, no mostrar de nuevo
        if summary.status == ConfirmationStatus.CONFIRMED:
            return False

        # Verificar si hay suficiente información
        profile = user_data.get("profile", {})
        personal = profile.get("personal", {})

        # Mínimo: nombre y algún otro dato
        has_name = bool(personal.get("name"))
        has_other = bool(
            personal.get("nationality")
            or personal.get("birth_date")
            or profile.get("work", {}).get("profession")
            or user_data.get("preferences", {}).get("migration_reason")
        )

        return has_name and has_other


# Singleton getter
_summary_manager = None


def get_summary_manager() -> UnderstandingSummaryManager:
    """Obtiene la instancia del gestor de resúmenes"""
    global _summary_manager
    if _summary_manager is None:
        _summary_manager = UnderstandingSummaryManager()
    return _summary_manager


# Helper functions
def can_recommend_visa(user_id: int) -> tuple[bool, str]:
    """Helper para verificar si se puede recomendar visa"""
    return get_summary_manager().can_recommend_visa(user_id)


def generate_understanding_summary(
    user_data: dict[str, Any], lang: str = "es"
) -> tuple[str, list[tuple[str, str]]]:
    """Helper para generar el resumen"""
    return get_summary_manager().generate_summary_text(user_data, lang)


def mark_summary_confirmed(user_id: int):
    """Helper para marcar resumen como confirmado"""
    get_summary_manager().mark_confirmed(user_id)


def mark_summary_shown(user_id: int):
    """Helper para marcar que se mostró el resumen"""
    get_summary_manager().mark_shown(user_id)


def should_show_summary(user_id: int, user_data: dict[str, Any]) -> bool:
    """Helper para verificar si mostrar resumen"""
    return get_summary_manager().should_show_summary(user_id, user_data)


def get_visa_blocking_message(reason: str, lang: str = "es") -> str:
    """Helper para obtener mensaje de bloqueo"""
    return get_summary_manager().get_blocking_message(reason, lang)
