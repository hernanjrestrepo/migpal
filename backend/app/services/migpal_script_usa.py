#!/usr/bin/env python3
"""
🇺🇸 GUION OFICIAL MIGPAL USA - MVP
==================================

Este es el guion conversacional oficial para migración a Estados Unidos.
Es una GUÍA FLEXIBLE - MigPAL y el cliente pueden adaptarlo.

REGLAS:
- Segmentos en orden estricto
- Prohibido hablar de visas/estados/ciudades hasta el segmento indicado
- Cada segmento requiere confirmación antes de avanzar
- Máx. 1 formulario cada 5 interacciones
- El resto es conversación libre con NLU

FLUJO:
1. Inicio humano y contención
2. Escucha profunda (pendiente)
3. Quiénes migran (pendiente)
4. Situación actual (pendiente)
5. Vida deseada (pendiente)
6. Restricciones (pendiente)
7. Resumen de entendimiento (pendiente)
8. Opciones migratorias (pendiente)
9. Plan personalizado (pendiente)
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class ScriptSegment(Enum):
    """Segmentos del guion MigPAL USA"""
    S1_INICIO_HUMANO = "s1_inicio_humano"           # Inicio y contención
    S2_ESCUCHA_PROFUNDA = "s2_escucha_profunda"     # Escuchar sin pedir datos
    S3_QUIENES_MIGRAN = "s3_quienes_migran"         # Familia, dependientes
    S4_SITUACION_ACTUAL = "s4_situacion_actual"     # Trabajo, ingresos
    S5_VIDA_DESEADA = "s5_vida_deseada"             # Sueños, metas
    S6_RESTRICCIONES = "s6_restricciones"           # Dinero, tiempo, docs
    S7_RESUMEN_ENTENDIMIENTO = "s7_resumen"         # Validación obligatoria
    S8_OPCIONES_MIGRATORIAS = "s8_opciones"         # SOLO después de S7
    S9_PLAN_PERSONALIZADO = "s9_plan"               # Plan final


@dataclass
class ScriptResponse:
    """Respuesta del guion"""
    message: str
    segment: ScriptSegment
    can_advance: bool = False
    buttons: Optional[List[Tuple[str, str]]] = None
    requires_confirmation: bool = False


class MigPALScriptUSA:
    """
    Guion Conversacional MigPAL USA
    
    Implementa el flujo oficial de conversación para migración a USA.
    Es una guía flexible que puede adaptarse al usuario.
    """
    
    # =========================================================================
    # SEGMENTO 1: INICIO HUMANO Y CONTENCIÓN
    # =========================================================================
    
    SEGMENT_1_GREETING = {
        "es": """Hola 👋

Soy MigPAL. Estoy aquí para ayudarte a pensar con claridad tu posible migración a Estados Unidos.

Antes de hablar de visas o papeles, quiero escucharte. Migrar a USA casi siempre nace de una mezcla de ilusión, presión económica, cansancio o ganas de empezar de nuevo.

Aquí no hay respuestas correctas. No hay juicios. Y no hay prisa.

Para empezar, dime algo abierto, con tus propias palabras:

👉 *¿Qué está pasando hoy en tu vida que te hizo pensar en irte a Estados Unidos?*""",

        "en": """Hi 👋

I'm MigPAL. I'm here to help you think clearly about your possible migration to the United States.

Before talking about visas or paperwork, I want to listen to you. Migrating to the USA almost always comes from a mix of hope, economic pressure, exhaustion, or the desire to start over.

There are no right answers here. No judgments. And no rush.

To start, tell me something open, in your own words:

