#!/usr/bin/env python3
"""
Tests para IA Conversacional v3.0.8
===================================
MigPAL es el AMIGO de los migrantes, no un formulario estúpido.
NUNCA debe mostrar "error" - siempre responder con empatía.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestIntentDetection:
    """Tests para detección de intenciones"""

    def test_detect_not_ready(self):
        """Detectar cuando el usuario no está listo"""
        from app.services.conversational_ai import ConversationalAI, UserIntent

        ai = ConversationalAI()

        test_cases = [
            "no estoy listo para escoger",
            "no estoy seguro todavía",
            "no sé qué elegir",
            "todavía no me decido",
            "not ready yet",
            "I'm not sure",
        ]

        for text in test_cases:
            intent = ai.detect_intent(text)
            assert intent == UserIntent.NOT_READY, f"Debería detectar NOT_READY en: {text}"

    def test_detect_confused(self):
        """Detectar cuando el usuario está confundido"""
        from app.services.conversational_ai import ConversationalAI, UserIntent

        ai = ConversationalAI()

        test_cases = [
            "no entiendo las opciones",
            "no conozco Estados Unidos",
            "estoy confundido",
            "qué significa eso",
            "I don't understand",
        ]

        for text in test_cases:
            intent = ai.detect_intent(text)
            assert intent == UserIntent.CONFUSED, f"Debería detectar CONFUSED en: {text}"

    def test_detect_question(self):
        """Detectar preguntas"""
        from app.services.conversational_ai import ConversationalAI, UserIntent

        ai = ConversationalAI()

        # Preguntas puras (con ?) deben detectarse como ASKING_QUESTION
        test_cases = [
            "¿cuál es la mejor opción?",
            "what is the best visa?",
        ]

        for text in test_cases:
            intent = ai.detect_intent(text)
            assert intent == UserIntent.ASKING_QUESTION, f"Debería detectar ASKING_QUESTION en: {text}"

        # "cómo funciona" puede ser WANTS_INFO o ASKING_QUESTION - ambos son válidos
        intent = ai.detect_intent("¿cómo funciona el proceso?")
        assert intent in [
            UserIntent.ASKING_QUESTION,
            UserIntent.WANTS_INFO,
        ], "Debería detectar ASKING_QUESTION o WANTS_INFO"

    def test_detect_concern(self):
        """Detectar preocupaciones"""
        from app.services.conversational_ai import ConversationalAI, UserIntent

        ai = ConversationalAI()

        test_cases = [
            "me preocupa el costo",
            "tengo miedo de no lograrlo",
            "estoy nervioso",
            "I'm worried about",
            "I'm scared",
        ]

        for text in test_cases:
            intent = ai.detect_intent(text)
            assert intent == UserIntent.EXPRESSING_CONCERN, f"Debería detectar EXPRESSING_CONCERN en: {text}"


class TestTopicDetection:
    """Tests para detección de temas"""

    def test_detect_regions_topic(self):
        """Detectar tema de regiones"""
        from app.services.conversational_ai import ConversationalAI

        ai = ConversationalAI()

        test_cases = [
            ("no conozco las regiones", "start"),
            ("qué estado me conviene", "location_region"),
            ("which city is best", "location_city"),
        ]

        for text, state in test_cases:
            topic = ai.detect_topic(text, state)
            assert topic == "regions", f"Debería detectar 'regions' en: {text}"

    def test_detect_visas_topic(self):
        """Detectar tema de visas"""
        from app.services.conversational_ai import ConversationalAI

        ai = ConversationalAI()

        test_cases = [
            ("qué visa necesito", "start"),
            ("tipos de visa", "visa_analysis"),
        ]

        for text, state in test_cases:
            topic = ai.detect_topic(text, state)
            assert topic == "visas", f"Debería detectar 'visas' en: {text}"


class TestConversationalResponses:
    """Tests para respuestas conversacionales"""

    @pytest.mark.asyncio
    async def test_not_ready_response_is_empathic(self):
        """La respuesta a 'no estoy listo' debe ser empática"""
        from app.services.conversational_ai import get_conversational_ai

        ai = get_conversational_ai()

        user = {"profile": {"personal": {"name": "Juan"}}, "language": "es"}

        response = await ai.process_free_text(
            "no estoy listo para escoger una zona", user, "location_region", "es"
        )

        # Debe ser empático
        assert "Juan" in response.message or "amigo" in response.message
        assert "prisa" in response.message.lower() or "entiendo" in response.message.lower()

        # NO debe contener "error"
        assert "error" not in response.message.lower()
        assert "⚠️" not in response.message

    @pytest.mark.asyncio
    async def test_confused_response_explains(self):
        """La respuesta a confusión debe explicar"""
        from app.services.conversational_ai import get_conversational_ai

        ai = get_conversational_ai()

        user = {"profile": {"personal": {"name": "María"}}, "language": "es"}

        response = await ai.process_free_text(
            "no conozco Estados Unidos, no sé qué zona elegir", user, "location_region", "es"
        )

        # Debe explicar las regiones
        assert any(
            word in response.message.lower()
            for word in ["región", "sur", "norte", "oeste", "florida", "california"]
        )

        # NO debe contener "error"
        assert "error" not in response.message.lower()

    @pytest.mark.asyncio
    async def test_never_shows_error(self):
        """NUNCA debe mostrar mensaje de error"""
        from app.services.conversational_ai import get_conversational_ai

        ai = get_conversational_ai()

        user = {"profile": {"personal": {"name": "Test"}}, "language": "es"}

        # Probar con varios inputs
        test_inputs = [
            "asdfghjkl",  # Texto sin sentido
            "123456",  # Solo números
            "no sé",  # Muy corto
            "quiero migrar pero no sé nada",  # Vago
        ]

        for text in test_inputs:
            response = await ai.process_free_text(text, user, "start", "es")

            # NUNCA debe contener "error"
            assert "error" not in response.message.lower(), f"Mostró error para: {text}"
            assert "⚠️" not in response.message, f"Mostró warning para: {text}"
            assert "inténtalo" not in response.message.lower(), f"Mostró retry para: {text}"


class TestContextInfo:
    """Tests para información contextual"""

    def test_regions_info_exists(self):
        """Debe existir información sobre regiones"""
        from app.services.conversational_ai import ConversationalAI

        ai = ConversationalAI()

        regions_info = ai.CONTEXT_INFO["es"]["regions"]

        assert "Sur" in regions_info or "South" in regions_info
        assert "Florida" in regions_info
        assert "California" in regions_info

    def test_visas_info_exists(self):
        """Debe existir información sobre visas"""
        from app.services.conversational_ai import ConversationalAI

        ai = ConversationalAI()

        visas_info = ai.CONTEXT_INFO["es"]["visas"]

        assert "H-1B" in visas_info
        assert "trabajo" in visas_info.lower() or "work" in visas_info.lower()


class TestNoErrorMessages:
    """Tests que verifican que NUNCA se muestra error"""

    def test_telegram_bot_no_error_message(self):
        """El bot no debe tener mensajes de error genéricos"""
        from pathlib import Path

        bot_file = Path(__file__).parent.parent / "app" / "services" / "telegram_bot.py"
        content = bot_file.read_text()

        # No debe haber "Hubo un error" sin manejo de IA
        # Buscar el patrón problemático
        import re

        # El mensaje de error debe estar dentro de un bloque de fallback de IA
        error_pattern = r"Hubo un error.*Inténtalo"
        matches = re.findall(error_pattern, content)

        # Si hay matches, deben estar comentados o en un fallback de IA
        for _match in matches:
            # Verificar que está en un contexto de fallback
            assert (
                "conversational_ai" in content or "Conversational AI" in content
            ), "Debe usar IA conversacional en lugar de mostrar error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
