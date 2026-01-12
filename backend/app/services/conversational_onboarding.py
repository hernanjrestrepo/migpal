#!/usr/bin/env python3
"""
MigPAL Conversational Onboarding v5.0
=====================================
FILOSOFÍA: Escuchar primero, preguntar después.

Este módulo reemplaza el onboarding rígido con una conversación natural:
- NO hay estados rígidos ni formularios
- El bot ESCUCHA lo que el usuario dice
- REFLEJA lo que entendió
- Pregunta UNA cosa natural a la vez
- Permite avanzar con información parcial
- NUNCA bloquea por falta de nombre/nacionalidad

Flujo Natural:
1. Usuario dice algo → Bot extrae info automáticamente
2. Bot refleja lo que entendió → "Entiendo que eres ingeniero..."
3. Bot pregunta UNA cosa que falta → "¿A qué país te gustaría ir?"
4. Repite hasta tener suficiente info para ayudar

NO HAY:
- Mensajes "⏳ Sigo aquí"
- Formularios con botones obligatorios
- Bloqueos por campos faltantes
- Estados rígidos tipo "name" → "birth_date" → "nationality"
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ============== CAMPOS DEL PERFIL ==============

@dataclass
class ProfileField:
    """Campo del perfil con su estado"""
    name: str
    value: Optional[str] = None
    confidence: float = 0.0
    source: str = ""  # "extracted", "asked", "inferred"
    
    @property
    def is_filled(self) -> bool:
        return self.value is not None and self.confidence >= 0.5


@dataclass
class UserProfile:
    """Perfil del usuario extraído de la conversación"""
    # Datos personales (opcionales para empezar)
    name: ProfileField = field(default_factory=lambda: ProfileField("name"))
    nationality: ProfileField = field(default_factory=lambda: ProfileField("nationality"))
    current_country: ProfileField = field(default_factory=lambda: ProfileField("current_country"))
    current_city: ProfileField = field(default_factory=lambda: ProfileField("current_city"))
    
    # Datos profesionales
    profession: ProfileField = field(default_factory=lambda: ProfileField("profession"))
    experience_years: ProfileField = field(default_factory=lambda: ProfileField("experience_years"))
    education_level: ProfileField = field(default_factory=lambda: ProfileField("education_level"))
    english_level: ProfileField = field(default_factory=lambda: ProfileField("english_level"))
    
    # Objetivos de migración
    destination_country: ProfileField = field(default_factory=lambda: ProfileField("destination_country"))
    migration_reason: ProfileField = field(default_factory=lambda: ProfileField("migration_reason"))
    timeline: ProfileField = field(default_factory=lambda: ProfileField("timeline"))
    budget: ProfileField = field(default_factory=lambda: ProfileField("budget"))
    
    # Familia
    has_family: ProfileField = field(default_factory=lambda: ProfileField("has_family"))
    travels_alone: ProfileField = field(default_factory=lambda: ProfileField("travels_alone"))
    family_size: ProfileField = field(default_factory=lambda: ProfileField("family_size"))
    
    def get_filled_count(self) -> int:
        """Cuenta campos llenos"""
        fields = [
            self.name, self.nationality, self.current_country, self.profession,
            self.experience_years, self.education_level, self.english_level,
            self.destination_country, self.migration_reason, self.timeline,
            self.budget, self.has_family
        ]
        return sum(1 for f in fields if f.is_filled)
    
    def get_completion_percentage(self) -> float:
        """Porcentaje de completitud"""
        total = 12  # Campos principales
        filled = self.get_filled_count()
        return (filled / total) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para guardar"""
        return {
            "personal": {
                "name": self.name.value,
                "nationality": self.nationality.value,
                "current_country": self.current_country.value,
                "current_city": self.current_city.value,
            },
            "work": {
                "profession": self.profession.value,
                "experience": self.experience_years.value,
            },
            "education": {
                "level": self.education_level.value,
            },
            "languages": {
                "english": self.english_level.value,
            },
            "preferences": {
                "destination": self.destination_country.value,
                "reason": self.migration_reason.value,
                "timeline": self.timeline.value,
                "budget": self.budget.value,
            },
            "family": {
                "has_family": self.has_family.value,
                "size": self.family_size.value,
            },
            "_meta": {
                "completion": self.get_completion_percentage(),
                "filled_count": self.get_filled_count(),
            }
        }


# ============== EXTRACTOR DE INFORMACIÓN ==============

