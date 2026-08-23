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
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class UserIntent(Enum):
    """Intenciones del usuario detectadas por IA"""

    NEEDS_HELP = "needs_help"  # Necesita ayuda/orientación
    NOT_READY = "not_ready"  # No está listo para decidir
    CONFUSED = "confused"  # Está confundido
    WANTS_INFO = "wants_info"  # Quiere más información
    WANTS_EXPLANATION = "wants_explanation"  # Quiere que le expliquen algo ("explícame")
    ASKING_QUESTION = "asking_question"  # Hace una pregunta
    EXPRESSING_CONCERN = "concern"  # Expresa preocupación
    READY_TO_CONTINUE = "ready"  # Listo para continuar
    CORRECTION = "correction"  # Quiere corregir algo
    OFF_TOPIC = "off_topic"  # Tema no relacionado
    PROVIDING_INFO = "providing_info"  # Dando información (nombre, profesión, etc)
    GREETING = "greeting"  # Saludo
    GRATITUDE = "gratitude"  # Agradecimiento
    UNKNOWN = "unknown"  # No se pudo determinar


@dataclass
class ConversationalResponse:
    """Respuesta conversacional de la IA"""

    message: str
    follow_up_question: str | None = None
    suggested_actions: list[tuple[str, str]] = None  # [(texto, callback)]
    should_advance_state: bool = False
    new_state: str | None = None
    extracted_data: dict[str, Any] = None


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
            r"qué es",
            r"que es",
            r"cómo funciona",
            r"como funciona",
            r"tell me more",
            r"more info",
            r"how does.*work",
        ],
        UserIntent.WANTS_EXPLANATION: [
            # REGLA: "explícame" SIEMPRE debe explicar, NUNCA redirigir
            r"explícame",
            r"explicame",
            r"explícamelo",
            r"explicamelo",
            r"explain",
            r"explain to me",
            r"can you explain",
            r"puedes explicar",
            r"me puedes explicar",
            r"no entiendo.*expl",
            r"qué significa",
            r"que significa",
            r"qué quiere decir",
            r"que quiere decir",
            r"a qué te refieres",
            r"a que te refieres",
            r"what do you mean",
            r"what does.*mean",
        ],
        UserIntent.GREETING: [
            r"^hola",
            r"^hello",
            r"^hi$",
            r"^hey",
            r"^buenos días",
            r"^buenas tardes",
            r"^buenas noches",
            r"^good morning",
            r"^good afternoon",
            r"^good evening",
            r"^qué tal",
            r"^que tal",
        ],
        UserIntent.GRATITUDE: [
            r"gracias",
            r"thank",
            r"thanks",
            r"te agradezco",
            r"muy amable",
            r"appreciate",
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
                "¡Claro! Con gusto te cuento más. 📚\n\n" "{context_info}\n\n" "¿Qué más te gustaría saber?"
            ),
            UserIntent.ASKING_QUESTION: (
                "{ai_response}\n\n" "¿Eso responde tu pregunta? ¿Hay algo más que quieras saber?"
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
        },
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
        },
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

    def extract_data(self, text: str, current_state: str) -> dict[str, Any]:
        """
        V3.1.0 - HARDENED data extraction
        Extraer datos del texto libre del usuario.

        REGLA CRÍTICA para nombres:
        - SOLO extraer nombre si hay señal fuerte ('me llamo', 'mi nombre es')
        - O si estamos en estado ask_name/name
        - Si no, NO guardar nombre para evitar datos fantasma
        """
        from app.services.ux_improvements import NameValidator

        extracted = {}
        text_lower = text.lower()

        # V3.1.0 - HARDENED name extraction
        # REGLA: SOLO extraer nombre si:
        # 1. Hay señal fuerte ('me llamo', 'mi nombre es', etc.)
        # 2. O estamos en estado ask_name/name

        is_name_state = current_state in ["name", "ask_name", "NAME_REQUEST", "confirm_name"]
        has_strong_signal = NameValidator.has_strong_name_signal(text)

        if has_strong_signal:
            # Extraer nombre usando el método seguro
            extracted_name = NameValidator.extract_name_from_signal(text)
            if extracted_name:
                extracted["name"] = extracted_name
                logger.info(f"🔒 NAME EXTRACTED (strong signal) | name={extracted_name}")
        elif is_name_state:
            # En estado de nombre, validar el texto completo como nombre
            is_valid, result = NameValidator.is_valid_name(text.strip(), current_state)
            if is_valid:
                extracted["name"] = result
                logger.info(f"🔒 NAME EXTRACTED (name state) | name={result}")
            else:
                logger.info(f"🚫 NAME REJECTED | reason={result} | text={text[:50]}")
        else:
            # NO extraer nombre fuera de contexto - evitar datos fantasma
            logger.debug(f"🚫 NAME NOT EXTRACTED (no signal, wrong state) | state={current_state}")
            pass

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
        if any(
            w in text_lower
            for w in ["región", "region", "estado", "state", "zona", "área", "area", "ciudad", "city"]
        ):
            return "regions"
        if any(w in text_lower for w in ["visa", "permiso", "permit", "documento", "document"]):
            return "visas"
        if any(w in text_lower for w in ["proceso", "process", "paso", "step", "cómo", "how"]):
            return "process"
        if any(
            w in text_lower
            for w in ["costo", "cost", "precio", "price", "dinero", "money", "cuánto", "how much"]
        ):
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
        self, text: str, user: dict[str, Any], current_state: str, lang: str = "es"
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

        logger.info(
            f"🧠 AI Processing | user={user.get('telegram_id')} | intent={intent.value} | topic={topic} | extracted={extracted_data}"
        )

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

        elif intent == UserIntent.WANTS_EXPLANATION:
            # REGLA: "explícame" SIEMPRE explica, NUNCA redirige
            return await self._handle_explanation_request(name, text, topic, context_info, lang, user)

        elif intent == UserIntent.GREETING:
            return await self._handle_greeting(name, lang, user)

        elif intent == UserIntent.GRATITUDE:
            return await self._handle_gratitude(name, lang)

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
        self, name: str, text: str, extracted_data: dict[str, Any], lang: str, user: dict
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
            should_advance_state=False,  # No avanzar automáticamente, seguir conversando
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

        return ConversationalResponse(message=message, suggested_actions=actions, should_advance_state=False)

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

        return ConversationalResponse(message=message, suggested_actions=actions, should_advance_state=False)

    async def _handle_wants_info(
        self, name: str, text: str, topic: str, context_info: str, lang: str
    ) -> ConversationalResponse:
        """Manejar cuando el usuario quiere más información"""

        if lang == "es":
            message = f"¡Con gusto, {name}! 📚\n\n" f"{context_info}\n\n" "¿Qué más te gustaría saber?"
        else:
            message = f"Of course, {name}! 📚\n\n" f"{context_info}\n\n" "What else would you like to know?"

        return ConversationalResponse(message=message, should_advance_state=False)

    async def _handle_question(
        self, name: str, text: str, topic: str, context_info: str, lang: str, user: dict
    ) -> ConversationalResponse:
        """Manejar preguntas del usuario usando IA"""

        # Usar IA para responder la pregunta
        try:
            from app.services.ai_chat import chat_with_ai

            ai_response = await chat_with_ai(
                message=text, context={"profile": user.get("profile", {}), "topic": topic}
            )

            response_text = ai_response.get("response", context_info)

        except Exception as e:
            logger.warning(f"AI chat error: {e}")
            response_text = context_info

        if lang == "es":
            message = f"{response_text}\n\n" "¿Eso responde tu pregunta? ¿Hay algo más que quieras saber?"
        else:
            message = (
                f"{response_text}\n\n"
                "Does that answer your question? Is there anything else you'd like to know?"
            )

        return ConversationalResponse(message=message, should_advance_state=False)

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

        return ConversationalResponse(message=message, should_advance_state=False)

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

        return ConversationalResponse(message=message, suggested_actions=actions, should_advance_state=False)

    async def _handle_explanation_request(
        self, name: str, text: str, topic: str, context_info: str, lang: str, user: dict
    ) -> ConversationalResponse:
        """
        Manejar solicitudes de explicación.
        REGLA CRÍTICA: "explícame" SIEMPRE debe explicar, NUNCA redirigir.
        """

        # Detectar qué quiere que le expliquen
        text_lower = text.lower()

        # Explicaciones específicas por tema detectado
        explanations = {
            "es": {
                "visa": (
                    "📝 *TE EXPLICO SOBRE LAS VISAS*\n\n"
                    "Una visa es un permiso que te da un país para entrar y quedarte por un tiempo.\n\n"
                    "*Tipos principales para USA:*\n\n"
                    "💼 *Trabajo (H-1B):* Para profesionales con título universitario. "
                    "Tu empleador en USA debe patrocinarte.\n\n"
                    "🎓 *Estudiante (F-1):* Para estudiar en universidad o escuela. "
                    "Puedes trabajar medio tiempo.\n\n"
                    "🏢 *Inversionista (E-2):* Si inviertes dinero en un negocio en USA. "
                    "Mínimo ~$100,000.\n\n"
                    "👨\u200d👩\u200d👧 *Familiar:* Si tienes familia ciudadana o residente que te patrocine.\n\n"
                    "¿Qué tipo te interesa más o quieres que te explique alguno en detalle?"
                ),
                "proceso": (
                    "📝 *TE EXPLICO EL PROCESO DE MIGRACIÓN*\n\n"
                    "Migrar legalmente tiene varios pasos:\n\n"
                    "1️⃣ *Evaluación:* Primero entendemos tu situación y opciones.\n\n"
                    "2️⃣ *Elección de ruta:* Decidimos qué tipo de visa es mejor para ti.\n\n"
                    "3️⃣ *Documentación:* Reunimos todos los papeles necesarios.\n\n"
                    "4️⃣ *Aplicación:* Enviamos la solicitud al gobierno.\n\n"
                    "5️⃣ *Entrevista:* En algunos casos, entrevista en la embajada.\n\n"
                    "6️⃣ *Aprobación:* Si todo sale bien, recibes tu visa.\n\n"
                    "El tiempo varía según el tipo de visa (de meses a años).\n\n"
                    "¿Qué parte del proceso te gustaría entender mejor?"
                ),
                "costos": (
                    "📝 *TE EXPLICO LOS COSTOS*\n\n"
                    "Los costos de migrar incluyen:\n\n"
                    "💳 *Tarifas de visa:* $160-$500 (depende del tipo)\n\n"
                    "👨\u200d⚖️ *Abogado (opcional):* $2,000-$10,000\n\n"
                    "📄 *Documentos:* $200-$1,000 (traducciones, apostillas)\n\n"
                    "✈️ *Viaje:* Variable según origen\n\n"
                    "🏠 *Establecimiento:* 3-6 meses de gastos (renta, comida, etc.)\n\n"
                    "*Ejemplo para USA:* Un proceso completo puede costar entre $5,000 y $20,000.\n\n"
                    "¿Quieres que calcule un presupuesto más específico para tu caso?"
                ),
                "regiones": (
                    "📝 *TE EXPLICO LAS REGIONES DE USA*\n\n"
                    "Estados Unidos tiene 4 regiones principales:\n\n"
                    "☀️ *SUR (Florida, Texas, Georgia):*\n"
                    "- Clima cálido todo el año\n"
                    "- Gran comunidad latina\n"
                    "- Costo de vida moderado\n\n"
                    "🏙️ *NORESTE (New York, New Jersey):*\n"
                    "- Muchas oportunidades laborales\n"
                    "- Ciudades grandes y diversas\n"
                    "- Costo de vida alto\n\n"
                    "🌲 *OESTE (California, Washington):*\n"
                    "- Hub tecnológico\n"
                    "- Clima agradable\n"
                    "- Muy caro\n\n"
                    "🌾 *MEDIO OESTE (Illinois, Ohio):*\n"
                    "- Más económico\n"
                    "- Buenas oportunidades\n"
                    "- Inviernos fríos\n\n"
                    "¿Qué región te interesa más?"
                ),
                "default": (
                    f"📝 *CON GUSTO TE EXPLICO, {name}*\n\n"
                    f"{context_info}\n\n"
                    "¿Hay algo específico que quieras que te aclare?"
                ),
            },
            "en": {
                "visa": (
                    "📝 *LET ME EXPLAIN ABOUT VISAS*\n\n"
                    "A visa is a permit that allows you to enter and stay in a country.\n\n"
                    "*Main types for USA:*\n\n"
                    "💼 *Work (H-1B):* For professionals with a university degree. "
                    "Your US employer must sponsor you.\n\n"
                    "🎓 *Student (F-1):* To study at a university or school. "
                    "You can work part-time.\n\n"
                    "🏢 *Investor (E-2):* If you invest money in a US business. "
                    "Minimum ~$100,000.\n\n"
                    "👨\u200d👩\u200d👧 *Family:* If you have citizen or resident family to sponsor you.\n\n"
                    "Which type interests you most or would you like me to explain any in detail?"
                ),
                "default": (
                    f"📝 *I'M HAPPY TO EXPLAIN, {name}*\n\n"
                    f"{context_info}\n\n"
                    "Is there something specific you'd like me to clarify?"
                ),
            },
        }

        lang_explanations = explanations.get(lang, explanations["es"])

        # Detectar tema de la explicación
        if any(w in text_lower for w in ["visa", "permiso", "h1b", "h-1b", "f1", "f-1"]):
            message = lang_explanations.get("visa", lang_explanations["default"])
        elif any(w in text_lower for w in ["proceso", "process", "paso", "step", "cómo", "how"]):
            message = lang_explanations.get("proceso", lang_explanations["default"])
        elif any(w in text_lower for w in ["costo", "cost", "precio", "price", "dinero", "money"]):
            message = lang_explanations.get("costos", lang_explanations["default"])
        elif any(w in text_lower for w in ["región", "region", "estado", "state", "ciudad", "city"]):
            message = lang_explanations.get("regiones", lang_explanations["default"])
        else:
            message = lang_explanations["default"]

        return ConversationalResponse(message=message, should_advance_state=False)

    async def _handle_greeting(self, name: str, lang: str, user: dict) -> ConversationalResponse:
        """Manejar saludos del usuario"""

        # Verificar si es usuario nuevo o recurrente
        has_profile = bool(user.get("profile", {}).get("personal", {}).get("name"))

        if lang == "es":
            if has_profile:
                message = f"¡Hola de nuevo, {name}! 👋\n\n" "¿En qué puedo ayudarte hoy?"
            else:
                message = (
                    "¡Hola! 👋 Soy MigPAL, tu amigo en el proceso de migración.\n\n"
                    "Estoy aquí para ayudarte a planear tu viaje a un nuevo país. "
                    "Puedo responder tus preguntas, explicarte el proceso, "
                    "y ayudarte a encontrar la mejor opción para ti.\n\n"
                    "Cuéntame, ¿qué te trae por aquí hoy? 💭"
                )
        else:
            if has_profile:
                message = f"Hello again, {name}! 👋\n\n" "How can I help you today?"
            else:
                message = (
                    "Hello! 👋 I'm MigPAL, your friend in the migration process.\n\n"
                    "I'm here to help you plan your journey to a new country. "
                    "I can answer your questions, explain the process, "
                    "and help you find the best option for you.\n\n"
                    "Tell me, what brings you here today? 💭"
                )

        return ConversationalResponse(message=message, should_advance_state=False)

    async def _handle_gratitude(self, name: str, lang: str) -> ConversationalResponse:
        """Manejar agradecimientos del usuario"""

        if lang == "es":
            message = (
                f"¡De nada, {name}! 😊\n\n"
                "Estoy aquí para ayudarte. "
                "¿Hay algo más en lo que pueda asistirte?"
            )
        else:
            message = (
                f"You're welcome, {name}! 😊\n\n"
                "I'm here to help. "
                "Is there anything else I can assist you with?"
            )

        return ConversationalResponse(message=message, should_advance_state=False)

    async def _handle_unknown(
        self, name: str, text: str, topic: str, context_info: str, lang: str, user: dict
    ) -> ConversationalResponse:
        """Manejar intención desconocida - usar IA"""

        # Intentar usar IA para entender y responder
        try:
            from app.services.ai_chat import chat_with_ai

            ai_response = await chat_with_ai(
                message=text, context={"profile": user.get("profile", {}), "topic": topic}
            )

            response_text = ai_response.get("response", "")

            if response_text:
                return ConversationalResponse(message=response_text, should_advance_state=False)
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

        return ConversationalResponse(message=message, should_advance_state=False)


# Singleton
_conversational_ai = None


def get_conversational_ai() -> ConversationalAI:
    """Obtener instancia de la IA conversacional"""
    global _conversational_ai
    if _conversational_ai is None:
        _conversational_ai = ConversationalAI()
    return _conversational_ai