👉 *What's happening in your life today that made you think about going to the United States?*"""
    }
    
    # Respuestas empáticas para Segmento 1 (escuchar, no pedir datos)
    SEGMENT_1_LISTENING_RESPONSES = {
        "es": {
            "anxious": (
                "Gracias por compartir eso conmigo. 💙\n\n"
                "Noto que hay algo de peso en lo que me cuentas. "
                "Es completamente normal sentirse así cuando se piensa en un cambio tan grande.\n\n"
                "Cuéntame más... ¿hace cuánto tiempo llevas pensando en esto?"
            ),
            "hopeful": (
                "Gracias por abrirte así. ✨\n\n"
                "Puedo sentir la esperanza en lo que me cuentas. "
                "Eso es muy valioso.\n\n"
                "Me gustaría entender mejor... ¿qué es lo que más te ilusiona de ese cambio?"
            ),
            "fearful": (
                "Gracias por confiar en mí con esto. 🤝\n\n"
                "Entiendo que hay miedo. Migrar es una decisión enorme "
                "y es completamente válido sentir temor.\n\n"
                "¿Qué es lo que más te preocupa de todo esto?"
            ),
            "frustrated": (
                "Te escucho. 💪\n\n"
                "Parece que hay mucha frustración acumulada. "
                "A veces llega un punto donde uno dice 'ya basta'.\n\n"
                "¿Qué es lo que más te tiene cansado/a de tu situación actual?"
            ),
            "determined": (
                "Me gusta esa determinación. 🎯\n\n"
                "Se nota que has pensado en esto. "
                "Esa claridad es importante.\n\n"
                "Cuéntame más sobre lo que te llevó a tomar esta decisión."
            ),
            "neutral": (
                "Gracias por compartir eso. 🙏\n\n"
                "Cada historia es única y quiero entender la tuya.\n\n"
                "¿Hay algo más que quieras contarme sobre lo que estás viviendo?"
            ),
            "confused": (
                "Entiendo. 🤔\n\n"
                "A veces no es fácil poner en palabras lo que sentimos. "
                "Y está bien no tener todo claro.\n\n"
                "¿Qué es lo primero que te viene a la mente cuando piensas en irte?"
            ),
        },
        "en": {
            "anxious": (
                "Thank you for sharing that with me. 💙\n\n"
                "I notice there's some weight in what you're telling me. "
                "It's completely normal to feel this way when thinking about such a big change.\n\n"
                "Tell me more... how long have you been thinking about this?"
            ),
            "hopeful": (
                "Thank you for opening up like this. ✨\n\n"
                "I can feel the hope in what you're telling me. "
                "That's very valuable.\n\n"
                "I'd like to understand better... what excites you most about this change?"
            ),
            "neutral": (
                "Thank you for sharing that. 🙏\n\n"
                "Every story is unique and I want to understand yours.\n\n"
                "Is there anything else you'd like to tell me about what you're going through?"
            ),
        }
    }
    
    # Indicadores de que el usuario está listo para avanzar del Segmento 1
    SEGMENT_1_READY_INDICATORS = [
        r"ya te conté",
        r"eso es todo",
        r"qué sigue",
        r"y ahora qué",
        r"siguiente",
        r"continuar",
        r"listo",
        r"ok",
        r"entendido",
    ]
    
    def __init__(self):
        self.current_segment = ScriptSegment.S1_INICIO_HUMANO
        self.segment_interactions = 0
        self.user_shared_enough = False
    
    def get_greeting(self, lang: str = "es") -> ScriptResponse:
        """Obtener el saludo inicial del Segmento 1"""
        message = self.SEGMENT_1_GREETING.get(lang, self.SEGMENT_1_GREETING["es"])
        
        return ScriptResponse(
            message=message,
            segment=ScriptSegment.S1_INICIO_HUMANO,
            can_advance=False,
            requires_confirmation=False
        )
    
    def process_segment_1(
        self,
        user_text: str,
        emotional_state: str,
        lang: str = "es"
    ) -> ScriptResponse:
        """
        Procesar respuesta en Segmento 1: Inicio humano y contención
        
        REGLA: Escuchar. No pedir datos. No avanzar.
        """
        import re
        
        self.segment_interactions += 1
        
        # Verificar si el usuario quiere avanzar
        text_lower = user_text.lower()
        wants_to_advance = any(
            re.search(pattern, text_lower)
            for pattern in self.SEGMENT_1_READY_INDICATORS
        )
        
        # Si el usuario ha compartido suficiente (mínimo 2 interacciones)
        # y quiere avanzar, permitirlo
        if wants_to_advance and self.segment_interactions >= 2:
            return self._transition_to_segment_2(lang)
        
        # Si no, seguir escuchando con respuesta empática
        responses = self.SEGMENT_1_LISTENING_RESPONSES.get(lang, self.SEGMENT_1_LISTENING_RESPONSES["es"])
        response_text = responses.get(emotional_state, responses["neutral"])
        
        # Después de 3+ interacciones, ofrecer gentilmente avanzar
        if self.segment_interactions >= 3:
            if lang == "es":
                response_text += (
                    "\n\n---\n\n"
                    "_Cuando sientas que me has contado lo esencial, "
                    "podemos pasar a conocer un poco más de tu situación. "
                    "Sin prisa._"
                )
            else:
                response_text += (
                    "\n\n---\n\n"
                    "_When you feel you've told me the essentials, "
                    "we can move on to learn a bit more about your situation. "
                    "No rush._"
                )
        
        return ScriptResponse(
            message=response_text,
            segment=ScriptSegment.S1_INICIO_HUMANO,
            can_advance=self.segment_interactions >= 2,
            requires_confirmation=False
        )
    
    def _transition_to_segment_2(self, lang: str) -> ScriptResponse:
        """Transición al Segmento 2"""
        self.current_segment = ScriptSegment.S2_ESCUCHA_PROFUNDA
        self.segment_interactions = 0
        
        if lang == "es":
            message = (
                "Gracias por compartir todo eso conmigo. 🙏\n\n"
                "Ahora entiendo mejor de dónde viene este deseo de cambio.\n\n"
                "Me gustaría conocer un poco más sobre tu situación actual, "
                "pero a tu ritmo. No hay formularios aquí, solo conversación.\n\n"
                "👉 *¿Quiénes estarían migrando contigo? ¿Vas solo/a, con pareja, con hijos?*"
            )
        else:
            message = (
                "Thank you for sharing all that with me. 🙏\n\n"
                "Now I understand better where this desire for change comes from.\n\n"
                "I'd like to learn a bit more about your current situation, "
                "but at your own pace. No forms here, just conversation.\n\n"
                "👉 *Who would be migrating with you? Are you going alone, with a partner, with children?*"
            )
        
        return ScriptResponse(
            message=message,
            segment=ScriptSegment.S2_ESCUCHA_PROFUNDA,
            can_advance=False,
            requires_confirmation=False
        )
    
    def is_visa_talk_allowed(self) -> bool:
        """Verificar si se puede hablar de visas (solo después de S7)"""
        allowed_segments = [
            ScriptSegment.S8_OPCIONES_MIGRATORIAS,
            ScriptSegment.S9_PLAN_PERSONALIZADO,
        ]
        return self.current_segment in allowed_segments
    
    def is_location_talk_allowed(self) -> bool:
        """Verificar si se puede hablar de estados/ciudades (solo después de S7)"""
        return self.is_visa_talk_allowed()
    
    def block_premature_visa_talk(self, lang: str = "es") -> ScriptResponse:
        """Respuesta cuando el usuario pregunta por visas antes de tiempo"""
        if lang == "es":
            message = (
                "Entiendo que quieres saber sobre visas, y llegaremos ahí. 🎯\n\n"
                "Pero primero necesito conocerte mejor para darte información "
                "que realmente te sirva, no respuestas genéricas.\n\n"
                "Es como ir al doctor: primero te escucha, luego receta.\n\n"
                "¿Me cuentas un poco más sobre tu situación?"
            )
        else:
            message = (
                "I understand you want to know about visas, and we'll get there. 🎯\n\n"
                "But first I need to know you better to give you information "
                "that will really help you, not generic answers.\n\n"
                "It's like going to the doctor: first they listen, then they prescribe.\n\n"
                "Can you tell me a bit more about your situation?"
            )
        
        return ScriptResponse(
            message=message,
            segment=self.current_segment,
            can_advance=False,
            requires_confirmation=False
        )


# Singleton
_script_usa = None

def get_migpal_script_usa() -> MigPALScriptUSA:
    """Obtener instancia del guion USA"""
    global _script_usa
    if _script_usa is None:
        _script_usa = MigPALScriptUSA()
    return _script_usa
