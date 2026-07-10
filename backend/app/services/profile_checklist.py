"""
MigPAL Profile Checklist v1.0 - RAG + Checklist
================================================
Implementa el checklist de datos requeridos para decisiones críticas.

REGLA DURA: No se puede recomendar visa ni generar plan sin checklist completo.

Checklist requerido:
- familia: composición familiar, edades de hijos
- edad: fecha de nacimiento o edad del solicitante
- idioma: nivel de inglés y otros idiomas
- presupuesto: ahorros, ingresos, capacidad de inversión
- estatus: visa actual, historial migratorio, problemas legales
- objetivo_usa: razón de migración, estado destino, timeline

Este módulo NO aprende de usuarios reales - solo usa datos curados.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ChecklistCategory(Enum):
    """Categorías del checklist"""

    FAMILIA = "familia"
    EDAD = "edad"
    IDIOMA = "idioma"
    PRESUPUESTO = "presupuesto"
    ESTATUS = "estatus"
    OBJETIVO_USA = "objetivo_usa"


@dataclass
class ChecklistField:
    """Campo individual del checklist"""

    name: str
    category: ChecklistCategory
    required: bool = True
    confirmed: bool = False
    value: Any = None
    source: str = ""  # "user_input", "inferred", "default"
    confirmed_at: datetime | None = None


@dataclass
class ChecklistStatus:
    """Estado completo del checklist"""

    user_id: int
    fields: dict[str, ChecklistField] = field(default_factory=dict)
    completion_percentage: float = 0.0
    missing_required: list[str] = field(default_factory=list)
    ready_for_recommendation: bool = False
    last_updated: datetime | None = None


# ============== DEFINICIÓN DEL CHECKLIST ==============

CHECKLIST_DEFINITION = {
    ChecklistCategory.FAMILIA: {
        "fields": [
            {
                "name": "has_family",
                "required": True,
                "question_es": "¿Viajas solo o con familia?",
                "question_en": "Are you traveling alone or with family?",
            },
            {
                "name": "family_count",
                "required": False,
                "question_es": "¿Cuántas personas viajan contigo?",
                "question_en": "How many people are traveling with you?",
            },
            {
                "name": "children_ages",
                "required": False,
                "question_es": "¿Qué edades tienen tus hijos?",
                "question_en": "How old are your children?",
            },
            {
                "name": "spouse_profession",
                "required": False,
                "question_es": "¿A qué se dedica tu pareja?",
                "question_en": "What does your spouse do?",
            },
        ],
        "priority": 1,
        "description_es": "Composición familiar",
        "description_en": "Family composition",
    },
    ChecklistCategory.EDAD: {
        "fields": [
            {
                "name": "birth_date",
                "required": True,
                "question_es": "¿Cuál es tu fecha de nacimiento?",
                "question_en": "What is your date of birth?",
            },
            {
                "name": "age",
                "required": True,
                "question_es": "¿Cuántos años tienes?",
                "question_en": "How old are you?",
            },
        ],
        "priority": 2,
        "description_es": "Edad del solicitante",
        "description_en": "Applicant's age",
    },
    ChecklistCategory.IDIOMA: {
        "fields": [
            {
                "name": "english_level",
                "required": True,
                "question_es": "¿Cuál es tu nivel de inglés?",
                "question_en": "What is your English level?",
            },
            {
                "name": "other_languages",
                "required": False,
                "question_es": "¿Hablas otros idiomas?",
                "question_en": "Do you speak other languages?",
            },
        ],
        "priority": 3,
        "description_es": "Nivel de idiomas",
        "description_en": "Language proficiency",
    },
    ChecklistCategory.PRESUPUESTO: {
        "fields": [
            {
                "name": "savings",
                "required": True,
                "question_es": "¿Cuánto tienes ahorrado aproximadamente?",
                "question_en": "How much do you have saved approximately?",
            },
            {
                "name": "monthly_income",
                "required": False,
                "question_es": "¿Cuál es tu ingreso mensual?",
                "question_en": "What is your monthly income?",
            },
            {
                "name": "investment_capacity",
                "required": False,
                "question_es": "¿Tienes capacidad de inversión?",
                "question_en": "Do you have investment capacity?",
            },
        ],
        "priority": 4,
        "description_es": "Situación financiera",
        "description_en": "Financial situation",
    },
    ChecklistCategory.ESTATUS: {
        "fields": [
            {
                "name": "current_visa",
                "required": False,
                "question_es": "¿Tienes alguna visa actualmente?",
                "question_en": "Do you currently have any visa?",
            },
            {
                "name": "visa_history",
                "required": True,
                "question_es": "¿Has tenido visas antes? ¿Cuáles?",
                "question_en": "Have you had visas before? Which ones?",
            },
            {
                "name": "visa_denials",
                "required": True,
                "question_es": "¿Te han negado alguna visa?",
                "question_en": "Have you been denied any visa?",
            },
            {
                "name": "legal_issues",
                "required": True,
                "question_es": "¿Tienes algún problema legal o antecedente?",
                "question_en": "Do you have any legal issues or records?",
            },
        ],
        "priority": 5,
        "description_es": "Estatus migratorio",
        "description_en": "Immigration status",
    },
    ChecklistCategory.OBJETIVO_USA: {
        "fields": [
            {
                "name": "migration_reason",
                "required": True,
                "question_es": "¿Por qué quieres migrar a USA?",
                "question_en": "Why do you want to migrate to the USA?",
            },
            {
                "name": "target_state",
                "required": False,
                "question_es": "¿Tienes algún estado en mente?",
                "question_en": "Do you have any state in mind?",
            },
            {
                "name": "timeline",
                "required": True,
                "question_es": "¿En cuánto tiempo te gustaría migrar?",
                "question_en": "When would you like to migrate?",
            },
            {
                "name": "has_contacts_usa",
                "required": False,
                "question_es": "¿Tienes familia o contactos en USA?",
                "question_en": "Do you have family or contacts in the USA?",
            },
        ],
        "priority": 6,
        "description_es": "Objetivo en USA",
        "description_en": "USA objective",
    },
}

# Campos adicionales del perfil profesional (para visa analysis)
PROFESSIONAL_FIELDS = {
    "profession": {
        "required": True,
        "question_es": "¿Cuál es tu profesión?",
        "question_en": "What is your profession?",
    },
    "education_level": {
        "required": True,
        "question_es": "¿Cuál es tu nivel educativo?",
        "question_en": "What is your education level?",
    },
    "experience_years": {
        "required": True,
        "question_es": "¿Cuántos años de experiencia tienes?",
        "question_en": "How many years of experience do you have?",
    },
    "achievements": {
        "required": False,
        "question_es": "¿Tienes logros destacados en tu campo?",
        "question_en": "Do you have notable achievements in your field?",
    },
}


class ProfileChecklist:
    """
    Gestor del checklist de perfil.

    REGLA: No se puede avanzar a decisiones críticas sin checklist completo.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._user_checklists: dict[int, ChecklistStatus] = {}
        return cls._instance

    def get_checklist(self, user_id: int) -> ChecklistStatus:
        """Obtiene el checklist de un usuario"""
        if user_id not in self._user_checklists:
            self._user_checklists[user_id] = self._create_empty_checklist(user_id)
        return self._user_checklists[user_id]

    def _create_empty_checklist(self, user_id: int) -> ChecklistStatus:
        """Crea un checklist vacío"""
        fields = {}
        for category, config in CHECKLIST_DEFINITION.items():
            for field_def in config["fields"]:
                fields[field_def["name"]] = ChecklistField(
                    name=field_def["name"], category=category, required=field_def["required"]
                )
        return ChecklistStatus(user_id=user_id, fields=fields)

    def update_from_profile(self, user_id: int, user_data: dict[str, Any]) -> ChecklistStatus:
        """
        Actualiza el checklist desde los datos del perfil.
        Solo marca como confirmado lo que el usuario ha proporcionado explícitamente.
        """
        checklist = self.get_checklist(user_id)
        profile = user_data.get("profile", {})

        # Mapeo de campos del perfil a campos del checklist
        field_mappings = {
            # Personal
            "birth_date": ("personal", "birth_date"),
            "age": ("personal", "age"),
            # Familia
            "has_family": ("personal", "has_family"),
            "family_count": ("personal", "family_count"),
            "children_ages": ("personal", "children_ages"),
            "spouse_profession": ("personal", "spouse_profession"),
            # Idiomas
            "english_level": ("languages", "english"),
            "other_languages": ("languages", "other"),
            # Presupuesto
            "savings": ("financial", "savings"),
            "monthly_income": ("financial", "monthly_income"),
            "investment_capacity": ("financial", "investment_capacity"),
            # Estatus
            "current_visa": ("history", "current_visa"),
            "visa_history": ("history", "visa_history"),
            "visa_denials": ("history", "visa_denials"),
            "legal_issues": ("history", "legal_issues"),
            # Objetivo
            "migration_reason": ("migration", "reason"),
            "target_state": ("migration", "target_state"),
            "timeline": ("migration", "timeline"),
            "has_contacts_usa": ("migration", "has_contacts"),
            # Profesional
            "profession": ("work", "profession"),
            "education_level": ("education", "level"),
            "experience_years": ("work", "experience_years"),
            "achievements": ("work", "achievements"),
        }

        for field_name, (section, key) in field_mappings.items():
            if field_name in checklist.fields:
                section_data = profile.get(section, {})
                value = section_data.get(key)

                if value is not None and value != "" and value != []:
                    checklist.fields[field_name].confirmed = True
                    checklist.fields[field_name].value = value
                    checklist.fields[field_name].source = "user_input"
                    checklist.fields[field_name].confirmed_at = datetime.now()

        # Calcular porcentaje de completitud
        self._calculate_completion(checklist)
        checklist.last_updated = datetime.now()

        return checklist

    def _calculate_completion(self, checklist: ChecklistStatus):
        """Calcula el porcentaje de completitud y campos faltantes"""
        required_fields = [f for f in checklist.fields.values() if f.required]
        confirmed_required = [f for f in required_fields if f.confirmed]

        if required_fields:
            checklist.completion_percentage = len(confirmed_required) / len(required_fields) * 100
        else:
            checklist.completion_percentage = 100.0

        checklist.missing_required = [f.name for f in required_fields if not f.confirmed]
        checklist.ready_for_recommendation = len(checklist.missing_required) == 0

    def get_next_question(self, user_id: int, lang: str = "es") -> tuple[str, str] | None:
        """
        Obtiene la siguiente pregunta para completar el checklist.
        Retorna (field_name, question) o None si está completo.
        """
        checklist = self.get_checklist(user_id)

        # Ordenar por prioridad de categoría
        for category in sorted(
            CHECKLIST_DEFINITION.keys(), key=lambda c: CHECKLIST_DEFINITION[c]["priority"]
        ):
            for field_def in CHECKLIST_DEFINITION[category]["fields"]:
                field_name = field_def["name"]
                if field_name in checklist.fields:
                    field = checklist.fields[field_name]
                    if field.required and not field.confirmed:
                        question_key = f"question_{lang}"
                        question = field_def.get(question_key, field_def.get("question_es", ""))
                        return (field_name, question)

        return None

    def get_missing_summary(self, user_id: int, lang: str = "es") -> str:
        """Genera un resumen de los campos faltantes"""
        checklist = self.get_checklist(user_id)

        if checklist.ready_for_recommendation:
            if lang == "es":
                return "✅ Tu perfil está completo para recibir recomendaciones."
            else:
                return "✅ Your profile is complete to receive recommendations."

        missing_by_category = {}
        for field_name in checklist.missing_required:
            if field_name in checklist.fields:
                category = checklist.fields[field_name].category
                if category not in missing_by_category:
                    missing_by_category[category] = []
                missing_by_category[category].append(field_name)

        if lang == "es":
            summary = f"📋 **Checklist de perfil** ({checklist.completion_percentage:.0f}% completo)\n\n"
            summary += "Necesito conocer más sobre:\n"
            for category, _fields in missing_by_category.items():
                desc = CHECKLIST_DEFINITION[category]["description_es"]
                summary += f"• {desc}\n"
        else:
            summary = f"📋 **Profile Checklist** ({checklist.completion_percentage:.0f}% complete)\n\n"
            summary += "I need to know more about:\n"
            for category, _fields in missing_by_category.items():
                desc = CHECKLIST_DEFINITION[category]["description_en"]
                summary += f"• {desc}\n"

        return summary

    def can_recommend_visa(self, user_id: int, user_data: dict[str, Any]) -> tuple[bool, str]:
        """
        Verifica si se puede recomendar visa.

        REGLA DURA: No recomendar sin checklist mínimo completo.

        Returns:
            (can_recommend, reason)
        """
        checklist = self.update_from_profile(user_id, user_data)

        # Campos mínimos para recomendación de visa
        minimum_for_visa = [
            "age",
            "english_level",
            "profession",
            "education_level",
            "migration_reason",
            "visa_history",
            "legal_issues",
        ]

        missing = []
        for field_name in minimum_for_visa:
            if field_name in checklist.fields:
                if not checklist.fields[field_name].confirmed:
                    missing.append(field_name)

        if missing:
            return False, f"missing_fields:{','.join(missing)}"

        return True, "ready"

    def can_generate_plan(self, user_id: int, user_data: dict[str, Any]) -> tuple[bool, str]:
        """
        Verifica si se puede generar plan de migración.

        REGLA DURA: Plan requiere checklist completo.

        Returns:
            (can_generate, reason)
        """
        checklist = self.update_from_profile(user_id, user_data)

        if not checklist.ready_for_recommendation:
            return False, f"incomplete_checklist:{','.join(checklist.missing_required)}"

        return True, "ready"

    def reset_user(self, user_id: int):
        """Resetea el checklist de un usuario"""
        if user_id in self._user_checklists:
            del self._user_checklists[user_id]
        logger.info(f"🔄 CHECKLIST | user={user_id} | reset=True")