class InfoExtractor:
    """Extrae información del texto del usuario de forma natural"""
    
    # Patrones para extraer información
    PATTERNS = {
        "profession": [
            r"soy\s+(ingenier[oa](?:\s+de\s+\w+)?|doctor[a]?|abogad[oa]|profesor[a]?|contador[a]?|enfermero[a]?|programador[a]?|diseñador[a]?|arquitect[oa]|médic[oa]|psicólog[oa]|economista|administrador[a]?|chef|cocinero[a]?|mecánic[oa]|electricista|plomero|carpintero|vendedor[a]?|gerente|director[a]?|analista|consultor[a]?)",
            r"trabajo\s+(?:como|de)\s+(\w+(?:\s+\w+)?)",
            r"mi\s+profesión\s+es\s+(\w+(?:\s+\w+)?)",
            r"i\s+am\s+(?:a|an)\s+(\w+(?:\s+\w+)?)",
            r"i\s+work\s+as\s+(?:a|an)?\s*(\w+(?:\s+\w+)?)",
        ],
        "experience_years": [
            r"(\d+)\s*(?:años?|years?)\s*(?:de\s+)?experiencia",
            r"experiencia\s+(?:de\s+)?(\d+)\s*(?:años?|years?)",
            r"(\d+)\s*(?:años?|years?)\s+(?:trabajando|working)",
        ],
        "destination_country": [
            # Patrones más amplios para detectar destino
            r"(?:quiero|deseo|me\s+gustaría|quisiera|voy)\s+(?:ir|irme|migrar|vivir|mudarme)\s+(?:a|en|para)\s+(estados\s+unidos|usa|eeuu|canadá|canada|españa|alemania|australia|reino\s+unido|uk|francia|italia|portugal|holanda|suiza|nueva\s+zelanda)",
            r"(?:irme|ir|migrar)\s+(?:a|para)\s+(estados\s+unidos|usa|eeuu|canadá|canada|españa|alemania|australia)",
            r"(?:mi\s+)?destino\s+(?:es|sería)\s+(estados\s+unidos|usa|eeuu|canadá|canada|españa|alemania|australia)",
            r"(?:to|in)\s+(usa|united\s+states|canada|spain|germany|australia|uk|france)",
            # Patrón simple: menciona el país directamente
            r"\b(estados\s+unidos|usa|eeuu|united\s+states)\b",
            r"\b(canadá|canada)\b",
            r"\b(españa|spain)\b",
            r"\b(alemania|germany)\b",
            r"\b(australia)\b",
        ],
        "english_level": [
            r"(?:mi\s+)?(?:nivel\s+de\s+)?inglés\s+(?:es\s+)?(?:nivel\s+)?(básico|intermedio|avanzado|nativo|fluido|b1|b2|c1|c2|a1|a2)",
            r"(?:hablo|tengo)\s+(?:un\s+)?inglés\s+(básico|intermedio|avanzado|fluido)",
            r"(?:my\s+)?english\s+(?:is\s+)?(basic|intermediate|advanced|native|fluent)",
            r"no\s+(?:hablo|sé)\s+(?:nada\s+de\s+)?inglés",
        ],
        "budget": [
            r"(?:tengo|cuento\s+con|mi\s+presupuesto\s+es)\s+(?:de\s+)?(?:unos?\s+)?(?:\$|usd|dólares?)?\s*(\d+(?:[,\.]\d+)?)\s*(?:mil|k|dólares?|usd)?",
            r"(?:\$|usd)\s*(\d+(?:[,\.]\d+)?)\s*(?:mil|k)?",
            r"(\d+(?:[,\.]\d+)?)\s*(?:mil|k)?\s*(?:dólares?|usd|euros?)",
        ],
        "timeline": [
            r"(?:quiero|planeo|pienso)\s+(?:irme|migrar|salir)\s+(?:en|dentro\s+de)\s+(\d+)\s*(meses?|años?|semanas?)",
            r"(?:en|dentro\s+de)\s+(\d+)\s*(meses?|años?)",
            r"(?:lo\s+más\s+)?pronto\s+posible|urgente|inmediato",
            r"(?:el\s+)?(?:próximo|siguiente)\s+(año|mes|semestre)",
            r"(?:este|próximo)\s+(año|mes|semestre)",
            r"el\s+(año|mes)\s+que\s+viene",
            r"para\s+(?:el\s+)?(\d{4})",  # para 2025
            r"en\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)",
        ],
        "nationality": [
            r"soy\s+(colombian[oa]|mexican[oa]|venezolan[oa]|argentin[oa]|chilen[oa]|peruan[oa]|ecuatorian[oa]|bolivian[oa]|uruguayo[a]|paraguayo[a]|brasileñ[oa]|cuban[oa]|dominican[oa]|puertorriqueñ[oa]|guatemaltec[oa]|hondureñ[oa]|salvadoreñ[oa]|nicaragüense|costarricens[ea]|panameñ[oa]|español[a]?)",
            r"(?:de|from)\s+(colombia|méxico|mexico|venezuela|argentina|chile|perú|peru|ecuador|bolivia|uruguay|paraguay|brasil|brazil|cuba|república\s+dominicana|puerto\s+rico|guatemala|honduras|el\s+salvador|nicaragua|costa\s+rica|panamá|españa|spain)",
            r"nacionalidad\s+(colombiana|mexicana|venezolana|argentina|chilena|peruana|ecuatoriana)",
        ],
        "current_country": [
            r"(?:vivo|estoy|resido)\s+(?:en|actualmente\s+en)\s+(colombia|méxico|mexico|venezuela|argentina|chile|perú|peru|ecuador|bolivia|uruguay|paraguay|brasil|brazil|cuba|estados\s+unidos|usa|españa|alemania)",
            r"(?:actualmente\s+)?(?:en|from)\s+(colombia|mexico|venezuela|argentina|chile|peru|ecuador|usa|spain|germany)",
        ],
        "education_level": [
            r"(?:soy|tengo)\s+(?:título\s+de\s+)?(licenciado|ingeniero|doctor|magíster|maestría|doctorado|técnico|bachiller|profesional)",
            r"(?:estudié|terminé|tengo)\s+(?:la\s+)?(universidad|carrera|maestría|doctorado|técnico|bachillerato)",
            r"(?:i\s+have\s+a\s+)?(bachelor|master|phd|doctorate|degree)",
            r"título\s+(?:universitario|profesional)\s+en\s+\w+",
            r"graduado\s+(?:de|en)\s+\w+",
            r"licenciatura\s+en\s+\w+",
            r"(?:ing\.|ingeniero|ingeniería)\s+en\s+\w+",
        ],
        "migration_reason": [
            r"(?:quiero\s+migrar\s+)?(?:por|para)\s+(trabajo|estudios|familia|seguridad|calidad\s+de\s+vida|oportunidades|mejor\s+futuro)",
            r"(?:busco|necesito)\s+(trabajo|estudiar|reunirme\s+con\s+mi\s+familia|seguridad|mejor\s+vida)",
        ],
        "has_family": [
            r"(?:viajo|voy|me\s+voy)\s+con\s+(?:mi\s+)?(familia|esposa|esposo|hijos|pareja)",
            r"(?:tengo|somos)\s+(\d+)\s+(?:hijos?|personas?|familia)",
        ],
        "travels_alone": [
            r"(?:viajo|voy)\s+solo",
            r"(?:soy\s+)?soltero",
            r"sin\s+familia",
            r"no\s+tengo\s+(?:familia|hijos|pareja)",
        ],
        "name": [
            # Solo extraer nombre cuando hay señal clara de que es un nombre
            r"(?:me\s+llamo|mi\s+nombre\s+es)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)",
            r"(?:my\s+name\s+is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            # NO usar "soy" solo porque puede ser "soy ingeniero"
        ],
    }
    
    # Normalización de países
    COUNTRY_NORMALIZE = {
        "estados unidos": "USA",
        "usa": "USA",
        "eeuu": "USA",
        "united states": "USA",
        "canadá": "Canadá",
        "canada": "Canadá",
        "españa": "España",
        "spain": "España",
        "alemania": "Alemania",
        "germany": "Alemania",
        "australia": "Australia",
        "reino unido": "Reino Unido",
        "uk": "Reino Unido",
        "francia": "Francia",
        "france": "Francia",
        "italia": "Italia",
        "italy": "Italia",
        "portugal": "Portugal",
        "holanda": "Holanda",
        "netherlands": "Holanda",
        "suiza": "Suiza",
        "switzerland": "Suiza",
        "nueva zelanda": "Nueva Zelanda",
        "new zealand": "Nueva Zelanda",
    }
    
    @classmethod
    def extract_all(cls, text: str) -> Dict[str, Tuple[str, float]]:
        """
        Extrae toda la información posible del texto.
        Returns: Dict[field_name, (value, confidence)]
        """
        text_lower = text.lower().strip()
        extracted = {}
        
        for field_name, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
                    value = value.strip()
                    
                    # Normalizar países
                    if field_name in ["destination_country", "current_country", "nationality"]:
                        value = cls.COUNTRY_NORMALIZE.get(value.lower(), value.title())
                    
                    # Normalizar niveles de inglés
                    if field_name == "english_level":
                        value = cls._normalize_english_level(value)

                    # Normalizar timeline
                    if field_name == "timeline":
                        value = cls._normalize_timeline(value)

                    # Calcular confianza basada en el patrón
                    confidence = 0.8 if len(match.group(0)) > 10 else 0.6
                    
                    extracted[field_name] = (value, confidence)
                    break  # Solo tomar la primera coincidencia
        
        return extracted
    
    @classmethod
    def _normalize_english_level(cls, value: str) -> str:
        """Normaliza el nivel de inglés"""
        value_lower = value.lower()
        if value_lower in ["básico", "basic", "a1", "a2"]:
            return "Básico"
        elif value_lower in ["intermedio", "intermediate", "b1", "b2"]:
            return "Intermedio"
        elif value_lower in ["avanzado", "advanced", "c1"]:
            return "Avanzado"
        elif value_lower in ["nativo", "native", "fluido", "fluent", "c2"]:
            return "Nativo/Fluido"
        return value.title()

    @classmethod
    def _normalize_timeline(cls, value: str) -> str:
        """Normaliza el timeline"""
        value_lower = value.lower()
        if value_lower in ["año", "ano"]:
            return "próximo año"
        elif value_lower in ["mes"]:
            return "próximo mes"
        elif value_lower in ["semestre"]:
            return "próximo semestre"
        elif "pronto" in value_lower or "urgente" in value_lower:
            return "lo antes posible"
        # Si es un mes específico
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                 "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        for mes in meses:
            if mes in value_lower:
                return f"en {mes}"
        return value


