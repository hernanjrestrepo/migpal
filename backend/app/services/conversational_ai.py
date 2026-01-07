#!/usr/bin/env python3
"""
MigPAL Conversational AI v3.0.8
===============================
MigPAL es el AMIGO de los migrantes, no un formulario estúpido.

Principios:
1. TODO es conversacional - los formularios son solo ayuda opcional
2. Si el usuario escribe texto libre, la IA debe ENTENDER y AYUDAR
3. Nunca mostrar "error" - siempre responder con empatía e inteligencia
4. La IA es el cerebro, no el código con opciones

Cuando el usuario dice:
- "no estoy listo para escoger" → Entender y ofrecer ayuda
- "no conozco Estados Unidos" → Explicar y guiar
- Cualquier texto libre → Procesar con IA y continuar la conversación
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class UserIntent(Enum):
    """Intenciones del usuario detectadas por IA"""
    NEEDS_HELP = "needs_help"           # Necesita ayuda/orientación
    NOT_READY = "not_ready"             # No está listo para decidir
    CONFUSED = "confused"               # Está confundido
    WANTS_INFO = "wants_info"           # Quiere más información
    ASKING_QUESTION = "asking_question" # Hace una pregunta
    EXPRESSING_CONCERN = "concern"      # Expresa preocupación
    READY_TO_CONTINUE = "ready"         # Listo para continuar
    CORRECTION = "correction"           # Quiere corregir algo
    OFF_TOPIC = "off_topic"             # Tema no relacionado
    PROVIDING_INFO = "providing_info"   # Dando información (nombre, profesión, etc)
    UNKNOWN = "unknown"                 # No se pudo determinar


@dataclass
class ConversationalResponse:
    """Respuesta conversacional de la IA"""
    message: str
    follow_up_question: Optional[str] = None
    suggested_actions: List[Tuple[str, str]] = None  # [(texto, callback)]
    should_advance_state: bool = False
    new_state: Optional[str] = None
    extracted_data: Dict[str, Any] = None


class ConversationalAI:
    """
    IA Conversacional para MigPAL.
    El cerebro que entiende al usuario y responde con inteligencia.
    """
    
    # Patrones para detectar intenciones
    INTENT_PATTERNS = {
        UserIntent.NOT_READY: [
            r"no estoy listo",
            r"no estoy seguro",
            r"no sé",
            r"no se",
            r"todavía no",
            r"aún no",
            r"not ready",
            r"not sure",
            r"don't know",
            r"i don't know",
        ],
        UserIntent.CONFUSED: [
            r"no entiendo",
            r"no comprendo",
            r"confundido",
            r"confusa",
            r"qué significa",
            r"que significa",
            r"no conozco",
            r"don't understand",
            r"confused",
            r"what does.*mean",
        ],
        UserIntent.WANTS_INFO: [
            r"cuéntame más",
            r"cuentame mas",
            r"más información",
            r"mas informacion",
            r"explícame",
            r"explicame",
            r"qué es",
            r"que es",
            r"cómo funciona",
            r"como funciona",
            r"tell me more",
            r"more info",
            r"explain",
            r"how does.*work",
        ],
        UserIntent.ASKING_QUESTION: [
            r"\?$",
            r"^qué ",
            r"^que ",
            r"^cómo ",
            r"^como ",
            r"^cuál ",
            r"^cual ",
            r"^dónde ",
            r"^donde ",
            r"^cuánto ",
            r"^cuanto ",
            r"^por qué ",
            r"^por que ",
            r"^what ",
            r"^how ",
            r"^where ",
            r"^when ",
            r"^why ",
            r"^which ",
        ],
        UserIntent.EXPRESSING_CONCERN: [
            r"me preocupa",
            r"tengo miedo",
            r"me da miedo",
            r"estoy nervioso",
            r"estoy nerviosa",
            r"worried",
            r"scared",
            r"afraid",
            r"nervous",
            r"anxious",
        ],
        UserIntent.NEEDS_HELP: [
            r"ayúdame",
            r"ayudame",
            r"necesito ayuda",
            r"no sé qué hacer",
            r"no se que hacer",
            r"help me",
            r"need help",
            r"i need",
        ],
        UserIntent.CORRECTION: [
            r"corrijo",
            r"corrección",
            r"correccion",
            r"me equivoqué",
            r"me equivoque",
            r"quise decir",
            r"en realidad",
            r"correction",
            r"i meant",
            r"actually",
        ],
    }
    
    # Respuestas empáticas por intención
    EMPATHIC_RESPONSES = {
        "es": {
            UserIntent.NOT_READY: (
                "Entiendo perfectamente, {name}. No hay prisa. 🤝\n\n"
                "Tomar decisiones sobre migración es algo grande y es completamente "
                "normal necesitar tiempo para pensar.\n\n"
                "{context_help}\n\n"
                "¿Qué te ayudaría a sentirte más preparado/a?"
            ),
            UserIntent.CONFUSED: (
                "No te preocupes, {name}. Es normal tener dudas. 💭\n\n"
                "{context_explanation}\n\n"
                "¿Hay algo específico que te gustaría que te explique mejor?"
            ),
            UserIntent.WANTS_INFO: (
                "¡Claro! Con gusto te cuento más. 📚\n\n"
                "{context_info}\n\n"
                "¿Qué más te gustaría saber?"
            ),
            UserIntent.ASKING_QUESTION: (
                "{ai_response}\n\n"
                "¿Eso responde tu pregunta? ¿Hay algo más que quieras saber?"
            ),
            UserIntent.EXPRESSING_CONCERN: (
                "Entiendo tu preocupación, {name}. Es completamente válido sentirse así. 💙\n\n"
                "{context_reassurance}\n\n"
                "Estoy aquí para ayudarte a navegar esto paso a paso. "
                "¿Qué es lo que más te preocupa?"
            ),
            UserIntent.NEEDS_HELP: (
                "¡Aquí estoy para ayudarte, {name}! 🌟\n\n"
                "{context_help}\n\n"
                "Cuéntame más sobre lo que necesitas."
            ),
        },
        "en": {
            UserIntent.NOT_READY: (
                "I completely understand, {name}. There's no rush. 🤝\n\n"
                "Making decisions about migration is a big deal and it's completely "
                "normal to need time to think.\n\n"
                "{context_help}\n\n"
                "What would help you feel more prepared?"
            ),
            UserIntent.CONFUSED: (
                "Don't worry, {name}. It's normal to have questions. 💭\n\n"
                "{context_explanation}\n\n"
                "Is there something specific you'd like me to explain better?"
            ),
            UserIntent.WANTS_INFO: (
                "Of course! I'm happy to tell you more. 📚\n\n"
                "{context_info}\n\n"
                "What else would you like to know?"
            ),
            UserIntent.ASKING_QUESTION: (
                "{ai_response}\n\n"
                "Does that answer your question? Is there anything else you'd like to know?"
            ),
            UserIntent.EXPRESSING_CONCERN: (
                "I understand your concern, {name}. It's completely valid to feel that way. 💙\n\n"
                "{context_reassurance}\n\n"
                "I'm here to help you navigate this step by step. "
                "What worries you the most?"
            ),
            UserIntent.NEEDS_HELP: (
                "I'm here to help you, {name}! 🌟\n\n"
                "{context_help}\n\n"
                "Tell me more about what you need."
            ),
        }
    }
    
    # Información contextual por tema
    CONTEXT_INFO = {
        "es": {
            "regions": (
                "Estados Unidos tiene 4 regiones principales:\n\n"
                "☀️ **Sur** (Florida, Texas, Georgia): Clima cálido, gran comunidad latina, "
                "costo de vida moderado.\n\n"
                "🌃 **Noreste** (New York, New Jersey): Muchas oportunidades, ciudades grandes, "
                "pero costo de vida alto.\n\n"
                "🌲 **Oeste** (California, Washington): Hub tecnológico, clima agradable, "
                "pero muy caro.\n\n"
                "🌾 **Medio Oeste** (Illinois, Ohio): Más económico, buenas oportunidades, "
                "inviernos fríos.\n\n"
                "Si me cuentas qué es importante para ti (clima, costo, trabajo, familia), "
                "puedo ayudarte a encontrar la mejor opción."
            ),
            "visas": (
                "Hay varios tipos de visas según tu situación:\n\n"
                "💼 **Trabajo**: H-1B (profesionales), L-1 (transferencia), O-1 (talentos)\n"
                "👨‍👩‍👧 **Familia**: Petición familiar, visa de prometido\n"
                "🎓 **Estudios**: F-1 (estudiante), J-1 (intercambio)\n"
                "🏢 **Negocios**: E-2 (inversionista), EB-5 (inversión grande)\n\n"
                "La mejor visa depende de tu perfil. Cuéntame más sobre tu situación "
                "y te ayudo a identificar las mejores opciones."
            ),
            "process": (
                "El proceso de migración generalmente incluye:\n\n"
                "1️⃣ **Evaluación**: Entender tu situación y opciones\n"
                "2️⃣ **Planificación**: Definir la mejor ruta migratoria\n"
                "3️⃣ **Documentación**: Preparar todos los papeles\n"
                "4️⃣ **Aplicación**: Enviar la solicitud\n"
                "5️⃣ **Seguimiento**: Monitorear el proceso\n\n"
                "Yo te acompaño en cada paso. No tienes que hacerlo solo/a."
            ),
            "costs": (
                "Los costos varían mucho según el tipo de visa y tu situación:\n\n"
                "📋 **Tarifas gubernamentales**: $200 - $2,000+\n"
                "👨‍⚖️ **Abogado** (opcional pero recomendado): $2,000 - $10,000+\n"
                "📄 **Documentos y traducciones**: $200 - $1,000\n"
                "✈️ **Viaje y establecimiento**: Variable\n\n"
                "Puedo ayudarte a calcular un presupuesto más específico "
                "basado en tu situación."
            ),
        },
        "en": {
            "regions": (
                "The United States has 4 main regions:\n\n"
                "☀️ **South** (Florida, Texas, Georgia): Warm weather, large Latino community, "
                "moderate cost of living.\n\n"
                "🌃 **Northeast** (New York, New Jersey): Many opportunities, big cities, "
                "but high cost of living.\n\n"
                "🌲 **West** (California, Washington): Tech hub, nice weather, "
                "but very expensive.\n\n"
                "🌾 **Midwest** (Illinois, Ohio): More affordable, good opportunities, "
                "cold winters.\n\n"
                "If you tell me what's important to you (weather, cost, work, family), "
                "I can help you find the best option."
            ),
            "visas": (
                "There are several types of visas depending on your situation:\n\n"
                "💼 **Work**: H-1B (professionals), L-1 (transfer), O-1 (talents)\n"
                "👨‍👩‍👧 **Family**: Family petition, fiancé visa\n"
                "🎓 **Studies**: F-1 (student), J-1 (exchange)\n"
                "🏢 **Business**: E-2 (investor), EB-5 (large investment)\n\n"
                "The best visa depends on your profile. Tell me more about your situation "
                "and I'll help you identify the best options."
            ),
            "process": (
                "The migration process generally includes:\n\n"
                "1️⃣ **Evaluation**: Understanding your situation and options\n"
                "2️⃣ **Planning**: Defining the best migration route\n"
                "3️⃣ **Documentation**: Preparing all the paperwork\n"
                "4️⃣ **Application**: Submitting the request\n"
                "5️⃣ **Follow-up**: Monitoring the process\n\n"
                "I'll accompany you every step of the way. You don't have to do it alone."
            ),
            "costs": (
                "Costs vary a lot depending on the type of visa and your situation:\n\n"
                "📋 **Government fees**: $200 - $2,000+\n"
                "👨‍⚖️ **Lawyer** (optional but recommended): $2,000 - $10,000+\n"
                "📄 **Documents and translations**: $200 - $1,000\n"
                "✈️ **Travel and settlement**: Variable\n\n"
                "I can help you calculate a more specific budget "
                "based on your situation."
            ),
        }
    }
    
    def __init__(self):
        self.ai_client = None  # Se inicializa con el cliente de IA
    
    def detect_intent(self, text: str) -> UserIntent:
        """Detectar la intención del usuario"""
        text_lower = text.lower().strip()
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent
        
        # Si tiene signo de pregunta, probablemente es una pregunta
        if "?" in text:
            return UserIntent.ASKING_QUESTION
        
        # Si parece estar dando información (nombre, profesión, números)
        if self._looks_like_info(text):
            return UserIntent.PROVIDING_INFO
        
        return UserIntent.UNKNOWN
    
    def _looks_like_info(self, text: str) -> bool:
        """Detectar si el texto parece información del usuario"""
        # Patrones que indican que está dando información
        info_patterns = [
            r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+",  # Nombre Apellido
            r"\d+\s*(años?|years?)",  # X años
            r"\$?\d{1,3}[,.]?\d{3}",  # Cantidades de dinero
            r"ingeniero|doctor|abogado|contador|profesor|diseñador|programador",  # Profesiones
            r"soy\s+\w+",  # "Soy X"
            r"trabajo\s+(como|en|de)",  # "Trabajo como/en/de"
            r"tengo\s+\d+",  # "Tengo X"
            r"gano\s+",  # "Gano X"
            r"mi\s+(nombre|profesión|trabajo|salario)",  # "Mi nombre/profesión es"
        ]
        
        text_lower = text.lower()
        for pattern in info_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    def extract_data(self, text: str, current_state: str) -> Dict[str, Any]:
        """Extraer datos del texto libre del usuario"""
        extracted = {}
        text_lower = text.lower()
        
        # Extraer nombre (si parece un nombre)
        # Patrón 1: Solo nombre y apellido
        name_match = re.match(r"^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+)$", text.strip())
        if name_match:
            extracted["name"] = name_match.group(1)
        else:
            # Patrón 2: "mi nombre es X" o "me llamo X" o "soy X"
            name_patterns = [
                r"(?:mi nombre(?:\s+correcto)?\s+es|me llamo|soy)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)",
                r"(?:my name is|i'm|i am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            ]
            for pattern in name_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    potential_name = match.group(1)
                    # Verificar que no sea una profesión
                    professions = ["ingeniero", "doctor", "abogado", "contador", "profesor", "diseñador", "programador"]
                    if potential_name.lower() not in professions:
                        # Capitalizar correctamente
                        name_parts = potential_name.split()
                        extracted["name"] = " ".join(p.capitalize() for p in name_parts)
                    break
        
        # Extraer profesión
        profession_patterns = [
            r"soy\s+(ingeniero|doctor|abogado|contador|profesor|diseñador|programador|desarrollador)[^.]*",
            r"(ingeniero|doctor|abogado|contador|profesor|diseñador|programador|desarrollador)\s+de\s+\w+",
            r"trabajo\s+como\s+(\w+(?:\s+\w+)?)",
        ]
        for pattern in profession_patterns:
            match = re.search(pattern, text_lower)
            if match:
                extracted["profession"] = match.group(0).strip()
                break
        
        # Extraer años de experiencia
        exp_match = re.search(r"(\d+)\s*años?\s*(de\s+experiencia)", text_lower)
        if exp_match:
            extracted["experience_years"] = int(exp_match.group(1))
        
        # Extraer salario (solo si tiene indicador de dinero)
        salary_match = re.search(r"(gano|salario|sueldo)[^\d]*\$?([\d,]+)", text_lower)
        if salary_match:
            salary_str = salary_match.group(2).replace(",", "")
            try:
                extracted["salary"] = int(salary_str)
            except:
                pass
        else:
            # Buscar patrón con $ explícito
            salary_match2 = re.search(r"\$([\d,]+)\s*(usd|dólares|dolares|mensuales?)?", text_lower)
            if salary_match2 and "ahorr" not in text_lower:  # No confundir con ahorros
                salary_str = salary_match2.group(1).replace(",", "")
                try:
                    val = int(salary_str)
                    if val > 100:  # Salarios son > 100
                        extracted["salary"] = val
                except:
                    pass
        
        # Extraer ahorros
        savings_match = re.search(r"(ahorr[oa]d?[oa]?s?|tengo)\s*[^\d]*\$?([\d,]+)", text_lower)
        if savings_match:
            savings_str = savings_match.group(2).replace(",", "")
            try:
                extracted["savings"] = int(savings_str)
            except:
                pass
        
        # Extraer motivación
        motivation_keywords = {
            "trabajo": "work",
            "trabajar": "work",
            "oportunidades": "work",
            "empleo": "work",
            "laboral": "work",
            "familia": "family",
            "hijos": "family",
            "esposa": "family",
            "esposo": "family",
            "padres": "family",
            "educación": "education",
            "estudiar": "education",
            "universidad": "education",
            "seguridad": "safety",
            "violencia": "safety",
            "peligro": "safety",
            "calidad de vida": "quality",
            "mejor vida": "quality",
            "futuro": "quality",
        }
        for keyword, motivation in motivation_keywords.items():
            if keyword in text_lower:
                extracted["motivation"] = motivation
                break
        
        return extracted
    
    def detect_topic(self, text: str, current_state: str) -> str:
        """Detectar el tema de la conversación"""
        text_lower = text.lower()
        
        # Detectar por palabras clave
        if any(w in text_lower for w in ["región", "region", "estado", "state", "zona", "área", "area", "ciudad", "city"]):
            return "regions"
        if any(w in text_lower for w in ["visa", "permiso", "permit", "documento", "document"]):
            return "visas"
        if any(w in text_lower for w in ["proceso", "process", "paso", "step", "cómo", "how"]):
            return "process"
        if any(w in text_lower for w in ["costo", "cost", "precio", "price", "dinero", "money", "cuánto", "how much"]):
            return "costs"
        
        # Detectar por estado actual
        state_topics = {
            "location_region": "regions",
            "location_state": "regions",
            "location_city": "regions",
            "visa_analysis": "visas",
            "visa_recommendation": "visas",
        }
        
        return state_topics.get(current_state, "process")
    
    async def process_free_text(
        self,
        text: str,
        user: Dict[str, Any],
        current_state: str,
        lang: str = "es"
    ) -> ConversationalResponse:
        """
        Procesar texto libre del usuario con inteligencia.
        NUNCA devolver error - siempre responder con empatía.
        """
        name = user.get("profile", {}).get("personal", {}).get("name", "amigo/a")
        intent = self.detect_intent(text)
        topic = self.detect_topic(text, current_state)
        
        # Extraer datos del texto
        extracted_data = self.extract_data(text, current_state)
        
        logger.info(f"🧠 AI Processing | user={user.get('telegram_id')} | intent={intent.value} | topic={topic} | extracted={extracted_data}")
        
        # Obtener información contextual
        context_info = self.CONTEXT_INFO.get(lang, self.CONTEXT_INFO["es"]).get(topic, "")
        
        # Si el usuario está dando información, procesarla y confirmar
        if intent == UserIntent.PROVIDING_INFO and extracted_data:
            return await self._handle_providing_info(name, text, extracted_data, lang, user)
        
        # Construir respuesta según intención
        if intent == UserIntent.NOT_READY:
            return await self._handle_not_ready(name, text, topic, context_info, lang, current_state)
        
        elif intent == UserIntent.CONFUSED:
            return await self._handle_confused(name, text, topic, context_info, lang)
        
        elif intent == UserIntent.WANTS_INFO:
            return await self._handle_wants_info(name, text, topic, context_info, lang)
        
        elif intent == UserIntent.ASKING_QUESTION:
            return await self._handle_question(name, text, topic, context_info, lang, user)
        
        elif intent == UserIntent.EXPRESSING_CONCERN:
            return await self._handle_concern(name, text, topic, context_info, lang)
        
        elif intent == UserIntent.NEEDS_HELP:
            return await self._handle_needs_help(name, text, topic, context_info, lang)
        
        else:
            # Intención desconocida - intentar extraer datos de todas formas
            if extracted_data:
                return await self._handle_providing_info(name, text, extracted_data, lang, user)
            # Si no hay datos, usar respuesta genérica amigable
            return await self._handle_unknown(name, text, topic, context_info, lang, user)
    
    async def _handle_providing_info(
        self, name: str, text: str, extracted_data: Dict[str, Any], lang: str, user: Dict
    ) -> ConversationalResponse:
        """Manejar cuando el usuario da información"""
        
        confirmations = []
        follow_up = None
        
        if lang == "es":
            # Confirmar datos extraídos
            if "name" in extracted_data:
                new_name = extracted_data["name"]
                confirmations.append(f"¡Mucho gusto, {new_name}! 😊")
                name = new_name
            
            if "profession" in extracted_data:
                confirmations.append(f"¡Excelente! Eres {extracted_data['profession']}. 💼")
            
            if "experience_years" in extracted_data:
                years = extracted_data["experience_years"]
                confirmations.append(f"Con {years} años de experiencia, tienes un perfil muy sólido. 💪")
            
            if "salary" in extracted_data:
                salary = extracted_data["salary"]
                confirmations.append(f"Entendido, tu salario actual es ${salary:,}. 💰")
            
            if "savings" in extracted_data:
                savings = extracted_data["savings"]
                confirmations.append(f"Tienes ${savings:,} en ahorros. ¡Eso es un buen comienzo! 🎯")
            
            if "motivation" in extracted_data:
                motivation_texts = {
                    "work": "Buscar mejores oportunidades laborales es una razón muy válida.",
                    "family": "Reunirte con tu familia es algo muy especial.",
                    "education": "La educación es una inversión increíble.",
                    "safety": "La seguridad es fundamental.",
                    "quality": "Buscar mejor calidad de vida es completamente válido.",
                }
                mot = extracted_data["motivation"]
                confirmations.append(motivation_texts.get(mot, "Entiendo tu motivación."))
            
            # Determinar siguiente pregunta
            if not confirmations:
                confirmations.append(f"Gracias por compartir eso, {name}. 😊")
            
            # Construir mensaje
            message = "\n\n".join(confirmations)
            
            # Determinar qué preguntar a continuación
            profile = user.get("profile", {})
            personal = profile.get("personal", {})
            professional = profile.get("professional", {})
            
            # Si acabamos de recibir el nombre, no preguntar nombre de nuevo
            has_name = personal.get("name") or "name" in extracted_data
            has_motivation = extracted_data.get("motivation")
            has_profession = professional.get("profession") or "profession" in extracted_data
            has_experience = "experience_years" in extracted_data
            
            if not has_name:
                follow_up = "¿Cómo te llamas?"
            elif not has_motivation:
                follow_up = "Cuéntame, ¿qué te motiva a considerar migrar?"
            elif not has_profession:
                follow_up = "¿A qué te dedicas profesionalmente?"
            elif not has_experience:
                follow_up = "¿Cuántos años de experiencia tienes en tu campo?"
            else:
                follow_up = "¡Excelente! Ya tengo una buena idea de tu perfil. ¿Te gustaría que exploremos opciones de destino?"
            
            message += f"\n\n{follow_up}"
            
        else:
            # English version
            if "name" in extracted_data:
                new_name = extracted_data["name"]
                confirmations.append(f"Nice to meet you, {new_name}! 😊")
                name = new_name
            
            if "profession" in extracted_data:
                confirmations.append(f"Great! You're a {extracted_data['profession']}. 💼")
            
            if "experience_years" in extracted_data:
                years = extracted_data["experience_years"]
                confirmations.append(f"With {years} years of experience, you have a solid profile. 💪")
            
            if not confirmations:
                confirmations.append(f"Thanks for sharing that, {name}. 😊")
            
            message = "\n\n".join(confirmations)
            follow_up = "Is there anything else you'd like to tell me about your situation?"
            message += f"\n\n{follow_up}"
        
        return ConversationalResponse(
            message=message,
            extracted_data=extracted_data,
            should_advance_state=False  # No avanzar automáticamente, seguir conversando
        )
    
    async def _handle_not_ready(
        self, name: str, text: str, topic: str, context_info: str, lang: str, current_state: str
    ) -> ConversationalResponse:
        """Manejar cuando el usuario no está listo"""
        
        # Respuesta empática
        if lang == "es":
            message = (
                f"Entiendo perfectamente, {name}. No hay ninguna prisa. 🤝\n\n"
                f"Tomar decisiones sobre migración es algo importante y es completamente "
                f"normal necesitar tiempo para pensar.\n\n"
            )
            
            if topic == "regions":
                message += (
                    "Si no conoces bien Estados Unidos, puedo ayudarte a entender "
                    "las diferentes regiones y qué ofrece cada una.\n\n"
                    f"{context_info}\n\n"
                    "¿Te gustaría que te cuente más sobre alguna región en particular, "
                    "o prefieres que te ayude a identificar qué es más importante para ti?"
                )
                actions = [
                    ("📚 Cuéntame más sobre las regiones", "ai_explain_regions"),
                    ("🎯 Ayúdame a decidir qué es importante", "ai_help_priorities"),
                    ("⏰ Prefiero pensarlo después", "ai_later"),
                ]
            else:
                message += (
                    "Estoy aquí cuando estés listo/a. Mientras tanto, "
                    "¿hay algo que te gustaría saber o alguna duda que pueda aclararte?"
                )
                actions = [
                    ("❓ Tengo preguntas", "ai_questions"),
                    ("📚 Quiero aprender más", "ai_learn_more"),
                    ("⏰ Vuelvo después", "ai_later"),
                ]
        else:
            message = (
                f"I completely understand, {name}. There's no rush at all. 🤝\n\n"
                f"Making decisions about migration is important and it's completely "
                f"normal to need time to think.\n\n"
            )
            
            if topic == "regions":
                message += (
                    "If you're not familiar with the United States, I can help you understand "
                    "the different regions and what each one offers.\n\n"
                    f"{context_info}\n\n"
                    "Would you like me to tell you more about a particular region, "
                    "or would you prefer help identifying what's most important to you?"
                )
                actions = [
                    ("📚 Tell me more about regions", "ai_explain_regions"),
                    ("🎯 Help me decide priorities", "ai_help_priorities"),
                    ("⏰ I'll think about it later", "ai_later"),
                ]
            else:
                message += (
                    "I'm here when you're ready. In the meantime, "
                    "is there anything you'd like to know or any questions I can answer?"
                )
                actions = [
                    ("❓ I have questions", "ai_questions"),
                    ("📚 I want to learn more", "ai_learn_more"),
                    ("⏰ I'll come back later", "ai_later"),
                ]
        
        return ConversationalResponse(
            message=message,
            suggested_actions=actions,
            should_advance_state=False
        )
    
    async def _handle_confused(
        self, name: str, text: str, topic: str, context_info: str, lang: str
    ) -> ConversationalResponse:
        """Manejar cuando el usuario está confundido"""
        
        if lang == "es":
            message = (
                f"No te preocupes, {name}. Es completamente normal tener dudas. 💭\n\n"
                f"Déjame explicarte mejor:\n\n"
                f"{context_info}\n\n"
                "¿Hay algo específico que te gustaría que te explique con más detalle?"
            )
            actions = [
                ("✅ Ahora entiendo mejor", "ai_understood"),
                ("🔄 Explícame de otra forma", "ai_explain_different"),
                ("❓ Tengo más preguntas", "ai_more_questions"),
            ]
        else:
            message = (
                f"Don't worry, {name}. It's completely normal to have questions. 💭\n\n"
                f"Let me explain better:\n\n"
                f"{context_info}\n\n"
                "Is there something specific you'd like me to explain in more detail?"
            )
            actions = [
                ("✅ I understand better now", "ai_understood"),
                ("🔄 Explain it differently", "ai_explain_different"),
                ("❓ I have more questions", "ai_more_questions"),
            ]
        
        return ConversationalResponse(
            message=message,
            suggested_actions=actions,
            should_advance_state=False
        )
    
    async def _handle_wants_info(
        self, name: str, text: str, topic: str, context_info: str, lang: str
    ) -> ConversationalResponse:
        """Manejar cuando el usuario quiere más información"""
        
        if lang == "es":
            message = (
                f"¡Con gusto, {name}! 📚\n\n"
                f"{context_info}\n\n"
                "¿Qué más te gustaría saber?"
            )
        else:
            message = (
                f"Of course, {name}! 📚\n\n"
                f"{context_info}\n\n"
                "What else would you like to know?"
            )
        
        return ConversationalResponse(
            message=message,
            should_advance_state=False
        )
    
    async def _handle_question(
        self, name: str, text: str, topic: str, context_info: str, lang: str, user: Dict
    ) -> ConversationalResponse:
        """Manejar preguntas del usuario usando IA"""
        
        # Usar IA para responder la pregunta
        try:
            from app.services.ai_chat import chat_with_ai
            
            context = f"""
            Usuario: {name}
            Tema actual: {topic}
            Pregunta: {text}
            
            Información de contexto:
            {context_info}
            
            Responde de forma amigable, empática y útil. 
            Eres MigPAL, el amigo de los migrantes.
            """
            
            ai_response = await chat_with_ai(
                message=text,
                context={"profile": user.get("profile", {}), "topic": topic}
            )
            
            response_text = ai_response.get("response", context_info)
            
        except Exception as e:
            logger.warning(f"AI chat error: {e}")
            response_text = context_info
        
        if lang == "es":
            message = (
                f"{response_text}\n\n"
                "¿Eso responde tu pregunta? ¿Hay algo más que quieras saber?"
            )
        else:
            message = (
                f"{response_text}\n\n"
                "Does that answer your question? Is there anything else you'd like to know?"
            )
        
        return ConversationalResponse(
            message=message,
            should_advance_state=False
        )
    
    async def _handle_concern(
        self, name: str, text: str, topic: str, context_info: str, lang: str
    ) -> ConversationalResponse:
        """Manejar preocupaciones del usuario"""
        
        if lang == "es":
            message = (
                f"Entiendo tu preocupación, {name}. Es completamente válido sentirse así. 💙\n\n"
                "Migrar es una decisión grande y es normal tener miedos o dudas.\n\n"
                "Lo importante es que no estás solo/a en esto. "
                "Estoy aquí para ayudarte a navegar cada paso.\n\n"
                "¿Qué es lo que más te preocupa? Cuéntame y veamos cómo podemos abordarlo juntos."
            )
        else:
            message = (
                f"I understand your concern, {name}. It's completely valid to feel that way. 💙\n\n"
                "Migrating is a big decision and it's normal to have fears or doubts.\n\n"
                "The important thing is that you're not alone in this. "
                "I'm here to help you navigate every step.\n\n"
                "What worries you the most? Tell me and let's see how we can address it together."
            )
        
        return ConversationalResponse(
            message=message,
            should_advance_state=False
        )
    
    async def _handle_needs_help(
        self, name: str, text: str, topic: str, context_info: str, lang: str
    ) -> ConversationalResponse:
        """Manejar cuando el usuario necesita ayuda"""
        
        if lang == "es":
            message = (
                f"¡Aquí estoy para ayudarte, {name}! 🌟\n\n"
                "Cuéntame más sobre lo que necesitas. Puedo ayudarte con:\n\n"
                "🗺️ Entender las opciones de destino\n"
                "📋 Conocer los tipos de visa\n"
                "💰 Calcular costos aproximados\n"
                "📝 Preparar documentos\n"
                "❓ Responder cualquier pregunta\n\n"
                "¿Por dónde te gustaría empezar?"
            )
            actions = [
                ("🗺️ Opciones de destino", "ai_destinations"),
                ("📋 Tipos de visa", "ai_visas"),
                ("💰 Costos", "ai_costs"),
                ("❓ Tengo una pregunta", "ai_question"),
            ]
        else:
            message = (
                f"I'm here to help you, {name}! 🌟\n\n"
                "Tell me more about what you need. I can help you with:\n\n"
                "🗺️ Understanding destination options\n"
                "📋 Learning about visa types\n"
                "💰 Calculating approximate costs\n"
                "📝 Preparing documents\n"
                "❓ Answering any questions\n\n"
                "Where would you like to start?"
            )
            actions = [
                ("🗺️ Destination options", "ai_destinations"),
                ("📋 Visa types", "ai_visas"),
                ("💰 Costs", "ai_costs"),
                ("❓ I have a question", "ai_question"),
            ]
        
        return ConversationalResponse(
            message=message,
            suggested_actions=actions,
            should_advance_state=False
        )
    
    async def _handle_unknown(
        self, name: str, text: str, topic: str, context_info: str, lang: str, user: Dict
    ) -> ConversationalResponse:
        """Manejar intención desconocida - usar IA"""
        
        # Intentar usar IA para entender y responder
        try:
            from app.services.ai_chat import chat_with_ai
            
            ai_response = await chat_with_ai(
                message=text,
                context={"profile": user.get("profile", {}), "topic": topic}
            )
            
            response_text = ai_response.get("response", "")
            
            if response_text:
                return ConversationalResponse(
                    message=response_text,
                    should_advance_state=False
                )
        except Exception as e:
            logger.warning(f"AI chat error: {e}")
        
        # Fallback amigable
        if lang == "es":
            message = (
                f"Gracias por compartir eso, {name}. 😊\n\n"
                "¿Podrías contarme un poco más sobre lo que necesitas? "
                "Estoy aquí para ayudarte con cualquier duda sobre migración."
            )
        else:
            message = (
                f"Thanks for sharing that, {name}. 😊\n\n"
                "Could you tell me a bit more about what you need? "
                "I'm here to help you with any questions about migration."
            )
        
        return ConversationalResponse(
            message=message,
            should_advance_state=False
        )


# Singleton
_conversational_ai = None

def get_conversational_ai() -> ConversationalAI:
    """Obtener instancia de la IA conversacional"""
    global _conversational_ai
    if _conversational_ai is None:
        _conversational_ai = ConversationalAI()
    return _conversational_ai