# Singleton instance
_profile_checklist: ProfileChecklist | None = None


def get_profile_checklist() -> ProfileChecklist:
    """Obtiene la instancia singleton del checklist"""
    global _profile_checklist
    if _profile_checklist is None:
        _profile_checklist = ProfileChecklist()
    return _profile_checklist


def check_profile_completeness(user_id: int, user_data: dict[str, Any]) -> dict[str, Any]:
    """
    Función de conveniencia para verificar completitud del perfil.

    Returns:
        {
            "complete": bool,
            "percentage": float,
            "missing": List[str],
            "next_question": Optional[Tuple[str, str]],
            "can_recommend_visa": bool,
            "can_generate_plan": bool
        }
    """
    checklist_manager = get_profile_checklist()
    checklist = checklist_manager.update_from_profile(user_id, user_data)
    lang = user_data.get("language", "es")

    can_visa, visa_reason = checklist_manager.can_recommend_visa(user_id, user_data)
    can_plan, plan_reason = checklist_manager.can_generate_plan(user_id, user_data)

    return {
        "complete": checklist.ready_for_recommendation,
        "percentage": checklist.completion_percentage,
        "missing": checklist.missing_required,
        "next_question": checklist_manager.get_next_question(user_id, lang),
        "can_recommend_visa": can_visa,
        "can_generate_plan": can_plan,
        "summary": checklist_manager.get_missing_summary(user_id, lang),
    }