# ============== GENERADOR DE PREGUNTAS ==============

class QuestionGenerator:
    """Genera la siguiente pregunta natural basada en lo que falta"""
    
    # Preguntas por campo (ordenadas por prioridad)
    QUESTIONS = {
        "es": {
            "destination_country": [
                "¿A qué país te gustaría migrar? 🌍",
                "¿Tienes algún país en mente para tu migración?",
                "¿Cuál es tu destino soñado?",
            ],
            "profession": [
                "¿A qué te dedicas actualmente? 💼",
                "Cuéntame, ¿cuál es tu profesión?",
                "¿En qué área trabajas?",
            ],
            "experience_years": [
                "¿Cuántos años de experiencia tienes en tu campo?",
                "¿Cuánto tiempo llevas trabajando en eso?",
            ],
            "english_level": [
                "¿Cómo está tu inglés? 🌐",
                "¿Qué nivel de inglés tienes?",
                "¿Hablas inglés?",
            ],
            "education_level": [
                "¿Cuál es tu nivel de estudios? 🎓",
                "¿Tienes título universitario o técnico?",
            ],
            "budget": [
                "¿Con cuánto presupuesto cuentas para el proceso? 💰",
                "¿Tienes ahorros para la migración?",
            ],
            "timeline": [
                "¿Para cuándo te gustaría migrar? ⏰",
                "¿Tienes una fecha en mente?",
            ],
            "migration_reason": [
                "¿Qué te motiva a migrar? 💭",
                "¿Por qué quieres dar este paso?",
            ],
            "has_family": [
                "¿Viajarías solo o con familia? 👨‍👩‍👧",
                "¿Tienes familia que migre contigo?",
            ],
            "nationality": [
                "¿De qué país eres originalmente?",
                "¿Cuál es tu nacionalidad?",
            ],
            "current_country": [
                "¿Dónde vives actualmente?",
                "¿En qué país estás ahora?",
            ],
            "name": [
                "Por cierto, ¿cómo te llamas? 😊",
                "¿Cuál es tu nombre?",
            ],
        },
        "en": {
            "destination_country": [
                "Which country would you like to migrate to? 🌍",
                "Do you have a destination in mind?",
            ],
            "profession": [
                "What do you do for work? 💼",
                "What's your profession?",
            ],
            "experience_years": [
                "How many years of experience do you have?",
            ],
            "english_level": [
                "How's your English? 🌐",
                "What's your English level?",
            ],
            "education_level": [
                "What's your education level? 🎓",
            ],
            "budget": [
                "What's your budget for the process? 💰",
            ],
            "timeline": [
                "When would you like to migrate? ⏰",
            ],
            "migration_reason": [
                "What motivates you to migrate? 💭",
            ],
            "has_family": [
                "Would you travel alone or with family? 👨‍👩‍👧",
            ],
            "nationality": [
                "What's your nationality?",
            ],
            "current_country": [
                "Where do you currently live?",
            ],
            "name": [
                "By the way, what's your name? 😊",
            ],
        }
    }
    
    # Prioridad de campos (qué preguntar primero)
    PRIORITY = [
        "destination_country",  # Lo más importante: ¿a dónde quiere ir?
        "profession",           # ¿Qué hace? (determina opciones de visa)
        "experience_years",     # ¿Cuánta experiencia?
        "english_level",        # Crítico para muchos países
        "education_level",      # Nivel de estudios
        "budget",               # Presupuesto disponible
        "timeline",             # ¿Para cuándo?
        "migration_reason",     # Motivación
        "has_family",           # ¿Viaja con familia?
        # Estos son menos prioritarios - se pueden inferir o preguntar después
        "nationality",
        "current_country",
        "name",                 # El nombre es lo MENOS importante para empezar
    ]
    
    @classmethod
    def get_next_question(cls, profile: UserProfile, lang: str = "es") -> Optional[Tuple[str, str]]:
        """
        Obtiene la siguiente pregunta natural basada en lo que falta.
        Returns: (field_name, question) o None si el perfil está completo
        """
        import random
        
        questions = cls.QUESTIONS.get(lang, cls.QUESTIONS["es"])
        
        # Revisar campos en orden de prioridad
        for field_name in cls.PRIORITY:
            field = getattr(profile, field_name, None)
            if field and not field.is_filled:
                field_questions = questions.get(field_name, [])
                if field_questions:
                    return (field_name, random.choice(field_questions))
        
        return None  # Perfil suficientemente completo


