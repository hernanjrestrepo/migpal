#!/usr/bin/env python3
"""
MigPAL Human Advisor v3.1.0
===========================
MigPAL como ASESOR MIGRATORIO HUMANO, no bot de formularios.

Principios:
1. Flujo conversacional general → particular
2. PROHIBIDO recomendar visa/país/plan sin Resumen de Entendimiento confirmado
3. Máximo 1 formulario cada 5 interacciones
4. Cada dato inferido debe ser parafraseado y validado
5. Si usuario corrige/duda/habla libre → reinterpretar, NO avanzar

Flujo de Exploración:
1. Motivo profundo (¿por qué realmente quieres migrar?)
2. Quiénes migran (familia, edades, dependientes)
3. Situación actual (trabajo, ingresos, educación)
4. Vida deseada (sueños, metas, estilo de vida)
5. Restricciones reales (dinero, tiempo, documentos)
6. SOLO DESPUÉS → opciones migratorias

Análisis:
- Emocional: Detectar miedo, ansiedad, entusiasmo, confusión
- Psicología del consumidor: Etapa de decisión, objeciones
- NLU: Intención real vs. palabras dichas
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Análisis de sentimiento
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

logger = logging.getLogger(__name__)


class ExplorationPhase(Enum):
    """Fases de exploración - general → particular"""
    GREETING = "greeting"                    # Saludo inicial
    DEEP_MOTIVATION = "deep_motivation"      # ¿Por qué REALMENTE quieres migrar?
    WHO_MIGRATES = "who_migrates"            # ¿Quiénes van? Familia, edades
    CURRENT_SITUATION = "current_situation"  # Situación actual
    DESIRED_LIFE = "desired_life"            # Vida deseada
    REAL_CONSTRAINTS = "real_constraints"    # Restricciones reales
    UNDERSTANDING_SUMMARY = "understanding"  # Resumen de entendimiento
    OPTIONS_EXPLORATION = "options"          # Explorar opciones (SOLO después del resumen)
    PLAN_CREATION = "plan_creation"          # Crear plan


class EmotionalState(Enum):
    """Estados emocionales detectados"""
    EXCITED = "excited"           # Entusiasmado
    HOPEFUL = "hopeful"           # Esperanzado
    ANXIOUS = "anxious"           # Ansioso
    FEARFUL = "fearful"           # Temeroso
    CONFUSED = "confused"         # Confundido
    FRUSTRATED = "frustrated"     # Frustrado
    DETERMINED = "determined"     # Determinado
    UNCERTAIN = "uncertain"       # Incierto
    NEUTRAL = "neutral"           # Neutral


class DecisionStage(Enum):
    """Etapas de decisión del consumidor"""
    AWARENESS = "awareness"       # Apenas considerando
    INTEREST = "interest"         # Interesado, buscando info
    CONSIDERATION = "consideration"  # Evaluando opciones
    INTENT = "intent"             # Decidido a actuar
    EVALUATION = "evaluation"     # Comparando opciones específicas
    PURCHASE = "purchase"         # Listo para comprometerse


@dataclass
class UserUnderstanding:
    """Entendimiento del usuario - debe ser confirmado antes de recomendar"""
    # Motivación profunda
    deep_motivation: Optional[str] = None
    underlying_fears: List[str] = field(default_factory=list)
    underlying_hopes: List[str] = field(default_factory=list)
    
    # Quiénes migran
    migrating_alone: Optional[bool] = None
    family_members: List[Dict[str, Any]] = field(default_factory=list)
    dependents_count: int = 0
    
    # Situación actual
    current_country: Optional[str] = None
    current_profession: Optional[str] = None
    years_experience: Optional[int] = None
    education_level: Optional[str] = None
    current_income: Optional[int] = None
    
    # Vida deseada
    desired_lifestyle: Optional[str] = None
    career_goals: Optional[str] = None
    family_priorities: List[str] = field(default_factory=list)
    
    # Restricciones
    available_savings: Optional[int] = None
    timeline_urgency: Optional[str] = None  # "urgent", "flexible", "no_rush"
    document_status: Optional[str] = None
    
    # Estado
    confirmed_by_user: bool = False
    last_updated: datetime = field(default_factory=datetime.now)
    
    def completeness_score(self) -> float:
        """Calcular qué tan completo está el entendimiento"""
        fields = [
            self.deep_motivation,
            self.migrating_alone is not None,
            self.current_profession,
            self.desired_lifestyle,
            self.available_savings is not None,
        ]
        return sum(1 for f in fields if f) / len(fields) * 100
    
    def missing_critical_info(self) -> List[str]:
        """Identificar información crítica faltante"""
        missing = []
        if not self.deep_motivation:
            missing.append("motivación profunda")
        if self.migrating_alone is None:
            missing.append("quiénes migran")
        if not self.current_profession:
            missing.append("situación laboral actual")
        if not self.desired_lifestyle:
            missing.append("vida deseada")
        if self.available_savings is None:
            missing.append("recursos disponibles")
        return missing


@dataclass
class ConversationContext:
    """Contexto de la conversación"""
    phase: ExplorationPhase = ExplorationPhase.GREETING
    emotional_state: EmotionalState = EmotionalState.NEUTRAL
    decision_stage: DecisionStage = DecisionStage.AWARENESS
    understanding: UserUnderstanding = field(default_factory=UserUnderstanding)
    
    # Control de formularios
    interaction_count: int = 0
    form_count: int = 0
    last_form_interaction: int = 0
    
    # Historial
    topics_discussed: List[str] = field(default_factory=list)
    pending_validations: List[str] = field(default_factory=list)
    
    def can_show_form(self) -> bool:
        """Verificar si se puede mostrar un formulario (máx 1 cada 5)"""
        if self.form_count == 0:
            return True
        return (self.interaction_count - self.last_form_interaction) >= 5
    
    def record_form(self):
        """Registrar que se mostró un formulario"""
        self.form_count += 1
        self.last_form_interaction = self.interaction_count
    
    def can_recommend(self) -> Tuple[bool, str]:
        """Verificar si se puede hacer recomendaciones"""
        if not self.understanding.confirmed_by_user:
            return False, "El Resumen de Entendimiento no ha sido confirmado"
        
        missing = self.understanding.missing_critical_info()
        if missing:
            return False, f"Falta información crítica: {', '.join(missing)}"
        
        return True, ""


class EmotionalAnalyzer:
    """Analizador emocional y psicológico"""
    
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer() if VADER_AVAILABLE else None
    
    def analyze_emotion(self, text: str, lang: str = "es") -> EmotionalState:
        """Detectar estado emocional del texto"""
        text_lower = text.lower()
        
        # Patrones emocionales en español
        emotion_patterns = {
            EmotionalState.EXCITED: [
                r"emocionad[oa]", r"feliz", r"genial", r"increíble", r"fantástico",
                r"no puedo esperar", r"muy ilusionad[oa]", r"🎉", r"😊", r"🚀"
            ],
            EmotionalState.ANXIOUS: [
                r"nervios[oa]", r"ansios[oa]", r"preocupad[oa]", r"estresad[oa]",
                r"no sé si", r"me da cosa", r"😰", r"😟"
            ],
            EmotionalState.FEARFUL: [
                r"miedo", r"temor", r"asustado", r"terror", r"pánico",
                r"me da miedo", r"tengo miedo", r"😨", r"😱"
            ],
            EmotionalState.CONFUSED: [
                r"confundid[oa]", r"no entiendo", r"no sé", r"perdid[oa]",
                r"no me queda claro", r"🤔", r"❓"
            ],
            EmotionalState.FRUSTRATED: [
                r"frustrad[oa]", r"harto", r"cansad[oa] de", r"ya no aguanto",
                r"imposible", r"😤", r"😠"
            ],
            EmotionalState.DETERMINED: [
                r"decidid[oa]", r"voy a", r"tengo que", r"necesito",
                r"estoy list[oa]", r"💪", r"✊"
            ],
            EmotionalState.HOPEFUL: [
                r"espero", r"ojalá", r"sueño con", r"me gustaría",
                r"tengo fe", r"🙏", r"✨"
            ],
            EmotionalState.UNCERTAIN: [
                r"no estoy segur[oa]", r"tal vez", r"quizás", r"puede ser",
                r"no sé si", r"depende"
            ],
        }
        
        for emotion, patterns in emotion_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return emotion
        
        # Usar VADER si está disponible
        if self.vader:
            scores = self.vader.polarity_scores(text)
            if scores['compound'] >= 0.5:
                return EmotionalState.EXCITED
            elif scores['compound'] <= -0.5:
                return EmotionalState.ANXIOUS
        
        return EmotionalState.NEUTRAL
    
    def analyze_decision_stage(self, text: str, context: ConversationContext) -> DecisionStage:
        """Detectar etapa de decisión del consumidor"""
        text_lower = text.lower()
        
        # Indicadores de cada etapa
        if any(w in text_lower for w in ["solo preguntando", "curiosidad", "qué es", "cómo funciona"]):
            return DecisionStage.AWARENESS
        
        if any(w in text_lower for w in ["me interesa", "cuéntame más", "quiero saber"]):
            return DecisionStage.INTEREST
        
        if any(w in text_lower for w in ["estoy considerando", "pensando en", "evaluando"]):
            return DecisionStage.CONSIDERATION
        
        if any(w in text_lower for w in ["quiero hacerlo", "voy a", "decidí", "necesito empezar"]):
            return DecisionStage.INTENT
        
        if any(w in text_lower for w in ["cuál es mejor", "comparar", "diferencia entre"]):
            return DecisionStage.EVALUATION
        
        if any(w in text_lower for w in ["listo para", "empecemos", "cuánto cuesta", "cómo pago"]):
            return DecisionStage.PURCHASE
        
        return context.decision_stage


class HumanAdvisor:
    """
    Asesor Migratorio Humano
    
    Actúa como un consultor humano, no como un bot.
    Escucha, entiende, valida y solo entonces recomienda.
    """
    
    def __init__(self):
        self.emotional_analyzer = EmotionalAnalyzer()
        self.contexts: Dict[int, ConversationContext] = {}
    
    def get_context(self, user_id: int) -> ConversationContext:
        """Obtener o crear contexto de conversación"""
        if user_id not in self.contexts:
            self.contexts[user_id] = ConversationContext()
        return self.contexts[user_id]
    
    async def process_message(
        self,
        user_id: int,
        text: str,
        user_data: Dict[str, Any],
        lang: str = "es"
    ) -> Dict[str, Any]:
        """
        Procesar mensaje del usuario como asesor humano.
        
        Returns:
            {
                "response": str,
                "buttons": List[Tuple[str, str]] or None,
                "extracted_data": Dict,
                "phase_changed": bool,
                "needs_validation": bool,
                "validation_summary": str or None,
            }
        """
        ctx = self.get_context(user_id)
        ctx.interaction_count += 1
        
        # Analizar emoción y etapa de decisión
        ctx.emotional_state = self.emotional_analyzer.analyze_emotion(text, lang)
        ctx.decision_stage = self.emotional_analyzer.analyze_decision_stage(text, ctx)
        
        logger.info(f"🧠 HumanAdvisor | user={user_id} | phase={ctx.phase.value} | emotion={ctx.emotional_state.value} | stage={ctx.decision_stage.value}")
        
        # Extraer datos del texto
        extracted = self._extract_data(text, ctx, lang)
        
        # Verificar si el usuario está corrigiendo o dudando
        if self._is_correction_or_doubt(text, lang, ctx):
            return await self._handle_correction_or_doubt(text, ctx, lang)
        
        # Verificar si intenta saltar fases
        if self._is_premature_request(text, ctx, lang):
            return await self._handle_premature_request(text, ctx, lang)
        
        # Procesar según la fase actual
        response = await self._process_by_phase(text, ctx, extracted, lang)
        
        # Si hay datos extraídos, validarlos antes de avanzar
        if extracted and not response.get("needs_validation"):
            validation = self._create_validation_summary(extracted, lang)
            if validation:
                response["needs_validation"] = True
                response["validation_summary"] = validation
        
        return response
    
    def _extract_data(self, text: str, ctx: ConversationContext, lang: str) -> Dict[str, Any]:
        """Extraer datos del texto libre"""
        extracted = {}
        text_lower = text.lower()
        
        # Motivación profunda
        motivation_patterns = {
            "better_life": [r"mejor vida", r"futuro mejor", r"calidad de vida"],
            "family_reunion": [r"reunir.*familia", r"estar con.*familia", r"mis hijos", r"mis padres"],
            "escape_situation": [r"salir de", r"escapar", r"huir", r"no aguanto", r"inseguridad"],
            "career_growth": [r"crecer profesional", r"mejor trabajo", r"oportunidades laborales"],
            "education": [r"estudiar", r"universidad", r"educación para"],
            "adventure": [r"conocer", r"experiencia", r"aventura", r"nuevo comienzo"],
        }
        
        for motivation, patterns in motivation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    extracted["motivation_type"] = motivation
                    break
        
        # Familia
        family_patterns = [
            (r"solo|soltero|soltera", "alone"),
            (r"esposa|esposo|pareja|novio|novia", "with_partner"),
            (r"hijos?|niños?|bebé", "with_children"),
            (r"familia completa|todos", "whole_family"),
        ]
        
        for pattern, family_type in family_patterns:
            if re.search(pattern, text_lower):
                extracted["family_situation"] = family_type
                break
        
        # Edades de hijos
        age_match = re.search(r"(\d+)\s*(?:años?|year)", text_lower)
        if age_match and "hijo" in text_lower or "niño" in text_lower:
            extracted["child_age"] = int(age_match.group(1))
        
        # Profesión
        profession_patterns = [
            r"soy\s+(ingeniero|doctor|abogado|contador|profesor|enfermero|programador|diseñador)[a-z]*",
            r"trabajo\s+(?:como|de)\s+(\w+)",
            r"me\s+dedico\s+a\s+(\w+)",
        ]
        
        for pattern in profession_patterns:
            match = re.search(pattern, text_lower)
            if match:
                extracted["profession"] = match.group(1)
                break
        
        # Experiencia
        exp_match = re.search(r"(\d+)\s*años?\s*(?:de\s+)?experiencia", text_lower)
        if exp_match:
            extracted["years_experience"] = int(exp_match.group(1))
        
        # Dinero
        money_patterns = [
            (r"(?:tengo|cuento con|dispongo de)[^\d]*\$?([\d,]+)", "savings"),
            (r"(?:gano|salario|sueldo)[^\d]*\$?([\d,]+)", "income"),
            (r"(?:ahorr[oa]d?[oa]?s?)[^\d]*\$?([\d,]+)", "savings"),
        ]
        
        for pattern, money_type in money_patterns:
            match = re.search(pattern, text_lower)
            if match and match.group(1):
                amount_str = match.group(1).replace(",", "")
                if amount_str:
                    try:
                        extracted[money_type] = int(amount_str)
                    except ValueError:
                        pass
        
        # Urgencia
        if any(w in text_lower for w in ["urgente", "pronto", "ya", "inmediato", "este año"]):
            extracted["urgency"] = "urgent"
        elif any(w in text_lower for w in ["sin prisa", "cuando sea", "no hay apuro", "flexible"]):
            extracted["urgency"] = "flexible"
        
        return extracted
    
    def _is_correction_or_doubt(self, text: str, lang: str, ctx: 'ConversationContext' = None) -> bool:
        """Detectar si el usuario está corrigiendo o dudando"""
        text_lower = text.lower()
        
        # En la fase de saludo, "no sé si quiero migrar" es válido, no es duda bloqueante
        if ctx and ctx.phase == ExplorationPhase.GREETING:
            # Solo bloquear si es una corrección explícita
            correction_patterns = [
                r"no,?\s*(en realidad|quise decir|me equivoqué)",
                r"corrijo|corrección",
                r"perdón,?\s*(es|era|quise)",
                r"no es así",
                r"me expresé mal",
            ]
            for pattern in correction_patterns:
                if re.search(pattern, text_lower):
                    return True
            return False
        
        correction_patterns = [
            r"no,?\s*(en realidad|quise decir|me equivoqué)",
            r"corrijo|corrección",
            r"perdón,?\s*(es|era|quise)",
            r"no es así",
            r"me expresé mal",
            r"no,?\s*espera",  # "no, espera" en cualquier parte
            r"\.\.\.[^.]*espera",  # "... espera"
        ]
        
        doubt_patterns = [
            r"déjame pensar",
            r"un momento",
            r"^espera$",  # Solo "espera"
        ]
        
        for pattern in correction_patterns + doubt_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _is_premature_request(self, text: str, ctx: ConversationContext, lang: str) -> bool:
        """Detectar si el usuario intenta saltar a recomendaciones sin contexto"""
        text_lower = text.lower()
        
        # Solicitudes prematuras
        premature_patterns = [
            r"qué visa",
            r"cuál es la mejor visa",
            r"recomiéndame",
            r"dime qué hacer",
            r"cuál es el plan",
            r"a qué país",
        ]
        
        # Solo es prematuro si no hemos completado el entendimiento
        if ctx.understanding.completeness_score() < 60:
            for pattern in premature_patterns:
                if re.search(pattern, text_lower):
                    return True
        
        return False
    
    async def _handle_correction_or_doubt(
        self, text: str, ctx: ConversationContext, lang: str
    ) -> Dict[str, Any]:
        """Manejar corrección o duda - NO avanzar de estado"""
        
        if lang == "es":
            response = (
                "Entiendo, tomemos un momento. 🤔\n\n"
                "Es completamente normal tener dudas o querer aclarar algo. "
                "Esto es importante y quiero asegurarme de entenderte bien.\n\n"
                "¿Podrías contarme más sobre lo que estás pensando?"
            )
        else:
            response = (
                "I understand, let's take a moment. 🤔\n\n"
                "It's completely normal to have doubts or want to clarify something. "
                "This is important and I want to make sure I understand you correctly.\n\n"
                "Could you tell me more about what you're thinking?"
            )
        
        return {
            "response": response,
            "buttons": None,
            "extracted_data": {},
            "phase_changed": False,
            "needs_validation": False,
        }
    
    async def _handle_premature_request(
        self, text: str, ctx: ConversationContext, lang: str
    ) -> Dict[str, Any]:
        """Manejar solicitud prematura de recomendaciones"""
        
        missing = ctx.understanding.missing_critical_info()
        
        if lang == "es":
            response = (
                "Entiendo que quieres avanzar, y me encanta tu entusiasmo. 🌟\n\n"
                "Pero como tu asesor, necesito conocerte mejor antes de darte "
                "recomendaciones que realmente te sirvan.\n\n"
                "Imagina que voy a un doctor y le digo 'recétame algo'. "
                "Un buen doctor primero pregunta, examina, y luego recomienda.\n\n"
            )
            
            if missing:
                response += f"Todavía me falta entender: {', '.join(missing)}.\n\n"
            
            response += "¿Me cuentas un poco más sobre tu situación?"
            
        else:
            response = (
                "I understand you want to move forward, and I love your enthusiasm. 🌟\n\n"
                "But as your advisor, I need to know you better before giving you "
                "recommendations that will truly help you.\n\n"
                "Imagine going to a doctor and saying 'prescribe me something'. "
                "A good doctor first asks, examines, and then recommends.\n\n"
            )
            
            if missing:
                response += f"I still need to understand: {', '.join(missing)}.\n\n"
            
            response += "Could you tell me a bit more about your situation?"
        
        return {
            "response": response,
            "buttons": None,
            "extracted_data": {},
            "phase_changed": False,
            "needs_validation": False,
        }
    
    async def _process_by_phase(
        self, text: str, ctx: ConversationContext, extracted: Dict, lang: str
    ) -> Dict[str, Any]:
        """Procesar según la fase actual"""
        
        phase_handlers = {
            ExplorationPhase.GREETING: self._phase_greeting,
            ExplorationPhase.DEEP_MOTIVATION: self._phase_deep_motivation,
            ExplorationPhase.WHO_MIGRATES: self._phase_who_migrates,
            ExplorationPhase.CURRENT_SITUATION: self._phase_current_situation,
            ExplorationPhase.DESIRED_LIFE: self._phase_desired_life,
            ExplorationPhase.REAL_CONSTRAINTS: self._phase_real_constraints,
            ExplorationPhase.UNDERSTANDING_SUMMARY: self._phase_understanding_summary,
            ExplorationPhase.OPTIONS_EXPLORATION: self._phase_options,
        }
        
        handler = phase_handlers.get(ctx.phase, self._phase_greeting)
        return await handler(text, ctx, extracted, lang)
    
    async def _phase_greeting(
        self, text: str, ctx: ConversationContext, extracted: Dict, lang: str
    ) -> Dict[str, Any]:
        """
        SEGMENTO 1: Inicio humano y contención
        
        GUIÓN OFICIAL:
        - Escuchar sin pedir datos
        - No avanzar hasta que el usuario haya compartido
        - Respuestas empáticas según estado emocional
        """
        from app.services.migpal_script_usa import get_migpal_script_usa
        
        script = get_migpal_script_usa()
        
        # Si es la primera interacción, dar el saludo oficial
        if ctx.interaction_count <= 1:
            greeting = script.get_greeting(lang)
            return {
                "response": greeting.message,
                "buttons": None,
                "extracted_data": extracted,
                "phase_changed": False,
                "needs_validation": False,
            }
        
        # Procesar respuesta del usuario en Segmento 1
        emotional_state = ctx.emotional_state.value
        script_response = script.process_segment_1(text, emotional_state, lang)
        
        # Si el guion indica transición a Segmento 2, cambiar fase
        if script_response.segment.value == "s2_escucha_profunda":
            ctx.phase = ExplorationPhase.DEEP_MOTIVATION
            return {
                "response": script_response.message,
                "buttons": None,
                "extracted_data": extracted,
                "phase_changed": True,
                "needs_validation": False,
            }
        
        # Seguir en Segmento 1 - escuchando
        return {
            "response": script_response.message,
            "buttons": None,
            "extracted_data": extracted,
            "phase_changed": False,
            "needs_validation": False,
        }
    
    async def _phase_deep_motivation(
        self, text: str, ctx: ConversationContext, extracted: Dict, lang: str
    ) -> Dict[str, Any]:
        """Fase de motivación profunda"""
        
        # Guardar motivación
        if extracted.get("motivation_type"):
            ctx.understanding.deep_motivation = extracted["motivation_type"]
        else:
            # Guardar el texto como motivación si no se detectó patrón
            ctx.understanding.deep_motivation = text[:200]
        
        # Parafrasear y validar
        motivation_paraphrases = {
            "better_life": "buscar una mejor calidad de vida para ti y los tuyos",
            "family_reunion": "reunirte con tu familia",
            "escape_situation": "salir de una situación difícil",
            "career_growth": "crecer profesionalmente",
            "education": "acceder a mejor educación",
            "adventure": "vivir una nueva experiencia",
        }
        
        paraphrase = motivation_paraphrases.get(
            extracted.get("motivation_type", ""),
            "lo que me cuentas"
        )
        
        if lang == "es":
            response = (
                f"Entiendo... {paraphrase}. 💭\n\n"
                "Eso es muy importante y válido.\n\n"
                "Ahora cuéntame, ¿quiénes estarían migrando contigo? "
                "¿Viajas solo/a, con pareja, con hijos? "
                "Si hay niños, ¿qué edades tienen?"
            )
        else:
            response = (
                f"I understand... {paraphrase}. 💭\n\n"
                "That's very important and valid.\n\n"
                "Now tell me, who would be migrating with you? "
                "Are you traveling alone, with a partner, with children? "
                "If there are children, what ages are they?"
            )
        
        ctx.phase = ExplorationPhase.WHO_MIGRATES
        ctx.topics_discussed.append("motivation")
        
        return {
            "response": response,
            "buttons": None,
            "extracted_data": extracted,
            "phase_changed": True,
            "needs_validation": False,
        }
    
    async def _phase_who_migrates(
        self, text: str, ctx: ConversationContext, extracted: Dict, lang: str
    ) -> Dict[str, Any]:
        """Fase de quiénes migran"""
        
        # Guardar información familiar
        family_situation = extracted.get("family_situation", "")
        ctx.understanding.migrating_alone = family_situation == "alone"
        
        if extracted.get("child_age"):
            ctx.understanding.family_members.append({
                "type": "child",
                "age": extracted["child_age"]
            })
        
        # Parafrasear
        if family_situation == "alone":
            paraphrase = "viajas solo/a"
        elif family_situation == "with_partner":
            paraphrase = "viajas con tu pareja"
        elif family_situation == "with_children":
            paraphrase = "viajas con tus hijos"
        elif family_situation == "whole_family":
            paraphrase = "viaja toda la familia"
        else:
            paraphrase = "tu situación familiar"
        
        if lang == "es":
            response = (
                f"Perfecto, entonces {paraphrase}. 👨‍👩‍👧\n\n"
                "Ahora me gustaría entender tu situación actual.\n\n"
                "¿A qué te dedicas actualmente? "
                "¿Cuántos años de experiencia tienes? "
                "¿Qué nivel de estudios completaste?"
            )
        else:
            response = (
                f"Perfect, so {paraphrase}. 👨‍👩‍👧\n\n"
                "Now I'd like to understand your current situation.\n\n"
                "What do you currently do for work? "
                "How many years of experience do you have? "
                "What level of education did you complete?"
            )
        
        ctx.phase = ExplorationPhase.CURRENT_SITUATION
        ctx.topics_discussed.append("family")
        
        return {
            "response": response,
            "buttons": None,
            "extracted_data": extracted,
            "phase_changed": True,
            "needs_validation": False,
        }
    
    async def _phase_current_situation(
        self, text: str, ctx: ConversationContext, extracted: Dict, lang: str
    ) -> Dict[str, Any]:
        """Fase de situación actual"""
        
        # Guardar datos
        if extracted.get("profession"):
            ctx.understanding.current_profession = extracted["profession"]
        if extracted.get("years_experience"):
            ctx.understanding.years_experience = extracted["years_experience"]
        if extracted.get("income"):
            ctx.understanding.current_income = extracted["income"]
        
        # Parafrasear
        profession = extracted.get("profession", "tu profesión")
        years = extracted.get("years_experience", "")
        years_text = f" con {years} años de experiencia" if years else ""
        
        if lang == "es":
            response = (
                f"¡Excelente! Eres {profession}{years_text}. 💼\n\n"
                "Eso es un gran activo.\n\n"
                "Ahora, hablemos de tus sueños. "
                "Si pudieras diseñar tu vida ideal después de migrar, "
                "¿cómo sería? ¿Qué tipo de trabajo te gustaría? "
                "¿En qué tipo de lugar te imaginas viviendo?"
            )
        else:
            response = (
                f"Excellent! You're a {profession}{years_text}. 💼\n\n"
                "That's a great asset.\n\n"
                "Now, let's talk about your dreams. "
                "If you could design your ideal life after migrating, "
                "what would it look like? What kind of work would you like? "
                "What kind of place do you imagine living in?"
            )
        
        ctx.phase = ExplorationPhase.DESIRED_LIFE
        ctx.topics_discussed.append("current_situation")
        
        return {
            "response": response,
            "buttons": None,
            "extracted_data": extracted,
            "phase_changed": True,
            "needs_validation": False,
        }
    
    async def _phase_desired_life(
        self, text: str, ctx: ConversationContext, extracted: Dict, lang: str
    ) -> Dict[str, Any]:
        """Fase de vida deseada"""
        
        # Guardar sueños
        ctx.understanding.desired_lifestyle = text[:300]
        
        if lang == "es":
            response = (
                "Me encanta esa visión. ✨\n\n"
                "Ahora, hablemos de algo práctico pero importante: los recursos.\n\n"
                "¿Con cuánto dinero cuentas aproximadamente para este proyecto? "
                "(ahorros, posibles préstamos, apoyo familiar)\n\n"
                "Y en términos de tiempo, ¿hay alguna urgencia? "
                "¿O tienes flexibilidad para planificar con calma?"
            )
        else:
            response = (
                "I love that vision. ✨\n\n"
                "Now, let's talk about something practical but important: resources.\n\n"
                "Approximately how much money do you have for this project? "
                "(savings, possible loans, family support)\n\n"
                "And in terms of time, is there any urgency? "
                "Or do you have flexibility to plan calmly?"
            )
        
        ctx.phase = ExplorationPhase.REAL_CONSTRAINTS
        ctx.topics_discussed.append("desired_life")
        
        return {
            "response": response,
            "buttons": None,
            "extracted_data": extracted,
            "phase_changed": True,
            "needs_validation": False,
        }
    
    async def _phase_real_constraints(
        self, text: str, ctx: ConversationContext, extracted: Dict, lang: str
    ) -> Dict[str, Any]:
        """Fase de restricciones reales"""
        
        # Guardar restricciones
        if extracted.get("savings"):
            ctx.understanding.available_savings = extracted["savings"]
        if extracted.get("urgency"):
            ctx.understanding.timeline_urgency = extracted["urgency"]
        
        ctx.topics_discussed.append("constraints")
        
        # Crear resumen de entendimiento
        return await self._create_understanding_summary(ctx, lang)
    
    async def _create_understanding_summary(
        self, ctx: ConversationContext, lang: str
    ) -> Dict[str, Any]:
        """Crear resumen de entendimiento para confirmación"""
        
        u = ctx.understanding
        
        if lang == "es":
            summary = "📋 *RESUMEN DE ENTENDIMIENTO*\n\n"
            summary += "Antes de darte recomendaciones, quiero asegurarme de que te entendí bien:\n\n"
            
            if u.deep_motivation:
                summary += f"🎯 *Motivación:* {u.deep_motivation}\n\n"
            
            if u.migrating_alone is not None:
                family = "solo/a" if u.migrating_alone else "con familia"
                summary += f"👨‍👩‍👧 *Quiénes migran:* {family}\n"
                if u.family_members:
                    for member in u.family_members:
                        summary += f"   - {member.get('type', 'familiar')}: {member.get('age', '?')} años\n"
                summary += "\n"
            
            if u.current_profession:
                exp = f" ({u.years_experience} años exp.)" if u.years_experience else ""
                summary += f"💼 *Profesión:* {u.current_profession}{exp}\n\n"
            
            if u.desired_lifestyle:
                summary += f"✨ *Vida deseada:* {u.desired_lifestyle[:100]}...\n\n"
            
            if u.available_savings:
                summary += f"💰 *Recursos:* ${u.available_savings:,}\n"
            if u.timeline_urgency:
                urgency_text = {"urgent": "Urgente", "flexible": "Flexible", "no_rush": "Sin prisa"}
                summary += f"⏰ *Tiempo:* {urgency_text.get(u.timeline_urgency, u.timeline_urgency)}\n"
            
            summary += "\n¿Es correcto? ¿Hay algo que quieras corregir o agregar?"
            
            buttons = [
                ("✅ Sí, es correcto", "understanding_confirmed"),
                ("✏️ Quiero corregir algo", "understanding_correct"),
                ("➕ Quiero agregar algo", "understanding_add"),
            ]
        else:
            summary = "📋 *UNDERSTANDING SUMMARY*\n\n"
            summary += "Before giving you recommendations, I want to make sure I understood you correctly:\n\n"
            # ... (versión en inglés similar)
            
            buttons = [
                ("✅ Yes, that's correct", "understanding_confirmed"),
                ("✏️ I want to correct something", "understanding_correct"),
                ("➕ I want to add something", "understanding_add"),
            ]
        
        ctx.phase = ExplorationPhase.UNDERSTANDING_SUMMARY
        
        return {
            "response": summary,
            "buttons": buttons,
            "extracted_data": {},
            "phase_changed": True,
            "needs_validation": True,
            "validation_summary": summary,
        }
    
    async def _phase_understanding_summary(
        self, text: str, ctx: ConversationContext, extracted: Dict, lang: str
    ) -> Dict[str, Any]:
        """Fase de confirmación del resumen"""
        
        # Si el usuario confirma, marcar como confirmado y avanzar
        if any(w in text.lower() for w in ["sí", "si", "correcto", "yes", "correct"]):
            ctx.understanding.confirmed_by_user = True
            ctx.phase = ExplorationPhase.OPTIONS_EXPLORATION
            
            if lang == "es":
                response = (
                    "¡Perfecto! Ahora sí puedo darte recomendaciones personalizadas. 🎯\n\n"
                    "Basándome en tu perfil, voy a analizar las mejores opciones para ti.\n\n"
                    "Dame un momento..."
                )
            else:
                response = (
                    "Perfect! Now I can give you personalized recommendations. 🎯\n\n"
                    "Based on your profile, I'm going to analyze the best options for you.\n\n"
                    "Give me a moment..."
                )
            
            return {
                "response": response,
                "buttons": None,
                "extracted_data": {},
                "phase_changed": True,
                "needs_validation": False,
            }
        
        # Si quiere corregir, volver a la fase apropiada
        return await self._handle_correction_or_doubt(text, ctx, lang)
    
    async def _phase_options(
        self, text: str, ctx: ConversationContext, extracted: Dict, lang: str
    ) -> Dict[str, Any]:
        """Fase de exploración de opciones - SOLO después de confirmación"""
        
        can_recommend, reason = ctx.can_recommend()
        
        if not can_recommend:
            if lang == "es":
                response = f"Antes de continuar, {reason}. ¿Me ayudas con eso?"
            else:
                response = f"Before continuing, {reason}. Can you help me with that?"
            
            return {
                "response": response,
                "buttons": None,
                "extracted_data": {},
                "phase_changed": False,
                "needs_validation": False,
            }
        
        # Aquí iría la lógica de recomendaciones personalizadas
        # basadas en el entendimiento confirmado
        
        if lang == "es":
            response = (
                "🗺️ *OPCIONES PARA TI*\n\n"
                "Basándome en tu perfil, estas son las opciones que más te convienen:\n\n"
                "... (recomendaciones personalizadas)"
            )
        else:
            response = (
                "🗺️ *OPTIONS FOR YOU*\n\n"
                "Based on your profile, these are the options that suit you best:\n\n"
                "... (personalized recommendations)"
            )
        
        return {
            "response": response,
            "buttons": None,
            "extracted_data": {},
            "phase_changed": False,
            "needs_validation": False,
        }
    
    def _create_validation_summary(self, extracted: Dict, lang: str) -> Optional[str]:
        """Crear resumen de validación para datos extraídos"""
        if not extracted:
            return None
        
        parts = []
        
        if lang == "es":
            if "profession" in extracted:
                parts.append(f"Eres {extracted['profession']}")
            if "years_experience" in extracted:
                parts.append(f"con {extracted['years_experience']} años de experiencia")
            if "savings" in extracted:
                parts.append(f"cuentas con ${extracted['savings']:,}")
            if "family_situation" in extracted:
                situations = {
                    "alone": "viajas solo/a",
                    "with_partner": "viajas con tu pareja",
                    "with_children": "viajas con hijos",
                }
                parts.append(situations.get(extracted["family_situation"], ""))
            
            if parts:
                return "Entiendo que " + ", ".join(parts) + ". ¿Es correcto?"
        
        return None


# Singleton
_human_advisor = None

def get_human_advisor() -> HumanAdvisor:
    """Obtener instancia del asesor humano"""
    global _human_advisor
    if _human_advisor is None:
        _human_advisor = HumanAdvisor()
    return _human_advisor
