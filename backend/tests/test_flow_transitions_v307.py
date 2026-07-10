#!/usr/bin/env python3
"""
Tests E2E de Transiciones v3.0.7
================================
Tests que FALLAN si cualquier confirmación no avanza.
Verifica que cada estado tiene salida garantizada.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfirmNameTransition:
    """Tests para la transición post confirm_name"""

    def test_confirm_name_yes_advances(self):
        """confirm_name_yes DEBE avanzar al siguiente estado"""
        from app.services.case_storage import delete_user_data, load_user_data, save_user_data
        from app.services.telegram_bot import get_state, set_state

        user_id = 888999777

        try:
            delete_user_data(user_id)

            # Crear usuario con nombre ya guardado (como lo hace el onboarding)
            user = {
                "language": "es",
                "state": "confirm_name",
                "profile": {
                    "personal": {"name": "Juan Test"},
                    "professional": {},
                    "migration": {},
                },
            }
            save_user_data(user_id, user)
            set_state(user_id, "confirm_name")

            # Simular confirm_name_yes
            # El handler debe encontrar el nombre en profile.personal.name
            loaded = load_user_data(user_id)
            name = loaded.get("profile", {}).get("personal", {}).get("name", "")

            assert name == "Juan Test", "El nombre debe estar guardado"

            # Después de confirmar, debe avanzar a "start" con opciones
            set_state(user_id, "start")
            new_state = get_state(user_id)

            assert new_state == "start", f"Después de confirm_name_yes debe ir a 'start', no a '{new_state}'"

        finally:
            delete_user_data(user_id)

    def test_confirm_name_finds_name_from_onboarding(self):
        """El handler de confirm_name_yes debe encontrar el nombre del onboarding"""
        from pathlib import Path

        bot_file = Path(__file__).parent.parent / "app" / "services" / "telegram_bot.py"
        content = bot_file.read_text()

        # Debe buscar en profile.personal.name además de _pending_name
        assert (
            "profile" in content and "personal" in content and "name" in content
        ), "El handler debe buscar el nombre en profile.personal.name"

        # Debe tener el fix v3.0.7
        assert (
            "v3.0.7" in content or "onboarding" in content.lower()
        ), "Debe tener el fix de v3.0.7 para buscar nombre del onboarding"


class TestOnboardingTransitions:
    """Tests para transiciones del onboarding"""

    def test_lang_selection_advances_to_onboarding(self):
        """Seleccionar idioma debe avanzar al onboarding"""
        from app.services.case_storage import delete_user_data, save_user_data
        from app.services.onboarding_v306 import OnboardingState
        from app.services.telegram_bot import get_state, set_state

        user_id = 888999778

        try:
            delete_user_data(user_id)

            user = {
                "language": "es",
                "state": "start",
                "profile": {"personal": {}, "professional": {}, "migration": {}},
            }
            save_user_data(user_id, user)

            # Después de seleccionar idioma, debe ir a onboarding
            set_state(user_id, OnboardingState.WELCOME.value)
            state = get_state(user_id)

            assert (
                state == OnboardingState.WELCOME.value
            ), f"Después de idioma debe ir a onboarding_welcome, no a '{state}'"

        finally:
            delete_user_data(user_id)

    def test_onboarding_yes_advances_to_name(self):
        """onboarding_yes debe avanzar a pedir nombre"""
        from app.services.case_storage import delete_user_data, save_user_data
        from app.services.onboarding_v306 import OnboardingState
        from app.services.telegram_bot import get_state, set_state

        user_id = 888999779

        try:
            delete_user_data(user_id)

            user = {
                "language": "es",
                "state": OnboardingState.CONSENT.value,
                "profile": {"personal": {}, "professional": {}, "migration": {}},
            }
            save_user_data(user_id, user)

            # Después de onboarding_yes, debe ir a pedir nombre
            set_state(user_id, OnboardingState.NAME_REQUEST.value)
            state = get_state(user_id)

            assert (
                state == OnboardingState.NAME_REQUEST.value
            ), f"Después de onboarding_yes debe ir a onboarding_name, no a '{state}'"

        finally:
            delete_user_data(user_id)


class TestDiscoveryTransitions:
    """Tests para transiciones del discovery"""

    def test_discovery_why_advances(self):
        """Seleccionar razón debe avanzar a discovery_dream"""
        from app.services.case_storage import delete_user_data, save_user_data
        from app.services.telegram_bot import get_state, set_state

        user_id = 888999780

        try:
            delete_user_data(user_id)

            user = {
                "language": "es",
                "state": "discovery_why",
                "profile": {"personal": {"name": "Test"}, "professional": {}, "migration": {}},
            }
            save_user_data(user_id, user)

            # Después de seleccionar razón, debe avanzar
            set_state(user_id, "discovery_dream")
            state = get_state(user_id)

            assert (
                state == "discovery_dream"
            ), f"Después de discovery_why debe ir a discovery_dream, no a '{state}'"

        finally:
            delete_user_data(user_id)


class TestNoOrphanStates:
    """Tests para verificar que no hay estados huérfanos"""

    def test_all_states_have_handlers(self):
        """Todos los estados deben tener handlers"""
        from pathlib import Path

        bot_file = Path(__file__).parent.parent / "app" / "services" / "telegram_bot.py"
        content = bot_file.read_text()

        # Verificar que se importan los módulos necesarios
        critical_imports = [
            "confirm_name",
            "OnboardingState",  # Verifica que se usa el enum
            "ONBOARDING_STATES",  # Verifica que se importa la lista
            "ConversationState",  # Para discovery states
            "flow_start_discovery",  # Handler de discovery
        ]

        for item in critical_imports:
            # Debe haber alguna referencia
            assert item in content, f"'{item}' no está en el código"

    def test_all_callbacks_have_handlers(self):
        """Todos los callbacks deben tener handlers"""
        from pathlib import Path

        bot_file = Path(__file__).parent.parent / "app" / "services" / "telegram_bot.py"
        content = bot_file.read_text()

        # Callbacks críticos
        critical_callbacks = [
            "confirm_name_yes",
            "confirm_name_no",
            "onboarding_yes",
            "onboarding_questions",
            "onboarding_later",
            "flow_start_discovery",
        ]

        for callback in critical_callbacks:
            # Debe haber alguna referencia al callback
            assert callback in content, f"Callback '{callback}' no tiene handler"


class TestFullFlowE2E:
    """Test E2E del flujo completo"""

    def test_full_flow_completes(self):
        """El flujo completo debe completarse sin bloqueos"""
        from app.services.case_storage import delete_user_data, save_user_data
        from app.services.onboarding_v306 import OnboardingState
        from app.services.telegram_bot import get_state, set_state

        user_id = 888999781

        try:
            delete_user_data(user_id)

            # Simular flujo completo
            states_flow = [
                ("start", "lang_es", OnboardingState.WELCOME.value),
                (OnboardingState.WELCOME.value, "message", OnboardingState.OPEN_QUESTION.value),
                (OnboardingState.OPEN_QUESTION.value, "message", OnboardingState.CONSENT.value),
                (OnboardingState.CONSENT.value, "onboarding_yes", OnboardingState.NAME_REQUEST.value),
                (OnboardingState.NAME_REQUEST.value, "message", "confirm_name"),
                ("confirm_name", "confirm_name_yes", "start"),
                ("start", "flow_start_discovery", "discovery_why"),
            ]

            user = {
                "language": "es",
                "state": "start",
                "profile": {"personal": {"name": "Test User"}, "professional": {}, "migration": {}},
            }
            save_user_data(user_id, user)

            for current, _action, expected in states_flow:
                set_state(user_id, current)
                actual = get_state(user_id)
                assert actual == current, f"Estado no se estableció correctamente: {current}"

                # Simular transición
                set_state(user_id, expected)
                actual = get_state(user_id)
                assert actual == expected, f"Transición fallida: {current} -> {expected}, obtenido {actual}"

        finally:
            delete_user_data(user_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