# ============== GENERADOR DE REFLEXIONES ==============

class ReflectionGenerator:
    """Genera reflexiones empáticas sobre lo que el usuario dijo"""
    
    TEMPLATES = {
        "es": {
            "profession": [
                "¡Interesante! Como {value}, tienes un perfil que puede ser muy atractivo para varios países. 💼",
                "Ser {value} te abre varias puertas. Hay buena demanda en el mercado internacional. 👍",
            ],
            "destination_country": [
                "¡{value}! Es un destino muy popular. Hay varias opciones de visa que podemos explorar. 🌍",
                "Entiendo que te interesa {value}. Es una excelente elección con muchas oportunidades. ✨",
            ],
            "experience_years": [
                "Con {value} años de experiencia, tu perfil es bastante competitivo. 📈",
                "{value} años de experiencia es muy valioso para los procesos migratorios. 💪",
            ],
            "english_level": [
                "Tu nivel de inglés {value} es un punto a tu favor. 🌐",
                "Con inglés {value}, tienes más opciones disponibles. 👍",
            ],
            "budget": [
                "Con un presupuesto de {value}, podemos trabajar con varias opciones. 💰",
            ],
            "timeline": [
                "Entiendo que quieres migrar {value}. Vamos a planificar bien. ⏰",
            ],
            "migration_reason": [
                "Migrar por {value} es una razón muy válida. Muchos lo hacen por lo mismo. 💭",
            ],
            "has_family": [
                "Migrar con familia requiere planificación adicional, pero es muy factible. 👨‍👩‍👧",
            ],
            "travels_alone": [
                "Viajar solo tiene sus ventajas: más flexibilidad y menos trámites. 💪",
                "Migrar solo puede ser más ágil. Tienes más opciones disponibles. 🚀",
            ],
            "name": [
                "¡Mucho gusto, {value}! 😊",
                "¡Hola {value}! Encantado de conocerte. 👋",
            ],
            "nationality": [
                "Siendo de {value}, hay programas específicos que podemos revisar. 🌎",
            ],
            "education_level": [
                "Con nivel {value}, tu perfil académico es sólido. 🎓",
            ],
        },
        "en": {
            "profession": [
                "Interesting! As a {value}, you have a profile that can be very attractive to several countries. 💼",
            ],
            "destination_country": [
                "{value}! It's a very popular destination. There are several visa options we can explore. 🌍",
            ],
            "experience_years": [
                "With {value} years of experience, your profile is quite competitive. 📈",
            ],
            "english_level": [
                "Your {value} English level is a plus. 🌐",
            ],
            "name": [
                "Nice to meet you, {value}! 😊",
            ],
        }
    }
    
    @classmethod
    def generate_reflection(cls, field_name: str, value: str, lang: str = "es") -> Optional[str]:
        """Genera una reflexión empática sobre la información extraída"""
        import random
        
        templates = cls.TEMPLATES.get(lang, cls.TEMPLATES["es"])
        field_templates = templates.get(field_name, [])
        
        if field_templates:
            template = random.choice(field_templates)
            return template.format(value=value)
        
        return None


