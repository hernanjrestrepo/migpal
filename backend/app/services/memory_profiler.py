"""
MigPAL Memory Profiler - SEGMENTO 3/3: MEMORIA, PERFILADO Y DECISIÓN
=====================================================================
Extracción ≠ decisión.

REGLAS DURAS:
1. Todo dato dicho por el usuario se guarda y se reutiliza
2. Antes de sugerir opciones, MigPAL debe: resumir lo entendido + pedir confirmación explícita
3. Si el usuario corrige algo → no avanzar de fase
4. La visa engine solo puede activarse con perfil completo validado
5. Si falta contexto → MigPAL pregunta, no asume
6. Prioridad: entender la vida deseada, no la visa

Este módulo implementa:
- DataMemory: Guarda TODO lo que dice el usuario
- ProfileValidator: Valida completitud del perfil antes de decisiones
- UnderstandingSummarizer: Resume lo entendido y pide confirmación
- CorrectionTracker: Detecta correcciones y bloquea avance de fase
- LifeGoalExtractor: Extrae la vida deseada, no solo la visa
- DecisionGate: Solo permite decisiones con perfil validado
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ============== CONFIGURACIÓN ==============

# Campos requeridos para perfil completo
REQUIRED_PROFILE_FIELDS = {
    "personal": ["name", "birth_date", "nationality", "current_country"],
    "family": ["family_status"],  # Si tiene familia, se requieren más campos
    "work": ["profession", "work_experience"],
    "education": ["education_level"],
    "migration": ["migration_reason", "timeline"],
    "financial": ["savings"]
}

# Campos adicionales si tiene familia
FAMILY_REQUIRED_FIELDS = ["family_count", "children_ages"]

# Campos para vida deseada (prioridad sobre visa)
LIFE_GOAL_FIELDS = {
    "dream": ["dream_in_usa", "life_goals", "priorities"],
    "location": ["preferred_climate", "city_size", "region_preference"],
    "work_life": ["work_or_business", "industry", "salary_expectation"],
    "family_life": ["school_importance", "safety_importance", "community_importance"]
}


# ============== DATA MEMORY ==============

class DataMemory:
    """
    Guarda TODO lo que dice el usuario y lo reutiliza.
    Regla: Todo dato dicho por el usuario se guarda y se reutiliza.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._user_memory = {}
            cls._instance._extraction_history = {}
        return cls._instance
    
    def store_raw_input(self, user_id: int, text: str, context: str = ""):
        """Guarda el input raw del usuario para análisis posterior"""
        if user_id not in self._user_memory:
            self._user_memory[user_id] = {
                "raw_inputs": [],
                "extracted_data": {},
                "corrections": [],
                "confirmations": []
            }
        
        self._user_memory[user_id]["raw_inputs"].append({
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "context": context
        })
        
        # Mantener solo últimos 100 inputs
        if len(self._user_memory[user_id]["raw_inputs"]) > 100:
            self._user_memory[user_id]["raw_inputs"] = self._user_memory[user_id]["raw_inputs"][-100:]
    
    def extract_and_store(self, user_id: int, text: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae datos del texto y los guarda en el perfil del usuario.
        Retorna los datos extraídos.
        """
        extracted = {}
        text_lower = text.lower()
        
        # Patrones de extracción mejorados
        patterns = {
            # Información personal
            "name": [
                r"(?:me llamo|mi nombre es|soy)\s+([A-Za-záéíóúñÁÉÍÓÚÑ\s]+?)(?:\s*[,.]|$)",
                r"(?:my name is|i'm|i am)\s+([A-Za-z\s]+?)(?:\s*[,.]|$)"
            ],
            "age": [
                r"tengo\s+(\d+)\s+años",
                r"(\d+)\s+años",
                r"i'm\s+(\d+)",
                r"i am\s+(\d+)",
                r"(\d+)\s+years\s+old"
            ],
            "nationality": [
                r"soy\s+(?:de\s+)?([A-Za-záéíóúñÁÉÍÓÚÑ]+)(?:no|na)?",
                r"(?:from|i'm from)\s+([A-Za-z]+)"
            ],
            "current_country": [
                r"vivo\s+en\s+([A-Za-záéíóúñÁÉÍÓÚÑ]+)",
                r"estoy\s+en\s+([A-Za-záéíóúñÁÉÍÓÚÑ]+)",
                r"live\s+in\s+([A-Za-z]+)"
            ],
            "current_city": [
                r"(?:vivo|estoy)\s+en\s+([A-Za-záéíóúñÁÉÍÓÚÑ]+),?\s*([A-Za-záéíóúñÁÉÍÓÚÑ]+)?",
            ],
            
            # Familia
            "family_count": [
                r"(\d+)\s+(?:hijos?|niños?|children|kids)",
                r"(?:tengo|have)\s+(\d+)\s+(?:hijos?|children)"
            ],
            "spouse": [
                r"(?:mi\s+)?(?:esposo|esposa|pareja|wife|husband|partner)",
            ],
            
            # Trabajo
            "profession": [
                r"(?:soy|trabajo como|work as)\s+(?:un\s+|una\s+|a\s+|an\s+)?([A-Za-záéíóúñÁÉÍÓÚÑ\s]+?)(?:\s*[,.]|$)",
                r"(?:mi profesión es|my profession is)\s+([A-Za-záéíóúñÁÉÍÓÚÑ\s]+?)(?:\s*[,.]|$)"
            ],
            "work_experience": [
                r"(\d+)\s+años?\s+(?:de\s+)?(?:experiencia|trabajando)",
                r"(\d+)\s+years?\s+(?:of\s+)?(?:experience|working)"
            ],
            "salary": [
                r"\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:usd|dólares|dolares|dollars)?",
                r"(?:gano|earn|make)\s+\$?\s*(\d+(?:,\d{3})*)"
            ],
            
            # Educación
            "education_level": [
                r"(?:soy|tengo)\s+(?:título de\s+)?(?:licenciado|ingeniero|doctor|maestría|bachiller)",
                r"(?:bachelor|master|phd|doctorate|degree)"
            ],
            "education_field": [
                r"(?:estudié|estudiando|studied|studying)\s+([A-Za-záéíóúñÁÉÍÓÚÑ\s]+?)(?:\s*[,.]|$)"
            ],
            
            # Finanzas
            "savings": [
                r"(?:tengo|ahorros?|savings?)\s+(?:de\s+)?\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
                r"\$?\s*(\d+(?:,\d{3})*)\s+(?:ahorrados?|saved)"
            ],
            
            # Migración
            "migration_reason": [
                r"(?:quiero migrar|want to migrate)\s+(?:por|porque|for|because)\s+(.+?)(?:\.|$)",
                r"(?:mi razón|my reason)\s+(?:es|is)\s+(.+?)(?:\.|$)"
            ],
            "timeline": [
                r"(?:en|within)\s+(\d+)\s+(?:meses?|años?|months?|years?)",
                r"(?:para|by|before)\s+(\d{4})"
            ],
            
            # Vida deseada
            "dream_in_usa": [
                r"(?:mi sueño|my dream)\s+(?:es|is)\s+(.+?)(?:\.|$)",
                r"(?:quiero|want to)\s+(.+?)\s+(?:en usa|in usa|in the us)"
            ],
            "preferred_climate": [
                r"(?:prefiero|prefer)\s+(?:clima\s+)?(?:cálido|frío|templado|warm|cold|temperate)"
            ],
            "city_size": [
                r"(?:ciudad|city)\s+(?:grande|pequeña|mediana|big|small|medium)"
            ]
        }
        
        # Extraer datos
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    value = match.group(1).strip() if match.groups() else True
                    extracted[field] = value
                    break
        
        # Guardar en memoria
        if user_id not in self._user_memory:
            self._user_memory[user_id] = {
                "raw_inputs": [],
                "extracted_data": {},
                "corrections": [],
                "confirmations": []
            }
        
        # Actualizar datos extraídos
        for field, value in extracted.items():
            self._user_memory[user_id]["extracted_data"][field] = {
                "value": value,
                "timestamp": datetime.now().isoformat(),
                "source_text": text[:100]
            }
        
        # Guardar en el perfil del usuario
        self._update_user_profile(user_data, extracted)
        
        return extracted
    
    def _update_user_profile(self, user_data: Dict[str, Any], extracted: Dict[str, Any]):
        """Actualiza el perfil del usuario con los datos extraídos"""
        profile = user_data.setdefault("profile", {})
        
        # Mapeo de campos a secciones del perfil
        field_mapping = {
            "name": ("personal", "name"),
            "age": ("personal", "age"),
            "birth_date": ("personal", "birth_date"),
            "nationality": ("personal", "nationality"),
            "current_country": ("personal", "current_country"),
            "current_city": ("personal", "current_city"),
            "family_count": ("family", "count"),
            "spouse": ("family", "has_spouse"),
            "profession": ("work", "profession"),
            "work_experience": ("work", "experience_years"),
            "salary": ("work", "current_salary"),
            "education_level": ("education", "level"),
            "education_field": ("education", "field"),
            "savings": ("financial", "savings"),
            "migration_reason": ("migration", "reason"),
            "timeline": ("migration", "timeline"),
            "dream_in_usa": ("life_goals", "dream"),
            "preferred_climate": ("preferences", "climate"),
            "city_size": ("preferences", "city_size")
        }
        
        for field, value in extracted.items():
            if field in field_mapping:
                section, key = field_mapping[field]
                if section not in profile:
                    profile[section] = {}
                profile[section][key] = value
    
    def get_all_known_data(self, user_id: int) -> Dict[str, Any]:
        """Obtiene todos los datos conocidos del usuario"""
        if user_id not in self._user_memory:
            return {}
        return self._user_memory[user_id].get("extracted_data", {})
    
    def record_correction(self, user_id: int, field: str, old_value: Any, new_value: Any):
        """Registra una corrección del usuario"""
        if user_id not in self._user_memory:
            self._user_memory[user_id] = {
                "raw_inputs": [],
                "extracted_data": {},
                "corrections": [],
                "confirmations": []
            }
        
        self._user_memory[user_id]["corrections"].append({
            "timestamp": datetime.now().isoformat(),
            "field": field,
            "old_value": old_value,
            "new_value": new_value
        })
    
    def record_confirmation(self, user_id: int, summary_type: str, confirmed: bool):
        """Registra una confirmación del usuario"""
        if user_id not in self._user_memory:
            self._user_memory[user_id] = {
                "raw_inputs": [],
                "extracted_data": {},
                "corrections": [],
                "confirmations": []
            }
        
        self._user_memory[user_id]["confirmations"].append({
            "timestamp": datetime.now().isoformat(),
            "summary_type": summary_type,
            "confirmed": confirmed
        })


# ============== PROFILE VALIDATOR ==============

class ProfileCompleteness(Enum):
    """Niveles de completitud del perfil"""
    EMPTY = "empty"
    MINIMAL = "minimal"
    BASIC = "basic"
    COMPLETE = "complete"
    VALIDATED = "validated"


@dataclass
class ProfileValidationResult:
    """Resultado de validación del perfil"""
    completeness: ProfileCompleteness
    percentage: float
    missing_required: List[str]
    missing_optional: List[str]
    has_family_data: bool
    has_life_goals: bool
    is_ready_for_visa: bool
    summary: str


class ProfileValidator:
    """
    Valida completitud del perfil antes de permitir decisiones.
    Regla: La visa engine solo puede activarse con perfil completo validado.
    """
    
    @staticmethod
    def validate(user_data: Dict[str, Any]) -> ProfileValidationResult:
        """Valida el perfil del usuario y retorna el resultado"""
        profile = user_data.get("profile", {})
        
        missing_required = []
        missing_optional = []
        filled_count = 0
        total_required = 0
        
        # Verificar campos requeridos
        for section, fields in REQUIRED_PROFILE_FIELDS.items():
            section_data = profile.get(section, {})
            for field in fields:
                total_required += 1
                if not section_data.get(field):
                    missing_required.append(f"{section}.{field}")
                else:
                    filled_count += 1
        
        # Si tiene familia, verificar campos adicionales
        has_family = profile.get("family", {}).get("family_status") in ["married", "with_children", "with_family"]
        if has_family:
            family_data = profile.get("family", {})
            for field in FAMILY_REQUIRED_FIELDS:
                total_required += 1
                if not family_data.get(field):
                    missing_required.append(f"family.{field}")
                else:
                    filled_count += 1
        
        # Verificar campos de vida deseada
        has_life_goals = False
        life_goals_data = profile.get("life_goals", {})
        preferences_data = profile.get("preferences", {})
        
        for section, fields in LIFE_GOAL_FIELDS.items():
            section_data = life_goals_data if section in ["dream", "work_life", "family_life"] else preferences_data
            for field in fields:
                if section_data.get(field):
                    has_life_goals = True
                else:
                    missing_optional.append(f"{section}.{field}")
        
        # Calcular porcentaje
        percentage = (filled_count / total_required * 100) if total_required > 0 else 0
        
        # Determinar nivel de completitud
        if percentage == 0:
            completeness = ProfileCompleteness.EMPTY
        elif percentage < 30:
            completeness = ProfileCompleteness.MINIMAL
        elif percentage < 70:
            completeness = ProfileCompleteness.BASIC
        elif percentage < 100:
            completeness = ProfileCompleteness.COMPLETE
        else:
            # Verificar si está validado (confirmado por el usuario)
            confirmations = user_data.get("confirmations", [])
            if any(c.get("summary_type") == "profile" and c.get("confirmed") for c in confirmations):
                completeness = ProfileCompleteness.VALIDATED
            else:
                completeness = ProfileCompleteness.COMPLETE
        
        # Determinar si está listo para visa
        is_ready_for_visa = (
            completeness in [ProfileCompleteness.COMPLETE, ProfileCompleteness.VALIDATED] and
            len(missing_required) == 0
        )
        
        # Generar resumen
        summary = ProfileValidator._generate_summary(
            completeness, percentage, missing_required, has_life_goals
        )
        
        return ProfileValidationResult(
            completeness=completeness,
            percentage=percentage,
            missing_required=missing_required,
            missing_optional=missing_optional,
            has_family_data=has_family,
            has_life_goals=has_life_goals,
            is_ready_for_visa=is_ready_for_visa,
            summary=summary
        )
    
    @staticmethod
    def _generate_summary(completeness: ProfileCompleteness, percentage: float,
                          missing: List[str], has_life_goals: bool) -> str:
        """Genera un resumen del estado del perfil"""
        if completeness == ProfileCompleteness.EMPTY:
            return "Aún no tengo información sobre ti."
        elif completeness == ProfileCompleteness.MINIMAL:
            return f"Tengo muy poca información ({percentage:.0f}%). Necesito conocerte mejor."
        elif completeness == ProfileCompleteness.BASIC:
            return f"Tengo información básica ({percentage:.0f}%). Faltan algunos datos importantes."
        elif completeness == ProfileCompleteness.COMPLETE:
            if has_life_goals:
                return f"Perfil completo ({percentage:.0f}%). Listo para confirmar."
            else:
                return f"Perfil casi completo ({percentage:.0f}%). Me gustaría entender mejor tus metas de vida."
        else:
            return f"Perfil validado ({percentage:.0f}%). ¡Listo para recomendaciones!"


# ============== UNDERSTANDING SUMMARIZER ==============

class UnderstandingSummarizer:
    """
    Resume lo entendido y pide confirmación explícita.
    Regla: Antes de sugerir opciones, MigPAL debe resumir lo entendido + pedir confirmación.
    """
    
    @staticmethod
    def generate_summary(user_data: Dict[str, Any], lang: str = "es") -> Tuple[str, List[Tuple[str, str]]]:
        """
        Genera un resumen de lo entendido y botones de confirmación.
        Returns: (summary_text, [(button_text, callback_data), ...])
        """
        profile = user_data.get("profile", {})
        personal = profile.get("personal", {})
        work = profile.get("work", {})
        education = profile.get("education", {})
        family = profile.get("family", {})
        migration = profile.get("migration", {})
        life_goals = profile.get("life_goals", {})
        financial = profile.get("financial", {})
        
        if lang == "es":
            summary_parts = ["📋 *RESUMEN DE LO QUE ENTENDÍ*\n"]
            
            # Personal
            if personal.get("name"):
                summary_parts.append(f"👤 *Nombre:* {personal['name']}")
            if personal.get("age") or personal.get("birth_date"):
                age = personal.get("age") or "calculando..."
                summary_parts.append(f"🎂 *Edad:* {age} años")
            if personal.get("nationality"):
                summary_parts.append(f"🌍 *Nacionalidad:* {personal['nationality']}")
            if personal.get("current_country"):
                city = personal.get("current_city", "")
                location = f"{city}, {personal['current_country']}" if city else personal['current_country']
                summary_parts.append(f"📍 *Ubicación actual:* {location}")
            
            # Familia
            if family.get("family_status"):
                status_map = {
                    "single": "Soltero/a",
                    "married": "Casado/a",
                    "with_children": "Con hijos",
                    "with_family": "Con familia"
                }
                summary_parts.append(f"👨‍👩‍👧 *Familia:* {status_map.get(family['family_status'], family['family_status'])}")
                if family.get("count"):
                    summary_parts.append(f"   └ {family['count']} miembro(s)")
            
            # Trabajo
            if work.get("profession"):
                summary_parts.append(f"💼 *Profesión:* {work['profession']}")
            if work.get("experience_years"):
                summary_parts.append(f"   └ {work['experience_years']} años de experiencia")
            
            # Educación
            if education.get("level"):
                summary_parts.append(f"🎓 *Educación:* {education['level']}")
            
            # Finanzas
            if financial.get("savings"):
                summary_parts.append(f"💰 *Ahorros:* ${financial['savings']}")
            
            # Migración
            if migration.get("reason"):
                summary_parts.append(f"✈️ *Razón de migrar:* {migration['reason']}")
            if migration.get("timeline"):
                summary_parts.append(f"📅 *Plazo:* {migration['timeline']}")
            
            # Vida deseada
            if life_goals.get("dream"):
                summary_parts.append(f"\n🌟 *Tu sueño:* {life_goals['dream']}")
            
            summary_parts.append("\n\n*¿Es correcta esta información?*")
            
            buttons = [
                ("✅ Sí, todo correcto", "confirm_summary_yes"),
                ("✏️ Necesito corregir algo", "confirm_summary_no"),
                ("➕ Quiero agregar más", "confirm_summary_add")
            ]
        else:
            summary_parts = ["📋 *SUMMARY OF WHAT I UNDERSTOOD*\n"]
            
            if personal.get("name"):
                summary_parts.append(f"👤 *Name:* {personal['name']}")
            if personal.get("age"):
                summary_parts.append(f"🎂 *Age:* {personal['age']} years")
            if personal.get("nationality"):
                summary_parts.append(f"🌍 *Nationality:* {personal['nationality']}")
            if personal.get("current_country"):
                summary_parts.append(f"📍 *Current location:* {personal['current_country']}")
            
            if work.get("profession"):
                summary_parts.append(f"💼 *Profession:* {work['profession']}")
            
            if migration.get("reason"):
                summary_parts.append(f"✈️ *Reason to migrate:* {migration['reason']}")
            
            if life_goals.get("dream"):
                summary_parts.append(f"\n🌟 *Your dream:* {life_goals['dream']}")
            
            summary_parts.append("\n\n*Is this information correct?*")
            
            buttons = [
                ("✅ Yes, all correct", "confirm_summary_yes"),
                ("✏️ I need to correct something", "confirm_summary_no"),
                ("➕ I want to add more", "confirm_summary_add")
            ]
        
        return "\n".join(summary_parts), buttons
    
    @staticmethod
    def get_missing_info_prompt(validation: ProfileValidationResult, lang: str = "es") -> str:
        """Genera prompt para pedir información faltante"""
        if not validation.missing_required:
            return ""
        
        # Mapeo de campos a preguntas amigables
        field_questions = {
            "es": {
                "personal.name": "¿Cómo te llamas?",
                "personal.birth_date": "¿Cuál es tu fecha de nacimiento?",
                "personal.nationality": "¿De qué país eres?",
                "personal.current_country": "¿En qué país vives actualmente?",
                "family.family_status": "¿Viajas solo o con familia?",
                "family.count": "¿Cuántas personas viajan contigo?",
                "family.children_ages": "¿Qué edades tienen tus hijos?",
                "work.profession": "¿A qué te dedicas?",
                "work.experience_years": "¿Cuántos años de experiencia tienes?",
                "education.level": "¿Cuál es tu nivel de estudios?",
                "migration.reason": "¿Por qué quieres migrar?",
                "migration.timeline": "¿En cuánto tiempo planeas migrar?",
                "financial.savings": "¿Con cuánto dinero cuentas para el proceso?"
            },
            "en": {
                "personal.name": "What's your name?",
                "personal.birth_date": "What's your date of birth?",
                "personal.nationality": "What country are you from?",
                "personal.current_country": "What country do you currently live in?",
                "family.family_status": "Are you traveling alone or with family?",
                "family.count": "How many people are traveling with you?",
                "family.children_ages": "How old are your children?",
                "work.profession": "What do you do for work?",
                "work.experience_years": "How many years of experience do you have?",
                "education.level": "What's your education level?",
                "migration.reason": "Why do you want to migrate?",
                "migration.timeline": "When do you plan to migrate?",
                "financial.savings": "How much money do you have for the process?"
            }
        }
        
        questions = field_questions.get(lang, field_questions["es"])
        
        # Obtener la primera pregunta faltante
        for field in validation.missing_required:
            if field in questions:
                return questions[field]
        
        return questions.get(validation.missing_required[0], "Cuéntame más sobre ti.")


# ============== CORRECTION TRACKER ==============

class CorrectionTracker:
    """
    Detecta correcciones y bloquea avance de fase.
    Regla: Si el usuario corrige algo → no avanzar de fase.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._pending_corrections = {}
            cls._instance._correction_history = {}
        return cls._instance
    
    # Patrones para detectar correcciones
    CORRECTION_PATTERNS = [
        r"(?:no,?\s+)?(?:en realidad|actually)",
        r"(?:no,?\s+)?(?:quise decir|i meant)",
        r"(?:no,?\s+)?(?:me equivoqué|i was wrong)",
        r"(?:no,?\s+)?(?:corrijo|correction)",
        r"(?:no,?\s+)?(?:perdón|sorry),?\s+(?:es|it's)",
        r"(?:no,?\s+)?(?:no es|it's not)\s+",
        r"(?:no,?\s+)?(?:cambio|change)\s+",
        r"^no,?\s+(?:mi|my)\s+",
        # Patrones adicionales para correcciones explícitas
        r"(?:mi|my)\s+(?:\w+\s+)?(?:correcto|correct)\s+(?:es|is)",
        r"(?:el|la|the)\s+(?:correcto|correct)\s+(?:es|is)",
        r"(?:debería|should)\s+(?:ser|be)",
        r"(?:es|is)\s+(?:incorrecto|incorrect|wrong)",
    ]
    
    def detect_correction(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Detecta si el texto es una corrección.
        Returns: (is_correction, corrected_field)
        """
        text_lower = text.lower().strip()
        
        for pattern in self.CORRECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                # Intentar detectar qué campo se está corrigiendo
                field = self._detect_corrected_field(text_lower)
                return True, field
        
        return False, None
    
    def _detect_corrected_field(self, text: str) -> Optional[str]:
        """Detecta qué campo se está corrigiendo"""
        field_keywords = {
            "name": ["nombre", "name", "llamo", "call me"],
            "age": ["edad", "age", "años", "years old"],
            "profession": ["profesión", "profession", "trabajo", "work", "job"],
            "email": ["correo", "email", "mail"],
            "phone": ["teléfono", "phone", "número", "number"],
            "country": ["país", "country", "nacionalidad", "nationality"],
            "family": ["familia", "family", "hijos", "children", "esposo", "esposa"]
        }
        
        for field, keywords in field_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return field
        
        return None
    
    def register_correction(self, user_id: int, field: str, old_value: Any, new_value: Any):
        """Registra una corrección pendiente"""
        if user_id not in self._pending_corrections:
            self._pending_corrections[user_id] = []
        
        correction = {
            "timestamp": datetime.now().isoformat(),
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
            "confirmed": False
        }
        
        self._pending_corrections[user_id].append(correction)
        
        # Guardar en historial
        if user_id not in self._correction_history:
            self._correction_history[user_id] = []
        self._correction_history[user_id].append(correction)
    
    def has_pending_corrections(self, user_id: int) -> bool:
        """Verifica si hay correcciones pendientes de confirmar"""
        if user_id not in self._pending_corrections:
            return False
        return len([c for c in self._pending_corrections[user_id] if not c["confirmed"]]) > 0
    
    def confirm_corrections(self, user_id: int):
        """Confirma todas las correcciones pendientes"""
        if user_id in self._pending_corrections:
            for correction in self._pending_corrections[user_id]:
                correction["confirmed"] = True
    
    def can_advance_phase(self, user_id: int) -> Tuple[bool, str]:
        """
        Verifica si se puede avanzar de fase.
        Regla: Si hay correcciones pendientes, no avanzar.
        """
        if self.has_pending_corrections(user_id):
            return False, "Tienes correcciones pendientes. Confirma los cambios antes de continuar."
        return True, ""


# ============== LIFE GOAL EXTRACTOR ==============

class LifeGoalExtractor:
    """
    Extrae la vida deseada, no solo la visa.
    Regla: Prioridad: entender la vida deseada, no la visa.
    """
    
    # Preguntas para entender la vida deseada
    LIFE_GOAL_QUESTIONS = {
        "es": {
            "dream": "¿Cuál es tu sueño en Estados Unidos? ¿Cómo te imaginas tu vida allá?",
            "priorities": "¿Qué es más importante para ti: estabilidad económica, calidad de vida, o oportunidades para tu familia?",
            "lifestyle": "¿Prefieres una vida en ciudad grande con más oportunidades, o una ciudad más tranquila con mejor calidad de vida?",
            "work_life": "¿Quieres trabajar para una empresa, emprender tu propio negocio, o trabajar remoto?",
            "family_life": "¿Qué tipo de comunidad buscas para tu familia? ¿Es importante la comunidad latina?",
            "timeline": "¿Cuándo te gustaría estar establecido en USA? ¿Tienes alguna fecha límite?"
        },
        "en": {
            "dream": "What's your dream in the United States? How do you imagine your life there?",
            "priorities": "What's more important to you: economic stability, quality of life, or opportunities for your family?",
            "lifestyle": "Do you prefer life in a big city with more opportunities, or a quieter city with better quality of life?",
            "work_life": "Do you want to work for a company, start your own business, or work remotely?",
            "family_life": "What kind of community are you looking for your family? Is the Latino community important?",
            "timeline": "When would you like to be settled in the USA? Do you have any deadline?"
        }
    }
    
    @staticmethod
    def get_next_life_goal_question(user_data: Dict[str, Any], lang: str = "es") -> Optional[str]:
        """Obtiene la siguiente pregunta sobre vida deseada que no ha sido respondida"""
        life_goals = user_data.get("profile", {}).get("life_goals", {})
        preferences = user_data.get("profile", {}).get("preferences", {})
        
        questions = LifeGoalExtractor.LIFE_GOAL_QUESTIONS.get(lang, LifeGoalExtractor.LIFE_GOAL_QUESTIONS["es"])
        
        # Verificar qué preguntas ya fueron respondidas
        answered = set()
        if life_goals.get("dream"):
            answered.add("dream")
        if life_goals.get("priorities") or preferences.get("priorities"):
            answered.add("priorities")
        if preferences.get("city_size"):
            answered.add("lifestyle")
        if life_goals.get("work_preference"):
            answered.add("work_life")
        if preferences.get("community_importance"):
            answered.add("family_life")
        if user_data.get("profile", {}).get("migration", {}).get("timeline"):
            answered.add("timeline")
        
        # Retornar la primera pregunta no respondida
        priority_order = ["dream", "priorities", "work_life", "lifestyle", "family_life", "timeline"]
        for question_key in priority_order:
            if question_key not in answered:
                return questions.get(question_key)
        
        return None
    
    @staticmethod
    def extract_life_goals(text: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae metas de vida del texto"""
        extracted = {}
        text_lower = text.lower()
        
        # Detectar prioridades
        if any(word in text_lower for word in ["dinero", "money", "económic", "economic", "salario", "salary"]):
            extracted["priority_economic"] = True
        if any(word in text_lower for word in ["familia", "family", "hijos", "children", "seguridad", "safety"]):
            extracted["priority_family"] = True
        if any(word in text_lower for word in ["calidad", "quality", "tranquil", "peace", "vida", "life"]):
            extracted["priority_quality"] = True
        
        # Detectar preferencia de ciudad
        if any(word in text_lower for word in ["grande", "big", "metrópoli", "metropolis", "oportunidades"]):
            extracted["city_preference"] = "large"
        elif any(word in text_lower for word in ["pequeña", "small", "tranquila", "quiet", "pueblo"]):
            extracted["city_preference"] = "small"
        elif any(word in text_lower for word in ["mediana", "medium", "balance"]):
            extracted["city_preference"] = "medium"
        
        # Detectar preferencia de trabajo
        if any(word in text_lower for word in ["negocio", "business", "emprender", "entrepreneur"]):
            extracted["work_preference"] = "business"
        elif any(word in text_lower for word in ["remoto", "remote", "desde casa", "from home"]):
            extracted["work_preference"] = "remote"
        elif any(word in text_lower for word in ["empresa", "company", "empleado", "employee"]):
            extracted["work_preference"] = "employee"
        
        return extracted


# ============== DECISION GATE ==============

class DecisionGate:
    """
    Solo permite decisiones con perfil validado.
    Regla: La visa engine solo puede activarse con perfil completo validado.
    """
    
    @staticmethod
    def can_make_decision(user_data: Dict[str, Any], decision_type: str) -> Tuple[bool, str, Optional[str]]:
        """
        Verifica si se puede tomar una decisión.
        Returns: (can_decide, reason, next_action)
        """
        validation = ProfileValidator.validate(user_data)
        
        # Decisiones que requieren perfil completo
        high_stakes_decisions = ["visa_recommendation", "city_selection", "payment", "diagnosis"]
        
        if decision_type in high_stakes_decisions:
            if not validation.is_ready_for_visa:
                missing_prompt = UnderstandingSummarizer.get_missing_info_prompt(validation)
                return False, f"Necesito más información antes de {decision_type}.", missing_prompt
            
            # Verificar si el perfil está validado (confirmado)
            if validation.completeness != ProfileCompleteness.VALIDATED:
                return False, "Necesito que confirmes la información antes de continuar.", "show_summary"
        
        # Verificar correcciones pendientes
        tracker = CorrectionTracker()
        can_advance, correction_msg = tracker.can_advance_phase(user_data.get("user_id", 0))
        if not can_advance:
            return False, correction_msg, "confirm_corrections"
        
        return True, "", None
    
    @staticmethod
    def get_decision_requirements(decision_type: str, lang: str = "es") -> List[str]:
        """Obtiene los requisitos para tomar una decisión"""
        requirements = {
            "es": {
                "visa_recommendation": [
                    "Nombre completo",
                    "Edad/Fecha de nacimiento",
                    "Nacionalidad",
                    "Situación familiar",
                    "Profesión y experiencia",
                    "Razón de migración",
                    "Ahorros disponibles",
                    "Confirmación del resumen"
                ],
                "city_selection": [
                    "Preferencias de clima",
                    "Tamaño de ciudad preferido",
                    "Prioridades (costo, seguridad, etc.)",
                    "Presupuesto mensual"
                ],
                "payment": [
                    "Perfil completo validado",
                    "Entendimiento del servicio",
                    "Confirmación de precio"
                ]
            },
            "en": {
                "visa_recommendation": [
                    "Full name",
                    "Age/Date of birth",
                    "Nationality",
                    "Family situation",
                    "Profession and experience",
                    "Reason for migration",
                    "Available savings",
                    "Summary confirmation"
                ],
                "city_selection": [
                    "Climate preferences",
                    "Preferred city size",
                    "Priorities (cost, safety, etc.)",
                    "Monthly budget"
                ],
                "payment": [
                    "Validated complete profile",
                    "Understanding of service",
                    "Price confirmation"
                ]
            }
        }
        
        lang_reqs = requirements.get(lang, requirements["es"])
        return lang_reqs.get(decision_type, [])


# ============== SINGLETON GETTERS ==============

def get_data_memory() -> DataMemory:
    return DataMemory()

def get_profile_validator() -> ProfileValidator:
    return ProfileValidator()

def get_understanding_summarizer() -> UnderstandingSummarizer:
    return UnderstandingSummarizer()

def get_correction_tracker() -> CorrectionTracker:
    return CorrectionTracker()

def get_life_goal_extractor() -> LifeGoalExtractor:
    return LifeGoalExtractor()

def get_decision_gate() -> DecisionGate:
    return DecisionGate()


# ============== INTEGRATION HELPERS ==============

def store_user_input(user_id: int, text: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper para guardar input del usuario y extraer datos"""
    memory = get_data_memory()
    memory.store_raw_input(user_id, text)
    return memory.extract_and_store(user_id, text, user_data)

def validate_profile(user_data: Dict[str, Any]) -> ProfileValidationResult:
    """Helper para validar perfil"""
    return ProfileValidator.validate(user_data)

def generate_understanding_summary(user_data: Dict[str, Any], lang: str = "es") -> Tuple[str, List[Tuple[str, str]]]:
    """Helper para generar resumen de entendimiento"""
    return UnderstandingSummarizer.generate_summary(user_data, lang)

def detect_correction(text: str) -> Tuple[bool, Optional[str]]:
    """Helper para detectar correcciones"""
    tracker = get_correction_tracker()
    return tracker.detect_correction(text)

def can_make_decision(user_data: Dict[str, Any], decision_type: str) -> Tuple[bool, str, Optional[str]]:
    """Helper para verificar si se puede tomar decisión"""
    return DecisionGate.can_make_decision(user_data, decision_type)

def get_next_life_question(user_data: Dict[str, Any], lang: str = "es") -> Optional[str]:
    """Helper para obtener siguiente pregunta de vida deseada"""
    return LifeGoalExtractor.get_next_life_goal_question(user_data, lang)


# V4.2 FIX: Guard clause for profile minimum completion
def is_profile_min_complete(user_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Verifica si el perfil tiene los campos mínimos requeridos para transiciones.
    
    Campos mínimos requeridos:
    - name (nombre)
    - nationality (nacionalidad)
    - current_country (país actual)
    
    Returns:
        (is_complete, blocking_message)
    """
    profile = user_data.get("profile", {})
    personal = profile.get("personal", {})
    
    # Campos mínimos requeridos
    min_required = {
        "name": personal.get("name"),
        "nationality": personal.get("nationality"),
        "current_country": personal.get("current_country")
    }
    
    missing = [field for field, value in min_required.items() if not value]
    
    if missing:
        # Generar mensaje de bloqueo
        field_names_es = {
            "name": "nombre",
            "nationality": "nacionalidad",
            "current_country": "país actual"
        }
        missing_names = [field_names_es.get(f, f) for f in missing]
        blocking_msg = (
            f"🚫 Antes de continuar, necesito saber tu {', '.join(missing_names)}.\n\n"
            "Esto me ayuda a darte información personalizada."
        )
        return False, blocking_msg
    
    return True, ""
