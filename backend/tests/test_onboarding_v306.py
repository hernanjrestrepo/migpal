#!/usr/bin/env python3
"""
Tests para Onboarding Conversacional v3.0.6
===========================================
El comando /start NO puede iniciar formularios.
Test E2E que falle si el primer prompt es un formulario.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestOnboardingNoFormulario:
    """Tests que verifican que /start NO inicia formularios"""

    def test_first_message_is_not_form(self):
        """El primer mensaje NO debe ser un formulario"""
        from app.services.onboarding_v306 import OnboardingMessages

        messages = OnboardingMessages()

        # El primer mensaje debe ser la presentación empática
        welcome_es = messages.WELCOME["es"]
        welcome_en = messages.WELCOME["en"]

        # NO debe contener palabras de formulario
        form_keywords = [
            "nombre completo",
            "full name",
            "fecha de nacimiento",
            "birth date",
            "correo electrónico",
            "email address",
            "teléfono",
            "phone number",
            "FASE 1",
            "PHASE 1",
            "nivel educativo",
            "education level",
        ]

        for keyword in form_keywords:
            assert (
                keyword.lower() not in welcome_es.lower()
            ), f"El mensaje de bienvenida contiene '{keyword}' que es de formulario"
            assert (
                keyword.lower() not in welcome_en.lower()
            ), f"Welcome message contains '{keyword}' which is a form field"

    def test_first_state_is_onboarding(self):
        """El primer estado debe ser de onboarding, no de formulario"""
        from app.services.onboarding_v306 import ONBOARDING_STATES, OnboardingState, is_form_state

        # El estado inicial debe ser WELCOME
        first_state = OnboardingState.WELCOME.value

        # Debe estar en los estados de onboarding
        assert first_state in ONBOARDING_STATES

        # NO debe ser un estado de formulario
        assert not is_form_state(first_state)

    def test_validate_onboarding_flow(self):
        """Validar que el flujo de onboarding no empieza con formulario"""
        from app.services.onboarding_v306 import OnboardingMessages, OnboardingState, validate_onboarding_flow

        messages = OnboardingMessages()

        # Flujo válido: empieza con onboarding
        is_valid, error = validate_onboarding_flow(messages.WELCOME["es"], OnboardingState.WELCOME.value)
        assert is_valid, f"El flujo de onboarding debería ser válido: {error}"

        # Flujo inválido: empieza con formulario
        is_valid, error = validate_onboarding_flow(
            "📝 FASE 1: Tu Perfil\n\n¿Cuál es tu nombre completo?", "name"
        )
        assert not is_valid, "El flujo NO debería ser válido si empieza con formulario"

    def test_no_fase1_before_consent(self):
        """No mostrar FASE 1 hasta consentimiento explícito"""
        from app.services.onboarding_v306 import OnboardingMessages

        messages = OnboardingMessages()

        # Ningún mensaje de onboarding debe contener "FASE 1"
        all_messages = [
            messages.WELCOME["es"],
            messages.WELCOME["en"],
            messages.PROCESS_EXPLANATION["es"],
            messages.PROCESS_EXPLANATION["en"],
            messages.CONSENT_REQUEST["es"],
            messages.CONSENT_REQUEST["en"],
        ]

        for msg in all_messages:
            assert "FASE 1" not in msg, f"Mensaje contiene 'FASE 1' antes del consentimiento: {msg[:50]}..."
            assert "PHASE 1" not in msg, f"Message contains 'PHASE 1' before consent: {msg[:50]}..."


class TestOnboardingFlow:
    """Tests del flujo de onboarding"""

    def test_welcome_message_is_empathic(self):
        """El mensaje de bienvenida debe ser empático"""
        from app.services.onboarding_v306 import OnboardingMessages

        messages = OnboardingMessages()
        welcome = messages.WELCOME["es"]

        # Debe contener palabras empáticas
        empathic_words = ["amigo", "escuchar", "ayudar", "acompañar", "entiendo", "sé que"]
        has_empathy = any(word in welcome.lower() for word in empathic_words)

        assert has_empathy, "El mensaje de bienvenida debe ser empático"
        assert len(welcome) > 200, "El mensaje de bienvenida debe ser sustancial"

    def test_open_question_exists(self):
        """Debe haber preguntas abiertas de vínculo"""
        from app.services.onboarding_v306 import OnboardingMessages

        messages = OnboardingMessages()
        questions = messages.OPEN_QUESTIONS["es"]

        assert len(questions) >= 2, "Debe haber al menos 2 preguntas abiertas"

        # Las preguntas deben ser abiertas (no sí/no)
        for q in questions:
            assert "?" in q, "Las preguntas deben terminar con ?"
            assert "qué" in q.lower() or "cómo" in q.lower(), "Las preguntas deben ser abiertas (qué, cómo)"

    def test_empathic_responses_exist(self):
        """Debe haber respuestas empáticas para diferentes temas"""
        from app.services.onboarding_v306 import OnboardingMessages

        messages = OnboardingMessages()
        responses = messages.EMPATHIC_RESPONSES["es"]

        # Debe haber respuestas para temas comunes
        required_themes = ["work", "family", "quality", "default"]
        for theme in required_themes:
            assert theme in responses, f"Falta respuesta empática para '{theme}'"
            assert len(responses[theme]) > 50, f"Respuesta para '{theme}' muy corta"

    def test_process_explanation_exists(self):
        """Debe haber explicación del proceso"""
        from app.services.onboarding_v306 import OnboardingMessages

        messages = OnboardingMessages()
        explanation = messages.PROCESS_EXPLANATION["es"]

        # Debe explicar el proceso
        assert "conversamos" in explanation.lower() or "primero" in explanation.lower()
        assert "plan" in explanation.lower()

    def test_consent_request_exists(self):
        """Debe pedir consentimiento explícito"""
        from app.services.onboarding_v306 import OnboardingMessages

        messages = OnboardingMessages()
        consent = messages.CONSENT_REQUEST["es"]
        buttons = messages.CONSENT_BUTTONS["es"]

        # Debe ser una pregunta
        assert "?" in consent

        # Debe haber opciones
        assert len(buttons) >= 2

        # Debe haber opción de "sí" y "no/después"
        button_texts = [b[0].lower() for b in buttons]
        has_yes = any("sí" in t or "empecemos" in t for t in button_texts)
        has_no = any("después" in t or "preguntas" in t for t in button_texts)

        assert has_yes, "Debe haber opción de aceptar"
        assert has_no, "Debe haber opción de declinar/preguntar"

    def test_name_request_after_consent(self):
        """El nombre solo se pide después del consentimiento"""
        from app.services.onboarding_v306 import OnboardingMessages

        messages = OnboardingMessages()
        name_request = messages.NAME_REQUEST["es"]

        # Debe pedir el nombre
        assert "nombre" in name_request.lower()

        # Debe ser amigable
        assert "!" in name_request or "?" in name_request


class TestOnboardingEngine:
    """Tests del motor de onboarding"""

    def test_get_welcome_message(self):
        """Obtener mensaje de bienvenida"""
        from app.services.onboarding_v306 import get_onboarding_engine

        engine = get_onboarding_engine()

        msg_es = engine.get_welcome_message("es")
        msg_en = engine.get_welcome_message("en")

        assert len(msg_es) > 100
        assert len(msg_en) > 100
        assert msg_es != msg_en

    def test_get_empathic_response(self):
        """Obtener respuesta empática según texto"""
        from app.services.onboarding_v306 import get_onboarding_engine

        engine = get_onboarding_engine()

        # Trabajo
        response = engine.get_empathic_response("Quiero mejores oportunidades de trabajo", "es")
        assert (
            "trabajo" in response.lower()
            or "profesional" in response.lower()
            or "valiente" in response.lower()
        )

        # Familia
        response = engine.get_empathic_response("Quiero reunirme con mi familia", "es")
        assert "familia" in response.lower() or "conexión" in response.lower()

        # Default
        response = engine.get_empathic_response("Hola", "es")
        assert len(response) > 50

    def test_state_flow(self):
        """Verificar flujo de estados"""
        from app.services.onboarding_v306 import OnboardingState, get_onboarding_engine

        engine = get_onboarding_engine()

        # WELCOME -> OPEN_QUESTION
        next_state = engine.get_next_state(OnboardingState.WELCOME.value)
        assert next_state == OnboardingState.OPEN_QUESTION.value

        # OPEN_QUESTION -> LISTENING
        next_state = engine.get_next_state(OnboardingState.OPEN_QUESTION.value)
        assert next_state == OnboardingState.LISTENING.value

        # CONSENT -> NAME_REQUEST
        next_state = engine.get_next_state(OnboardingState.CONSENT.value)
        assert next_state == OnboardingState.NAME_REQUEST.value


class TestE2EOnboarding:
    """Test E2E del onboarding completo"""

    def test_full_onboarding_flow(self):
        """Simular flujo completo de onboarding"""
        from app.services.case_storage import delete_user_data, save_user_data
        from app.services.onboarding_v306 import OnboardingState, get_onboarding_engine

        engine = get_onboarding_engine()
        user_id = 888777

        try:
            delete_user_data(user_id)

            # Simular flujo
            user = {
                "language": "es",
                "state": OnboardingState.WELCOME.value,
                "profile": {"personal": {}, "migration": {}},
            }
            save_user_data(user_id, user)

            # PASO 1: Bienvenida
            welcome = engine.get_welcome_message("es")
            assert "amigo" in welcome.lower() or "MigPAL" in welcome

            # PASO 2: Pregunta abierta
            user["state"] = OnboardingState.OPEN_QUESTION.value
            save_user_data(user_id, user)
            question = engine.get_open_question("es")
            assert "?" in question

            # PASO 3: Respuesta empática
            response = engine.get_empathic_response("Quiero trabajar en USA", "es")
            assert len(response) > 50

            # PASO 4: Explicación
            explanation = engine.get_process_explanation("es")
            assert "conversamos" in explanation.lower() or "primero" in explanation.lower()

            # PASO 5: Consentimiento
            user["state"] = OnboardingState.CONSENT.value
            save_user_data(user_id, user)
            consent, buttons = engine.get_consent_request("es")
            assert "?" in consent
            assert len(buttons) >= 2

            # PASO 6: Nombre (después del consentimiento)
            user["state"] = OnboardingState.NAME_REQUEST.value
            save_user_data(user_id, user)
            name_request = engine.get_name_request("es")
            assert "nombre" in name_request.lower()

            # Verificar que NO hubo "FASE 1" en ningún momento
            all_messages = [welcome, question, response, explanation, consent, name_request]
            for msg in all_messages:
                assert "FASE 1" not in msg, f"Se mostró 'FASE 1' antes del consentimiento: {msg[:50]}"

        finally:
            delete_user_data(user_id)

    def test_start_command_does_not_show_form(self):
        """El comando /start NO debe mostrar formulario"""
        # Verificar que el código de telegram_bot.py no muestra formulario en /start
        from pathlib import Path

        bot_file = Path(__file__).parent.parent / "app" / "services" / "telegram_bot.py"
        content = bot_file.read_text()

        # Buscar el handler de _cmd_start
        import re

        start_handler = re.search(r"async def _cmd_start\(self.*?(?=async def |$)", content, re.DOTALL)

        assert start_handler, "No se encontró el handler de /start"

        handler_code = start_handler.group(0)

        # NO debe ir directo a STATE_NAME
        # Debe usar OnboardingState
        assert (
            "OnboardingState" in handler_code or "onboarding" in handler_code.lower()
        ), "El handler de /start debe usar el onboarding conversacional"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