# ============== MOTOR CONVERSACIONAL ==============

class ConversationalEngine:
    """Motor principal del onboarding conversacional"""
    
    def __init__(self):
        self.extractor = InfoExtractor()
        self.question_gen = QuestionGenerator()
        self.reflection_gen = ReflectionGenerator()

    def _is_user_question(self, text: str) -> bool:
        """Detecta si el mensaje del usuario es una pregunta que requiere respuesta"""
        text_lower = text.lower().strip()

        # Patrones de preguntas comunes
        question_patterns = [
            r'¿.*\?',  # Cualquier cosa entre ¿ y ?
            r'.*\?$',   # Termina en ?
            r'^(qué|que|cuál|cual|cómo|como|cuándo|cuando|dónde|donde|quién|quien|por qué|porque)\s+',
            r'^(what|which|how|when|where|who|why)\s+',
            r'(opciones?|alternativas?|posibilidades?|caminos?)\s+(tengo|hay|existen|tiene)',
            r'(puedo|podría|debo|debería)\s+',
            r'(recomiendas|sugieres|aconsejas)',
            r'(ayuda|ayúdame|explica|explícame)',
            r'(visa|visas)\s+(tengo|hay|existen|para)',
            r'(requisitos?|documentos?|papeles?)\s+(necesito|requiero|piden)',
            r'(cuánto|cuanto)\s+(cuesta|vale|necesito|tiempo|demora)',
        ]

        for pattern in question_patterns:
            if re.search(pattern, text_lower):
                return True

        return False
    
    def process_message(self, text: str, user_data: Dict[str, Any], lang: str = "es") -> Tuple[str, Dict[str, Any]]:
        """
        Procesa un mensaje del usuario y genera una respuesta conversacional.

        Returns:
            Tuple[response_text, updated_user_data]
        """
        # 1. Detectar si es una pregunta que requiere respuesta de IA
        is_question = self._is_user_question(text)

        # 2. Extraer información del mensaje
        extracted = self.extractor.extract_all(text)

        # 3. Actualizar el perfil del usuario
        profile = self._get_or_create_profile(user_data)
        reflections = []

        for field_name, (value, confidence) in extracted.items():
            field = getattr(profile, field_name, None)
            if field and not field.is_filled:
                field.value = value
                field.confidence = confidence
                field.source = "extracted"

                # Generar reflexión para este campo
                reflection = self.reflection_gen.generate_reflection(field_name, value, lang)
                if reflection:
                    reflections.append(reflection)

                logger.info(f"📝 EXTRACTED | field={field_name} | value={value} | confidence={confidence}")

        # 4. Guardar perfil actualizado
        user_data["conversational_profile"] = profile.to_dict()

        # 5. Si es una pregunta del usuario, marcar que necesita respuesta de IA
        if is_question and profile.get_completion_percentage() >= 30:  # Solo si tenemos algo de contexto
            # Marcar que es una pregunta que necesita IA
            user_data["pending_ai_question"] = text
            user_data["has_reflections"] = len(reflections) > 0
            if reflections:
                user_data["pending_reflections"] = reflections

            # Por ahora, responder que estamos procesando la pregunta
            processing_msg = (
                "Déjame pensar en tu pregunta... 🤔"
                if lang == "es" else
                "Let me think about your question... 🤔"
            )

            # Si hay reflexiones, incluirlas
            if reflections:
                response = reflections[0] + "\n\n" + processing_msg
            else:
                response = processing_msg

            return response, user_data

        # 6. Flujo normal: generar respuesta con reflexiones y preguntas
        response_parts = []

        # Agregar reflexiones (máximo 2 para no abrumar)
        if reflections:
            response_parts.extend(reflections[:2])

        # 7. Obtener siguiente pregunta
        next_q = self.question_gen.get_next_question(profile, lang)

        if next_q:
            field_name, question = next_q
            response_parts.append(f"\n{question}")
        else:
            # Perfil suficientemente completo
            completion = profile.get_completion_percentage()
            if completion >= 50:
                summary = self._generate_summary(profile, lang)
                response_parts.append(f"\n{summary}")

                # Si el perfil está bastante completo, agregar recomendaciones
                if completion >= 60:
                    recommendations = VisaRecommendationEngine.generate_recommendations(profile, lang)
                    if recommendations:
                        response_parts.append(f"\n{recommendations}")

        # Si no hay reflexiones ni pregunta, dar respuesta genérica empática
        if not response_parts:
            response_parts.append(
                "Entiendo. Cuéntame más sobre tu situación y lo que buscas. 💭"
                if lang == "es" else
                "I understand. Tell me more about your situation and what you're looking for. 💭"
            )

        response = "\n\n".join(response_parts)

        return response, user_data
    
    def get_welcome_message(self, lang: str = "es") -> str:
        """Mensaje de bienvenida conversacional"""
        if lang == "es":
            return (
                "¡Hola! 👋 Soy MigPAL, tu consultor de migración.\n\n"
                "Estoy aquí para ayudarte a encontrar el mejor camino para tu proceso migratorio. "
                "Cuéntame, ¿qué te trae por aquí hoy? 💭"
            )
        else:
            return (
                "Hi! 👋 I'm MigPAL, your migration consultant.\n\n"
                "I'm here to help you find the best path for your migration process. "
                "Tell me, what brings you here today? 💭"
            )
    
    def _get_or_create_profile(self, user_data: Dict[str, Any]) -> UserProfile:
        """Obtiene o crea el perfil conversacional"""
        profile = UserProfile()
        
        # Cargar datos existentes si hay
        existing = user_data.get("conversational_profile", {})
        if existing:
            personal = existing.get("personal", {})
            work = existing.get("work", {})
            education = existing.get("education", {})
            languages = existing.get("languages", {})
            preferences = existing.get("preferences", {})
            family = existing.get("family", {})
            
            if personal.get("name"):
                profile.name.value = personal["name"]
                profile.name.confidence = 0.9
            if personal.get("nationality"):
                profile.nationality.value = personal["nationality"]
                profile.nationality.confidence = 0.9
            if personal.get("current_country"):
                profile.current_country.value = personal["current_country"]
                profile.current_country.confidence = 0.9
            
            if work.get("profession"):
                profile.profession.value = work["profession"]
                profile.profession.confidence = 0.9
            if work.get("experience"):
                profile.experience_years.value = work["experience"]
                profile.experience_years.confidence = 0.9
            
            if education.get("level"):
                profile.education_level.value = education["level"]
                profile.education_level.confidence = 0.9
            
            if languages.get("english"):
                profile.english_level.value = languages["english"]
                profile.english_level.confidence = 0.9
            
            if preferences.get("destination"):
                profile.destination_country.value = preferences["destination"]
                profile.destination_country.confidence = 0.9
            if preferences.get("reason"):
                profile.migration_reason.value = preferences["reason"]
                profile.migration_reason.confidence = 0.9
            if preferences.get("timeline"):
                profile.timeline.value = preferences["timeline"]
                profile.timeline.confidence = 0.9
            if preferences.get("budget"):
                profile.budget.value = preferences["budget"]
                profile.budget.confidence = 0.9
            
            if family.get("has_family"):
                profile.has_family.value = family["has_family"]
                profile.has_family.confidence = 0.9
        
        # También cargar del perfil tradicional si existe
        old_profile = user_data.get("profile", {})
        if old_profile:
            personal = old_profile.get("personal", {})
            work = old_profile.get("work", {})
            
            if personal.get("name") and not profile.name.is_filled:
                profile.name.value = personal["name"]
                profile.name.confidence = 0.9
            if personal.get("nationality") and not profile.nationality.is_filled:
                profile.nationality.value = personal["nationality"]
                profile.nationality.confidence = 0.9
            if work.get("profession") and not profile.profession.is_filled:
                profile.profession.value = work["profession"]
                profile.profession.confidence = 0.9
        
        return profile
    
    def _generate_summary(self, profile: UserProfile, lang: str = "es") -> str:
        """Genera un resumen del perfil para confirmar"""
        parts = []

        if lang == "es":
            parts.append("📋 *Perfil capturado hasta ahora:*\n")

            # Datos personales
            if profile.name.is_filled or profile.nationality.is_filled or profile.current_country.is_filled:
                parts.append("👤 *Datos Personales*")
                if profile.name.is_filled:
                    parts.append(f"   • Nombre: {profile.name.value}")
                if profile.nationality.is_filled:
                    parts.append(f"   • Nacionalidad: {profile.nationality.value}")
                if profile.current_country.is_filled:
                    parts.append(f"   • País actual: {profile.current_country.value}")
                if profile.current_city.is_filled:
                    parts.append(f"   • Ciudad: {profile.current_city.value}")
                parts.append("")

            # Perfil profesional
            if profile.profession.is_filled or profile.experience_years.is_filled or profile.education_level.is_filled:
                parts.append("💼 *Perfil Profesional*")
                if profile.profession.is_filled:
                    parts.append(f"   • Profesión: {profile.profession.value}")
                if profile.experience_years.is_filled:
                    parts.append(f"   • Experiencia: {profile.experience_years.value} años")
                if profile.education_level.is_filled:
                    parts.append(f"   • Educación: {profile.education_level.value}")
                if profile.english_level.is_filled:
                    parts.append(f"   • Inglés: {profile.english_level.value}")
                parts.append("")

            # Plan migratorio
            if profile.destination_country.is_filled or profile.timeline.is_filled or profile.budget.is_filled:
                parts.append("🎯 *Plan Migratorio*")
                if profile.destination_country.is_filled:
                    parts.append(f"   • Destino: {profile.destination_country.value}")
                if profile.timeline.is_filled:
                    parts.append(f"   • Cuándo: {profile.timeline.value}")
                if profile.budget.is_filled:
                    parts.append(f"   • Presupuesto: ${profile.budget.value}")
                if profile.migration_reason.is_filled:
                    parts.append(f"   • Motivo: {profile.migration_reason.value}")
                parts.append("")

            # Estado familiar
            if profile.has_family.is_filled or profile.travels_alone.is_filled:
                parts.append("👨‍👩‍👧 *Situación Familiar*")
                if profile.travels_alone.is_filled and profile.travels_alone.value:
                    parts.append(f"   • Viaja solo")
                elif profile.has_family.is_filled:
                    parts.append(f"   • Viaja con familia")
                    if profile.family_size.is_filled:
                        parts.append(f"   • Tamaño familia: {profile.family_size.value}")
                parts.append("")

            completion = profile.get_completion_percentage()
            parts.append(f"📊 *Completitud del perfil: {completion:.0f}%*")

            if completion >= 70:
                parts.append("\n✅ *Tu perfil está bastante completo.*")
                parts.append("Basado en esta información, puedo darte recomendaciones específicas de visa.")
                parts.append("\n¿Todo correcto? ¿O hay algo que quieras corregir o agregar? 🤔")
            else:
                parts.append(f"\n💡 *Necesito un poco más de información para darte las mejores recomendaciones.*")
                parts.append("\n¿Es correcto lo que tengo hasta ahora? 😊")

        else:  # English
            parts.append("📋 *Profile captured so far:*\n")

            # Personal data
            if profile.name.is_filled or profile.nationality.is_filled or profile.current_country.is_filled:
                parts.append("👤 *Personal Information*")
                if profile.name.is_filled:
                    parts.append(f"   • Name: {profile.name.value}")
                if profile.nationality.is_filled:
                    parts.append(f"   • Nationality: {profile.nationality.value}")
                if profile.current_country.is_filled:
                    parts.append(f"   • Current country: {profile.current_country.value}")
                parts.append("")

            # Professional profile
            if profile.profession.is_filled or profile.experience_years.is_filled:
                parts.append("💼 *Professional Profile*")
                if profile.profession.is_filled:
                    parts.append(f"   • Profession: {profile.profession.value}")
                if profile.experience_years.is_filled:
                    parts.append(f"   • Experience: {profile.experience_years.value} years")
                if profile.education_level.is_filled:
                    parts.append(f"   • Education: {profile.education_level.value}")
                if profile.english_level.is_filled:
                    parts.append(f"   • English: {profile.english_level.value}")
                parts.append("")

            # Migration plan
            if profile.destination_country.is_filled or profile.timeline.is_filled:
                parts.append("🎯 *Migration Plan*")
                if profile.destination_country.is_filled:
                    parts.append(f"   • Destination: {profile.destination_country.value}")
                if profile.timeline.is_filled:
                    parts.append(f"   • When: {profile.timeline.value}")
                if profile.budget.is_filled:
                    parts.append(f"   • Budget: ${profile.budget.value}")
                parts.append("")

            completion = profile.get_completion_percentage()
            parts.append(f"📊 *Profile completion: {completion:.0f}%*")

            if completion >= 70:
                parts.append("\n✅ *Your profile is quite complete.*")
                parts.append("Based on this information, I can give you specific visa recommendations.")
                parts.append("\n Is everything correct? Or is there something you'd like to fix or add? 🤔")
            else:
                parts.append(f"\n💡 *I need a bit more information to give you the best recommendations.*")
                parts.append("\nIs what I have so far correct? 😊")

        return "\n".join(parts)


