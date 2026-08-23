#!/usr/bin/env python3
"""
MigPAL E2E Test - Occupation Flow Never Triggers emotion_clarification
======================================================================
V5.0 FIX: Respuestas válidas a ocupación NUNCA deben derivar en emotion_clarification.

Este test verifica que:
1. "soy ingeniero" NO activa emotion_clarification
2. "tengo una empresa de IA" NO activa emotion_clarification
3. "trabajo como programador" NO activa emotion_clarification
4. Solo señales EXPLÍCITAS de confusión activan emotion_clarification:
   - "no entiendo", "estoy confundido", "me perdí"

Ejecutar: python -m pytest backend/tests/test_occupation_no_emotion_clarification.py -v -s
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestOccupationNeverTriggersEmotionClarification:
    """
    Tests que verifican que respuestas válidas a ocupación NUNCA activan emotion_clarification.

    REGLA CRÍTICA: Si el usuario responde coherentemente a una pregunta activa,
    NO debe activarse emotion_clarification.
    """

    def test_soy_ingeniero_is_valid_response(self):
        """'soy ingeniero' es respuesta válida, NO confusión"""
        from app.services.profile_validator import PriorityIntentHandler

        test_cases = [
            "soy ingeniero",
            "soy ingeniero de software",
            "soy ingeniera de sistemas",
            "soy doctor",
            "soy abogado",
            "soy programador",
            "soy diseñador",
        ]

        for text in test_cases:
            # Verificar que es respuesta válida
            is_valid = PriorityIntentHandler.is_valid_response(text)
            assert is_valid, f"'{text}' debería ser respuesta válida"

            # Verificar que NO activa emotion_clarification
            should_interrupt, intent_type, _ = PriorityIntentHandler.should_interrupt_flow(text)
            assert (
                not should_interrupt or intent_type != "confusion"
            ), f"'{text}' NO debería activar confusion, pero activó: {intent_type}"

    def test_tengo_empresa_is_valid_response(self):
        """'tengo una empresa' es respuesta válida, NO confusión"""
        from app.services.profile_validator import PriorityIntentHandler

        test_cases = [
            "tengo una empresa de IA",
            "tengo una empresa de tecnología",
            "tengo un negocio",
            "tengo una startup",
            "tengo una compañía de software",
        ]

        for text in test_cases:
            is_valid = PriorityIntentHandler.is_valid_response(text)
            assert is_valid, f"'{text}' debería ser respuesta válida"

            should_interrupt, intent_type, _ = PriorityIntentHandler.should_interrupt_flow(text)
            assert (
                not should_interrupt or intent_type != "confusion"
            ), f"'{text}' NO debería activar confusion"

    def test_trabajo_como_is_valid_response(self):
        """'trabajo como X' es respuesta válida, NO confusión"""
        from app.services.profile_validator import PriorityIntentHandler

        test_cases = [
            "trabajo como programador",
            "trabajo en una empresa de tecnología",
            "trabajo de ingeniero",
            "trabajo como consultor",
        ]

        for text in test_cases:
            is_valid = PriorityIntentHandler.is_valid_response(text)
            assert is_valid, f"'{text}' debería ser respuesta válida"

            should_interrupt, intent_type, _ = PriorityIntentHandler.should_interrupt_flow(text)
            assert (
                not should_interrupt or intent_type != "confusion"
            ), f"'{text}' NO debería activar confusion"

    def test_explicit_confusion_does_trigger(self):
        """Solo señales EXPLÍCITAS de confusión deben activar emotion_clarification"""
        from app.services.profile_validator import PriorityIntentHandler

        # Estas SÍ deben activar confusion
        explicit_confusion_cases = [
            "no entiendo",
            "estoy confundido",
            "estoy confundida",
            "me perdí",
            "estoy perdido",
            "no comprendo",
            "no me queda claro",
        ]

        for text in explicit_confusion_cases:
            should_interrupt, intent_type, _ = PriorityIntentHandler.should_interrupt_flow(text)
            assert (
                should_interrupt and intent_type == "confusion"
            ), f"'{text}' DEBERÍA activar confusion, pero no lo hizo"

    def test_aja_no_longer_triggers_confusion(self):
        """'ajá' ya NO debe activar confusion (era falso positivo)"""
        from app.services.profile_validator import PriorityIntentHandler

        # Estas NO deben activar confusion (eran falsos positivos)
        false_positive_cases = [
            "ajá",
            "aja",
            "qué pasa",
            "que pasa",
            "no sé",  # Solo "no sé" sin contexto de confusión
        ]

        for text in false_positive_cases:
            should_interrupt, intent_type, _ = PriorityIntentHandler.should_interrupt_flow(text)
            # No debe activar confusion (puede activar otros intents o ninguno)
            if should_interrupt:
                assert intent_type != "confusion", f"'{text}' NO debería activar confusion (falso positivo)"

    def test_long_response_with_info_not_confusion(self):
        """Respuestas largas con información NO son confusión"""
        from app.services.profile_validator import PriorityIntentHandler

        test_cases = [
            "Soy ingeniero de software con 10 años de experiencia en desarrollo web",
            "Tengo una empresa de inteligencia artificial que desarrolla chatbots",
            "Trabajo como consultor de tecnología para empresas multinacionales",
            "Mi profesión es arquitecto de software y tengo experiencia en cloud",
        ]

        for text in test_cases:
            is_valid = PriorityIntentHandler.is_valid_response(text)
            assert is_valid, f"'{text}' debería ser respuesta válida"

            should_interrupt, intent_type, _ = PriorityIntentHandler.should_interrupt_flow(text)
            assert (
                not should_interrupt or intent_type != "confusion"
            ), f"'{text}' NO debería activar confusion"

    def test_occupation_detection_works(self):
        """CorrectionNLU debe detectar ocupación correctamente"""
        from app.services.ux_v305 import CorrectionNLU, CorrectionType

        test_cases = [
            ("soy ingeniero", "ingeniero"),
            ("soy ingeniero de software", "ingeniero"),
            ("trabajo como programador", "programador"),
            ("soy doctor", "doctor"),
            ("soy abogado", "abogado"),
        ]

        for text, expected_profession in test_cases:
            correction = CorrectionNLU.detect_correction(text)
            assert correction is not None, f"Debería detectar ocupación en: '{text}'"
            assert (
                correction.type == CorrectionType.OCCUPATION
            ), f"Tipo debería ser OCCUPATION, no {correction.type}"
            assert (
                expected_profession in correction.value.lower()
            ), f"Profesión debería contener '{expected_profession}', pero es '{correction.value}'"


class TestReflectConfirmAdvancePattern:
    """
    Tests para el patrón REFLECT → CONFIRM → ADVANCE.

    El bot debe:
    1. REFLECT: Parafrasear lo que entendió ("Entiendo que eres ingeniero")
    2. CONFIRM: Confirmar implícitamente (no preguntar "¿es correcto?")
    3. ADVANCE: Avanzar a la siguiente pregunta
    """

    def test_confirmation_message_reflects_profession(self):
        """El mensaje de confirmación debe reflejar la profesión"""
        from app.services.ux_v305 import CorrectionIntent, CorrectionNLU, CorrectionType

        # Crear un CorrectionIntent de prueba
        correction = CorrectionIntent(
            type=CorrectionType.OCCUPATION,
            value="ingeniero de software",
            confidence=0.9,
            original_text="soy ingeniero de software",
        )

        # Obtener mensaje de confirmación
        msg_es = CorrectionNLU.get_confirmation_message(correction, "es")
        CorrectionNLU.get_confirmation_message(correction, "en")

        # Verificar que el mensaje refleja la profesión
        assert "ingeniero" in msg_es.lower(), f"Mensaje ES debería mencionar 'ingeniero': {msg_es}"

        # Verificar que pregunta el nombre (ADVANCE)
        assert (
            "nombre" in msg_es.lower() or "llamas" in msg_es.lower()
        ), f"Mensaje ES debería preguntar nombre: {msg_es}"


class TestSingleActiveIntent:
    """
    Tests para garantizar una sola intención activa.

    REGLA: Si el bot pregunta ocupación, NO puede cambiar de estado
    hasta confirmar la ocupación.
    """

    def test_occupation_state_not_changed_by_confusion_patterns(self):
        """El estado no debe cambiar si el usuario da información válida"""
        from app.services.profile_validator import PriorityIntentHandler

        # Simular que el bot preguntó ocupación
        current_state = "ask_occupation"

        # Usuario responde con ocupación
        user_response = "soy ingeniero de software"

        # Verificar que NO se interrumpe el flujo
        should_interrupt, intent_type, _ = PriorityIntentHandler.should_interrupt_flow(
            user_response, current_state
        )

        assert (
            not should_interrupt or intent_type != "confusion"
        ), "Respuesta válida a ocupación NO debe interrumpir el flujo"


class TestNoGaslighting:
    """
    Tests para evitar gaslighting conversacional.

    El bot NO debe:
    - Repetir preguntas que ya fueron respondidas
    - Ignorar información que el usuario ya dio
    - Hacer sentir al usuario que no fue escuchado
    """

    def test_valid_response_not_ignored(self):
        """Respuestas válidas NO deben ser ignoradas"""
        from app.services.profile_validator import PriorityIntentHandler

        # Respuestas que contienen información válida
        valid_responses = [
            "soy ingeniero y quiero migrar a USA",
            "tengo una empresa de tecnología en Colombia",
            "trabajo como programador desde hace 5 años",
            "mi profesión es arquitecto de software",
        ]

        for response in valid_responses:
            is_valid = PriorityIntentHandler.is_valid_response(response)
            assert is_valid, f"'{response}' debería ser reconocida como respuesta válida"

            # No debe activar confusion
            should_interrupt, intent_type, _ = PriorityIntentHandler.should_interrupt_flow(response)
            if should_interrupt:
                assert intent_type != "confusion", f"'{response}' NO debe activar confusion (gaslighting)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
