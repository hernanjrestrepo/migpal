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

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ScriptSegment(Enum):
    """Segmentos del guion MigPAL USA"""

    S1_INICIO_HUMANO = "s1_inicio_humano"  # Inicio y contención
    S2_ESCUCHA_PROFUNDA = "s2_escucha_profunda"  # Escuchar sin pedir datos
    S3_QUIENES_MIGRAN = "s3_quienes_migran"  # Familia, dependientes
    S4_SITUACION_ACTUAL = "s4_situacion_actual"  # Trabajo, ingresos
    S5_VIDA_DESEADA = "s5_vida_deseada"  # Sueños, metas
    S6_RESTRICCIONES = "s6_restricciones"  # Dinero, tiempo, docs
    S7_RESUMEN_ENTENDIMIENTO = "s7_resumen"  # Validación obligatoria
    S8_OPCIONES_MIGRATORIAS = "s8_opciones"  # SOLO después de S7
    S9_PLAN_PERSONALIZADO = "s9_plan"  # Plan final


@dataclass
class ScriptResponse:
    """Respuesta del guion"""

    message: str
    segment: ScriptSegment
    can_advance: bool = False
    buttons: list[tuple[str, str]] | None = None
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

👉 *What's happening in your life today that made you think about going to the United States?*""",
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
        },
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
            requires_confirmation=False,
        )

    def process_segment_1(self, user_text: str, emotional_state: str, lang: str = "es") -> ScriptResponse:
        """
        Procesar respuesta en Segmento 1: Inicio humano y contención

        REGLA: Escuchar. No pedir datos. No avanzar.
        """
        import re

        self.segment_interactions += 1

        # Verificar si el usuario quiere avanzar
        text_lower = user_text.lower()
        wants_to_advance = any(re.search(pattern, text_lower) for pattern in self.SEGMENT_1_READY_INDICATORS)

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
            requires_confirmation=False,
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
            requires_confirmation=False,
        )

    # =========================================================================
    # SEGMENTO 3: FAMILIA Y REALIDAD HUMANA
    # =========================================================================

    SEGMENT_3_INITIAL = {
        "es": """Cuéntame un poco más sobre eso. 👨‍👩‍👧

¿Quiénes serían? ¿Pareja, hijos, padres? ¿Edades aproximadas?

No necesito exactitud, solo contexto humano.""",
        "en": """Tell me a bit more about that. 👨‍👩‍👧

Who would they be? Partner, children, parents? Approximate ages?

I don't need exact numbers, just human context.""",
    }

    SEGMENT_3_ACKNOWLEDGMENT = {
        "es": """Gracias. Esto cambia completamente el tipo de opciones reales en Estados Unidos. 🎯

Ahora, para entender desde dónde partes:

👉 *¿Dónde vives hoy y cómo es tu situación laboral o económica actualmente?*""",
        "en": """Thank you. This completely changes the type of real options in the United States. 🎯

Now, to understand where you're starting from:

👉 *Where do you live today and what's your current work or economic situation?*""",
    }

    # Respuestas empáticas para Segmento 3
    SEGMENT_3_RESPONSES = {
        "es": {
            "solo": (
                "Entiendo, vas solo/a. 💪\n\n"
                "Eso tiene sus ventajas: más flexibilidad, menos trámites, "
                "y puedes moverte más rápido.\n\n"
                "{transition}"
            ),
            "pareja": (
                "Ir con tu pareja es un gran paso juntos. 💑\n\n"
                "Es importante que ambos estén alineados en esta decisión.\n\n"
                "{transition}"
            ),
            "hijos_pequenos": (
                "Entiendo, tienes hijos pequeños. 👶\n\n"
                "Eso es muy importante porque afecta las opciones de visa, "
                "escuelas, y el tipo de ciudad que te conviene.\n\n"
                "{transition}"
            ),
            "hijos_grandes": (
                "Hijos adolescentes o jóvenes. 📚\n\n"
                "Eso abre opciones interesantes, especialmente si están "
                "en edad de estudiar allá.\n\n"
                "{transition}"
            ),
            "familia_extendida": (
                "Llevar a padres o familia extendida es un acto de amor. ❤️\n\n"
                "También complica un poco los trámites, pero hay opciones.\n\n"
                "{transition}"
            ),
            "default": (
                "Gracias por contarme. 🙏\n\n"
                "Cada situación familiar es única y eso influye mucho "
                "en las opciones reales.\n\n"
                "{transition}"
            ),
        },
        "en": {
            "solo": (
                "I understand, you're going alone. 💪\n\n"
                "That has its advantages: more flexibility, less paperwork, "
                "and you can move faster.\n\n"
                "{transition}"
            ),
            "default": (
                "Thank you for sharing. 🙏\n\n"
                "Every family situation is unique and that greatly influences "
                "the real options.\n\n"
                "{transition}"
            ),
        },
    }

    def process_segment_3(self, user_text: str, extracted_data: dict, lang: str = "es") -> ScriptResponse:
        """
        Procesar Segmento 3: Familia y realidad humana

        REGLA: Conversación libre. Extraer datos sin formularios.
        """

        self.segment_interactions += 1
        text_lower = user_text.lower()

        # Detectar situación familiar
        family_type = self._detect_family_type(text_lower, extracted_data)

        # Obtener respuesta apropiada
        responses = self.SEGMENT_3_RESPONSES.get(lang, self.SEGMENT_3_RESPONSES["es"])
        response_template = responses.get(family_type, responses["default"])

        # Si es la primera interacción del segmento, solo escuchar
        if self.segment_interactions == 1:
            transition = self.SEGMENT_3_ACKNOWLEDGMENT.get(lang, self.SEGMENT_3_ACKNOWLEDGMENT["es"])
            response_text = response_template.format(transition=transition)

            return ScriptResponse(
                message=response_text,
                segment=ScriptSegment.S3_QUIENES_MIGRAN,
                can_advance=True,
                requires_confirmation=False,
            )

        # Si ya respondió sobre familia, transicionar a Segmento 4
        return self._transition_to_segment_4(lang)

    def _detect_family_type(self, text: str, extracted: dict) -> str:
        """Detectar tipo de situación familiar"""
        import re

        # Patrones para detectar situación familiar
        if re.search(r"solo|sola|solter[oa]|sin familia|nadie", text):
            return "solo"

        if re.search(r"pareja|esposa|esposo|novi[oa]|marido|mujer", text):
            if re.search(r"hijo|hija|niño|niña|bebé", text):
                # Tiene pareja e hijos
                if re.search(r"\b[0-5]\b|pequeño|bebé|añitos", text):
                    return "hijos_pequenos"
                elif re.search(r"\b(1[0-9]|20)\b|adolescente|joven|universidad", text):
                    return "hijos_grandes"
                return "hijos_pequenos"  # Default si no se detecta edad
            return "pareja"

        if re.search(r"hijo|hija|niño|niña", text):
            if re.search(r"\b[0-5]\b|pequeño|bebé", text):
                return "hijos_pequenos"
            return "hijos_grandes"

        if re.search(r"padre|madre|papá|mamá|abuelo|abuela|hermano|hermana", text):
            return "familia_extendida"

        return "default"

    def _transition_to_segment_4(self, lang: str) -> ScriptResponse:
        """Transición al Segmento 4: Situación actual"""
        self.current_segment = ScriptSegment.S4_SITUACION_ACTUAL
        self.segment_interactions = 0

        if lang == "es":
            message = (
                "Perfecto, ya tengo una imagen más clara. 📝\n\n"
                "Ahora cuéntame sobre tu situación actual:\n\n"
                "👉 *¿A qué te dedicas? ¿Cuántos años de experiencia tienes? "
                "¿Cómo está tu situación económica hoy?*"
            )
        else:
            message = (
                "Perfect, I now have a clearer picture. 📝\n\n"
                "Now tell me about your current situation:\n\n"
                "👉 *What do you do for work? How many years of experience do you have? "
                "How's your economic situation today?*"
            )

        return ScriptResponse(
            message=message,
            segment=ScriptSegment.S4_SITUACION_ACTUAL,
            can_advance=False,
            requires_confirmation=False,
        )

    # =========================================================================
    # SEGMENTO 4: VIDA DESEADA EN USA (ANTES QUE VISA)
    # =========================================================================

    SEGMENT_4_INITIAL = {
        "es": """Antes de hablar de visas, pensemos en la vida. ✨

Imagináte dentro de 3 a 5 años en Estados Unidos y que las cosas salieron bien.

👉 *¿Cómo te gustaría que fuera tu día a día allí?*

Por ejemplo:
– tipo de trabajo o actividad
– ciudad grande vs. ciudad mediana
– comunidad latina importante o no
– estabilidad vs. crecimiento
– clima y ritmo de vida

Respóndeme como te salga. Yo luego lo organizo.""",
        "en": """Before talking about visas, let's think about life. ✨

Imagine yourself 3 to 5 years from now in the United States, and things worked out well.

👉 *What would you like your day-to-day life to be like there?*

For example:
– type of work or activity
– big city vs. medium city
– important Latino community or not
– stability vs. growth
– climate and pace of life

Answer however it comes to you. I'll organize it later.""",
    }

    # Respuestas empáticas para Segmento 4
    SEGMENT_4_RESPONSES = {
        "es": {
            "career_focused": (
                "Me encanta esa visión profesional. 💼\n\n"
                "Quieres crecer en tu carrera y eso es muy valioso. "
                "USA tiene muchas oportunidades para eso.\n\n"
                "{transition}"
            ),
            "family_focused": (
                "Eso es hermoso. 👨‍👩‍👧\n\n"
                "Priorizar la familia y su bienestar es una motivación muy poderosa. "
                "Hay lugares en USA perfectos para eso.\n\n"
                "{transition}"
            ),
            "stability_focused": (
                "La estabilidad es fundamental. 🏠\n\n"
                "Después de tanta incertidumbre, querer paz y seguridad "
                "es completamente válido.\n\n"
                "{transition}"
            ),
            "adventure_focused": (
                "¡Me gusta ese espíritu! 🚀\n\n"
                "Quieres crecer, explorar, y aprovechar al máximo la experiencia. "
                "USA tiene mucho que ofrecer.\n\n"
                "{transition}"
            ),
            "balanced": (
                "Un equilibrio entre trabajo y vida personal. ⚖️\n\n"
                "Eso es sabio. No todo es trabajar, también hay que vivir.\n\n"
                "{transition}"
            ),
            "default": (
                "Gracias por compartir esa visión. 🙏\n\n"
                "Cada sueño es único y eso me ayuda a entender qué opciones "
                "realmente te servirían.\n\n"
                "{transition}"
            ),
        },
        "en": {
            "default": (
                "Thank you for sharing that vision. 🙏\n\n"
                "Every dream is unique and this helps me understand what options "
                "would really work for you.\n\n"
                "{transition}"
            ),
        },
    }

    SEGMENT_4_TRANSITION = {
        "es": """Ahora, para ser realistas, hablemos de recursos. 💰

👉 *¿Con cuánto dinero cuentas aproximadamente para este proyecto?*

(Ahorros, posibles préstamos, apoyo familiar... no necesito cifras exactas, solo un rango)

Y en términos de tiempo: *¿hay alguna urgencia o tienes flexibilidad?*""",
        "en": """Now, to be realistic, let's talk about resources. 💰

👉 *Approximately how much money do you have for this project?*

(Savings, possible loans, family support... I don't need exact figures, just a range)

And in terms of time: *is there any urgency or do you have flexibility?*""",
    }

    def process_segment_4(self, user_text: str, extracted_data: dict, lang: str = "es") -> ScriptResponse:
        """
        Procesar Segmento 4: Vida deseada en USA

        REGLA: Antes de hablar de visas, pensemos en la vida.
        """

        self.segment_interactions += 1
        text_lower = user_text.lower()

        # Detectar tipo de vida deseada
        life_type = self._detect_life_type(text_lower)

        # Obtener respuesta apropiada
        responses = self.SEGMENT_4_RESPONSES.get(lang, self.SEGMENT_4_RESPONSES["es"])
        response_template = responses.get(life_type, responses["default"])

        # Transición al Segmento 5 (Restricciones)
        transition = self.SEGMENT_4_TRANSITION.get(lang, self.SEGMENT_4_TRANSITION["es"])
        response_text = response_template.format(transition=transition)

        return ScriptResponse(
            message=response_text,
            segment=ScriptSegment.S5_VIDA_DESEADA,
            can_advance=True,
            requires_confirmation=False,
        )

    def _detect_life_type(self, text: str) -> str:
        """Detectar tipo de vida deseada"""
        import re

        # Patrones para detectar enfoque de vida
        if re.search(r"carrera|profesional|crecer|empresa|negocio|emprender|startup", text):
            return "career_focused"

        if re.search(r"familia|hijos|escuela|segur[oa]|tranquil[oa]|niños", text):
            return "family_focused"

        if re.search(r"estable|estabilidad|paz|calm[oa]|sin estrés", text):
            return "stability_focused"

        if re.search(r"aventura|explorar|viajar|conocer|experiencia|nuevo", text):
            return "adventure_focused"

        if re.search(r"equilibrio|balance|trabajo.*vida|vida.*trabajo", text):
            return "balanced"

        return "default"

    def _transition_to_segment_5(self, lang: str) -> ScriptResponse:
        """Transición al Segmento 5: Restricciones"""
        self.current_segment = ScriptSegment.S5_VIDA_DESEADA
        self.segment_interactions = 0

        message = self.SEGMENT_4_TRANSITION.get(lang, self.SEGMENT_4_TRANSITION["es"])

        return ScriptResponse(
            message=message,
            segment=ScriptSegment.S5_VIDA_DESEADA,
            can_advance=False,
            requires_confirmation=False,
        )

    # =========================================================================
    # SEGMENTO 5: RESTRICCIONES REALES + RESUMEN OBLIGATORIO
    # =========================================================================

    SEGMENT_5_RESOURCES_QUESTION = {
        "es": """¿Con cuánto dinero cuentas aproximadamente para este proyecto? 💰

(Ahorros, posibles préstamos, apoyo familiar... no necesito cifras exactas, solo un rango)

Y en términos de tiempo: *¿hay alguna urgencia o tienes flexibilidad?*""",
        "en": """Approximately how much money do you have for this project? 💰

(Savings, possible loans, family support... I don't need exact figures, just a range)

And in terms of time: *is there any urgency or do you have flexibility?*""",
    }

    SEGMENT_5_SUMMARY_INTRO = {
        "es": """Gracias. Ahora déjame detenerme un momento. 📝

📌 *RESUMEN DE LO QUE ENTIENDO HASTA AHORA:*""",
        "en": """Thank you. Now let me stop for a moment. 📝

📌 *SUMMARY OF WHAT I UNDERSTAND SO FAR:*""",
    }

    SEGMENT_5_CONFIRMATION_QUESTION = {
        "es": """

👉 *¿Esto refleja bien tu situación o cambiarías algo importante?*""",
        "en": """

👉 *Does this reflect your situation well or would you change something important?*""",
    }

    # Respuestas para confirmación/corrección del resumen
    SEGMENT_5_RESPONSES = {
        "es": {
            "confirmed": (
                "¡Perfecto! Ahora sí puedo darte recomendaciones personalizadas. 🎯\n\n"
                "Basándome en tu perfil, voy a analizar las mejores opciones para ti.\n\n"
                "Dame un momento..."
            ),
            "correction": (
                "Entendido, gracias por la aclaración. 🙏\n\n"
                "Es importante que tenga la información correcta.\n\n"
                "¿Qué parte te gustaría corregir o agregar?"
            ),
            "partial": (
                "Ok, veo que hay algo que ajustar. 📝\n\n"
                "Cuéntame qué cambiarías y actualizo mi entendimiento."
            ),
        },
        "en": {
            "confirmed": (
                "Perfect! Now I can give you personalized recommendations. 🎯\n\n"
                "Based on your profile, I'll analyze the best options for you.\n\n"
                "Give me a moment..."
            ),
            "correction": (
                "Understood, thanks for the clarification. 🙏\n\n"
                "It's important that I have the correct information.\n\n"
                "What part would you like to correct or add?"
            ),
        },
    }

    def generate_understanding_summary(self, understanding: dict, lang: str = "es") -> str:
        """
        Generar el resumen de entendimiento obligatorio.

        REGLA: NO avanzar hasta que el usuario confirme o corrija.
        """
        intro = self.SEGMENT_5_SUMMARY_INTRO.get(lang, self.SEGMENT_5_SUMMARY_INTRO["es"])
        question = self.SEGMENT_5_CONFIRMATION_QUESTION.get(lang, self.SEGMENT_5_CONFIRMATION_QUESTION["es"])

        # Construir resumen dinámico
        summary_parts = []

        # 1. Por qué quieres irte
        motivation = understanding.get("deep_motivation", "")
        if motivation:
            if lang == "es":
                summary_parts.append(
                    f"🎯 *Por qué quieres irte:* {motivation[:100]}..."
                    if len(motivation) > 100
                    else f"🎯 *Por qué quieres irte:* {motivation}"
                )
            else:
                summary_parts.append(
                    f"🎯 *Why you want to leave:* {motivation[:100]}..."
                    if len(motivation) > 100
                    else f"🎯 *Why you want to leave:* {motivation}"
                )

        # 2. Quiénes migrarían
        family = understanding.get("family_members", [])
        migrating_alone = understanding.get("migrating_alone", None)
        if migrating_alone:
            if lang == "es":
                summary_parts.append("👤 *Quiénes migran:* Solo/a")
            else:
                summary_parts.append("👤 *Who migrates:* Alone")
        elif family:
            family_desc = ", ".join(
                [f"{m.get('type', 'familiar')} ({m.get('age', '?')} años)" for m in family]
            )
            if lang == "es":
                summary_parts.append(f"👨‍👩‍👧 *Quiénes migran:* Con familia - {family_desc}")
            else:
                summary_parts.append(f"👨‍👩‍👧 *Who migrates:* With family - {family_desc}")

        # 3. Situación actual
        profession = understanding.get("current_profession", "")
        years = understanding.get("years_experience", "")
        if profession:
            prof_text = f"{profession}"
            if years:
                prof_text += f" ({years} años exp.)"
            if lang == "es":
                summary_parts.append(f"💼 *Profesión:* {prof_text}")
            else:
                summary_parts.append(f"💼 *Profession:* {prof_text}")

        # 4. Vida deseada
        lifestyle = understanding.get("desired_lifestyle", "")
        if lifestyle:
            if lang == "es":
                summary_parts.append(
                    f"✨ *Vida deseada:* {lifestyle[:80]}..."
                    if len(lifestyle) > 80
                    else f"✨ *Vida deseada:* {lifestyle}"
                )
            else:
                summary_parts.append(
                    f"✨ *Desired life:* {lifestyle[:80]}..."
                    if len(lifestyle) > 80
                    else f"✨ *Desired life:* {lifestyle}"
                )

        # 5. Recursos y restricciones
        savings = understanding.get("available_savings", "")
        urgency = understanding.get("timeline_urgency", "")
        if savings or urgency:
            constraints = []
            if savings:
                constraints.append(f"${savings:,}" if isinstance(savings, int) else str(savings))
            if urgency:
                urgency_text = {
                    "urgent": "urgente" if lang == "es" else "urgent",
                    "flexible": "flexible",
                    "no_rush": "sin prisa" if lang == "es" else "no rush",
                }.get(urgency, urgency)
                constraints.append(urgency_text)
            if lang == "es":
                summary_parts.append(f"💰 *Recursos/Tiempo:* {', '.join(constraints)}")
            else:
                summary_parts.append(f"💰 *Resources/Time:* {', '.join(constraints)}")

        # Construir mensaje completo
        summary_body = (
            "\n".join(summary_parts)
            if summary_parts
            else ("(Información pendiente)" if lang == "es" else "(Information pending)")
        )

        return f"{intro}\n\n{summary_body}{question}"

    def process_segment_5(
        self, user_text: str, understanding: dict, is_confirmation_phase: bool, lang: str = "es"
    ) -> ScriptResponse:
        """
        Procesar Segmento 5: Restricciones + Resumen Obligatorio

        REGLA CRÍTICA: NO avanzar hasta que el usuario confirme o corrija.
        """

        text_lower = user_text.lower()

        # Si estamos en fase de confirmación del resumen
        if is_confirmation_phase:
            return self._process_summary_confirmation(text_lower, lang)

        # Si no, estamos recopilando restricciones
        # Generar el resumen obligatorio
        summary = self.generate_understanding_summary(understanding, lang)

        return ScriptResponse(
            message=summary,
            segment=ScriptSegment.S7_RESUMEN_ENTENDIMIENTO,
            can_advance=False,  # BLOQUEANTE hasta confirmación
            requires_confirmation=True,
            buttons=(
                [
                    ("✅ Sí, es correcto", "confirm_summary"),
                    ("✏️ Quiero corregir algo", "correct_summary"),
                    ("➕ Quiero agregar algo", "add_to_summary"),
                ]
                if lang == "es"
                else [
                    ("✅ Yes, it's correct", "confirm_summary"),
                    ("✏️ I want to correct something", "correct_summary"),
                    ("➕ I want to add something", "add_to_summary"),
                ]
            ),
        )

    def _process_summary_confirmation(self, text: str, lang: str) -> ScriptResponse:
        """
        Procesar la confirmación/corrección del resumen.

        REGLA: Solo avanzar si el usuario confirma explícitamente.
        """
        responses = self.SEGMENT_5_RESPONSES.get(lang, self.SEGMENT_5_RESPONSES["es"])

        # Detectar confirmación
        confirmation_patterns = [
            r"sí|si|yes|correcto|exacto|perfecto|bien|ok|está bien",
            r"confirm",
            r"así es|eso es|exactamente",
        ]

        is_confirmed = any(__import__("re").search(pattern, text) for pattern in confirmation_patterns)

        # Detectar corrección
        correction_patterns = [
            r"no|cambiar|corregir|agregar|falta|incorrecto",
            r"en realidad|pero|aunque",
        ]

        is_correction = any(__import__("re").search(pattern, text) for pattern in correction_patterns)

        if is_confirmed and not is_correction:
            # ¡CONFIRMADO! Ahora sí podemos avanzar
            return ScriptResponse(
                message=responses["confirmed"],
                segment=ScriptSegment.S8_OPCIONES_MIGRATORIAS,
                can_advance=True,
                requires_confirmation=False,
            )
        elif is_correction:
            # Necesita corrección - NO avanzar
            return ScriptResponse(
                message=responses["correction"],
                segment=ScriptSegment.S7_RESUMEN_ENTENDIMIENTO,
                can_advance=False,
                requires_confirmation=True,
            )
        else:
            # Respuesta ambigua - pedir clarificación
            return ScriptResponse(
                message=responses.get("partial", responses["correction"]),
                segment=ScriptSegment.S7_RESUMEN_ENTENDIMIENTO,
                can_advance=False,
                requires_confirmation=True,
            )

    # =========================================================================
    # SEGMENTO 6: INTRODUCCIÓN AL SISTEMA MIGRATORIO USA (SIN RECOMENDAR)
    # =========================================================================

    SEGMENT_6_INTRO = {
        "es": """Perfecto. Gracias por confirmarlo. ✅

Estados Unidos tiene muchos caminos migratorios, pero no todos sirven para todas las personas.

⚠️ *Elegir mal una visa puede costar años y mucho dinero.*

Por eso, primero analizamos tu perfil humano y profesional, y solo después vemos qué opciones migratorias tienen sentido *en la vida real*, no en teoría.

👉 *¿Te parece si ahora revisamos, con calma, qué caminos podrían ser viables para ti en USA?*""",
        "en": """Perfect. Thanks for confirming. ✅

The United States has many immigration paths, but not all of them work for everyone.

⚠️ *Choosing the wrong visa can cost years and a lot of money.*

That's why we first analyze your human and professional profile, and only then look at what immigration options make sense *in real life*, not in theory.

👉 *Would you like us to now review, calmly, what paths could be viable for you in the USA?*""",
    }

    SEGMENT_6_RESPONSES = {
        "es": {
            "ready": (
                "¡Excelente! Vamos a ello. 🚀\n\n"
                "Basado en todo lo que me has contado, voy a analizar "
                "las opciones que realmente podrían funcionar para ti.\n\n"
                "Dame un momento mientras proceso tu perfil..."
            ),
            "not_ready": (
                "Entiendo, no hay prisa. 🙏\n\n"
                "Cuando estés listo/a para explorar las opciones, "
                "solo dímelo. Estaré aquí.\n\n"
                "¿Hay algo más que quieras contarme o preguntar antes?"
            ),
            "questions": (
                "Claro, es normal tener preguntas antes de avanzar. 🤔\n\n" "¿Qué te gustaría saber?"
            ),
        },
        "en": {
            "ready": (
                "Excellent! Let's do it. 🚀\n\n"
                "Based on everything you've told me, I'm going to analyze "
                "the options that could really work for you.\n\n"
                "Give me a moment while I process your profile..."
            ),
            "not_ready": (
                "I understand, no rush. 🙏\n\n"
                "When you're ready to explore the options, "
                "just let me know. I'll be here.\n\n"
                "Is there anything else you'd like to tell me or ask before?"
            ),
        },
    }

    def get_segment_6_intro(self, lang: str = "es") -> ScriptResponse:
        """
        Obtener la introducción al sistema migratorio.

        Se muestra DESPUÉS de confirmar el resumen, ANTES de recomendar visas.
        """
        message = self.SEGMENT_6_INTRO.get(lang, self.SEGMENT_6_INTRO["es"])

        return ScriptResponse(
            message=message,
            segment=ScriptSegment.S8_OPCIONES_MIGRATORIAS,
            can_advance=False,
            requires_confirmation=True,  # Necesita consentimiento para analizar visas
            buttons=(
                [
                    ("✅ Sí, vamos a verlo", "start_visa_analysis"),
                    ("🤔 Tengo preguntas primero", "questions_first"),
                    ("⏸️ Prefiero esperar", "wait"),
                ]
                if lang == "es"
                else [
                    ("✅ Yes, let's see it", "start_visa_analysis"),
                    ("🤔 I have questions first", "questions_first"),
                    ("⏸️ I prefer to wait", "wait"),
                ]
            ),
        )

    def process_segment_6(self, user_text: str, lang: str = "es") -> ScriptResponse:
        """
        Procesar respuesta del Segmento 6.

        REGLA: Solo con consentimiento se pasa a análisis de visas.
        """
        import re

        text_lower = user_text.lower()
        responses = self.SEGMENT_6_RESPONSES.get(lang, self.SEGMENT_6_RESPONSES["es"])

        # Detectar si está listo para continuar
        ready_patterns = [
            r"sí|si|yes|vamos|dale|ok|claro|por supuesto|adelante",
            r"quiero ver|muéstrame|análisis|opciones",
        ]

        is_ready = any(re.search(pattern, text_lower) for pattern in ready_patterns)

        # Detectar si tiene preguntas
        question_patterns = [
            r"pregunta|duda|\?|qué|cómo|cuál|cuánto",
        ]

        has_questions = any(re.search(pattern, text_lower) for pattern in question_patterns)

        # Detectar si prefiere esperar
        wait_patterns = [
            r"no|esperar|después|luego|todavía no|aún no",
        ]

        wants_to_wait = any(re.search(pattern, text_lower) for pattern in wait_patterns)

        if is_ready and not wants_to_wait:
            # ¡Listo para análisis de visas!
            return ScriptResponse(
                message=responses["ready"],
                segment=ScriptSegment.S8_OPCIONES_MIGRATORIAS,
                can_advance=True,
                requires_confirmation=False,
            )
        elif has_questions:
            return ScriptResponse(
                message=responses.get("questions", responses["not_ready"]),
                segment=ScriptSegment.S8_OPCIONES_MIGRATORIAS,
                can_advance=False,
                requires_confirmation=True,
            )
        else:
            # Prefiere esperar
            return ScriptResponse(
                message=responses["not_ready"],
                segment=ScriptSegment.S8_OPCIONES_MIGRATORIAS,
                can_advance=False,
                requires_confirmation=True,
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
            message=message, segment=self.current_segment, can_advance=False, requires_confirmation=False
        )


# Singleton
_script_usa = None


def get_migpal_script_usa() -> MigPALScriptUSA:
    """Obtener instancia del guion USA"""
    global _script_usa
    if _script_usa is None:
        _script_usa = MigPALScriptUSA()
    return _script_usa