# ============== GENERADOR DE RECOMENDACIONES ==============

class VisaRecommendationEngine:
    """Genera recomendaciones de visa basadas en el perfil"""

    @classmethod
    def generate_recommendations(cls, profile: UserProfile, lang: str = "es") -> Optional[str]:
        """Genera recomendaciones de visa si el perfil está suficientemente completo"""
        if profile.get_completion_percentage() < 50:
            return None

        recommendations = []

        # Para USA con perfil de ingeniero de software
        if profile.destination_country.value == "USA" and profile.profession.value and "ingenier" in profile.profession.value.lower():
            if lang == "es":
                recommendations.append("🎯 *Opciones de visa para ti:*\n")

                # H-1B
                if profile.experience_years.value and int(profile.experience_years.value.split()[0]) >= 3:
                    recommendations.append("**1. Visa H-1B (Trabajo especializado)**")
                    recommendations.append("   ✅ Tu perfil califica: Ingeniero con experiencia")
                    recommendations.append("   💼 Necesitas: Empleador que te patrocine")
                    recommendations.append("   ⏱️ Tiempo: 6-12 meses")
                    recommendations.append("   💰 Costo estimado: $5,000-$10,000\n")

                # O-1
                if profile.experience_years.value and int(profile.experience_years.value.split()[0]) >= 5:
                    recommendations.append("**2. Visa O-1 (Habilidades extraordinarias)**")
                    recommendations.append("   ✅ Posible con tu experiencia de 5+ años")
                    recommendations.append("   📋 Necesitas: Demostrar logros destacados")
                    recommendations.append("   ⏱️ Tiempo: 2-6 meses")
                    recommendations.append("   💰 Costo estimado: $5,000-$8,000\n")

                # L-1
                recommendations.append("**3. Visa L-1 (Transferencia corporativa)**")
                recommendations.append("   ✅ Si trabajas en empresa multinacional")
                recommendations.append("   🏢 Necesitas: 1 año en la empresa")
                recommendations.append("   ⏱️ Tiempo: 2-4 meses")
                recommendations.append("   💰 Costo estimado: $3,000-$5,000\n")

                # EB-2 NIW
                if profile.budget.value:
                    try:
                        # Convertir el presupuesto a número
                        budget_str = str(profile.budget.value).replace(",", "").replace("$", "")
                        if "k" in budget_str.lower():
                            budget = int(float(budget_str.lower().replace("k", "")) * 1000)
                        elif "mil" in budget_str.lower():
                            budget = int(float(budget_str.lower().replace("mil", "")) * 1000)
                        else:
                            # Si es solo un número, asumimos que está en miles
                            budget = int(float(budget_str)) * 1000

                        if budget >= 15000:
                            recommendations.append("**4. EB-2 NIW (Green Card - Interés Nacional)**")
                            recommendations.append("   ✅ Tu presupuesto lo permite")
                            recommendations.append("   🎓 Ideal para ingenieros con impacto")
                            recommendations.append("   ⏱️ Tiempo: 12-24 meses")
                            recommendations.append("   💰 Costo estimado: $10,000-$15,000\n")
                    except:
                        pass  # Si no se puede convertir el presupuesto, simplemente omitir EB-2

                recommendations.append("💡 *Siguiente paso recomendado:*")
                recommendations.append("Buscar empleadores que patrocinen H-1B en tu área")

            else:  # English
                recommendations.append("🎯 *Visa options for you:*\n")

                # H-1B
                if profile.experience_years.value and int(profile.experience_years.value.split()[0]) >= 3:
                    recommendations.append("**1. H-1B Visa (Specialty Occupation)**")
                    recommendations.append("   ✅ You qualify: Engineer with experience")
                    recommendations.append("   💼 Need: Employer sponsorship")
                    recommendations.append("   ⏱️ Timeline: 6-12 months")
                    recommendations.append("   💰 Estimated cost: $5,000-$10,000\n")

        # Para otros países o perfiles
        elif profile.destination_country.value and profile.profession.value:
            if lang == "es":
                recommendations.append("🎯 *Basado en tu perfil, estas son tus opciones:*\n")
                recommendations.append(f"Para {profile.destination_country.value} como {profile.profession.value}:")
                recommendations.append("• Visa de trabajo calificado")
                recommendations.append("• Programas de nominación")
                recommendations.append("• Visa de emprendedor (si aplica)")
                recommendations.append("\n💡 ¿Te gustaría explorar alguna opción en particular?")
            else:
                recommendations.append("🎯 *Based on your profile, these are your options:*\n")
                recommendations.append(f"For {profile.destination_country.value} as {profile.profession.value}:")
                recommendations.append("• Skilled worker visa")
                recommendations.append("• Nomination programs")
                recommendations.append("• Entrepreneur visa (if applicable)")
                recommendations.append("\n💡 Would you like to explore any particular option?")

        return "\n".join(recommendations) if recommendations else None


# ============== SINGLETON ==============

_engine = None
_recommendation_engine = None

def get_conversational_engine() -> ConversationalEngine:
    """Obtiene la instancia del motor conversacional"""
    global _engine
    if _engine is None:
        _engine = ConversationalEngine()
    return _engine

def get_recommendation_engine() -> VisaRecommendationEngine:
    """Obtiene la instancia del motor de recomendaciones"""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = VisaRecommendationEngine()
    return _recommendation_engine


# ============== FUNCIONES DE CONVENIENCIA ==============

def process_conversational_message(text: str, user_data: Dict[str, Any], lang: str = "es") -> Tuple[str, Dict[str, Any]]:
    """Procesa un mensaje de forma conversacional"""
    engine = get_conversational_engine()
    return engine.process_message(text, user_data, lang)

def get_conversational_welcome(lang: str = "es") -> str:
    """Obtiene el mensaje de bienvenida conversacional"""
    engine = get_conversational_engine()
    return engine.get_welcome_message(lang)

def is_profile_sufficient(user_data: Dict[str, Any]) -> bool:
    """Verifica si el perfil tiene suficiente información para dar recomendaciones"""
    profile_data = user_data.get("conversational_profile", {})
    meta = profile_data.get("_meta", {})
    completion = meta.get("completion", 0)
    return completion >= 40  # 40% es suficiente para empezar a dar recomendaciones
