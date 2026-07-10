#!/usr/bin/env python3
"""
Test para el bug de ConversationFlowEngine.process_response()
Bug: TypeError: got an unexpected keyword argument 'options'
Fix: Cambiar options= a selected_options=
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFlowEngineBug:
    """Tests para el bug de process_response con options"""

    def test_process_response_accepts_selected_options(self):
        """Test que process_response acepta selected_options como argumento"""
        from app.services.conversation_flow import ConversationFlowEngine, ConversationState

        engine = ConversationFlowEngine()
        user_id = 999999

        # Inicializar contexto
        ctx = engine.get_context(user_id)
        ctx.current_state = ConversationState.DISCOVERY_WHY
        engine.set_context(user_id, ctx)

        # Llamar con selected_options (el fix)
        try:
            next_state, error_msg = engine.process_response(user_id, "work", selected_options=["work"])
            assert next_state is not None
            assert error_msg == ""
        except TypeError as e:
            pytest.fail(f"process_response no acepta selected_options: {e}")

    def test_process_response_without_options(self):
        """Test que process_response funciona sin options"""
        from app.services.conversation_flow import ConversationFlowEngine, ConversationState

        engine = ConversationFlowEngine()
        user_id = 999998

        # Inicializar contexto
        ctx = engine.get_context(user_id)
        ctx.current_state = ConversationState.DISCOVERY_WHY
        engine.set_context(user_id, ctx)

        # Llamar sin options
        try:
            next_state, error_msg = engine.process_response(user_id, "work")
            assert next_state is not None
        except TypeError as e:
            pytest.fail(f"process_response falla sin options: {e}")

    def test_flow_pref_tech_callback(self):
        """Test que simula el callback flow_pref_tech que causó el bug"""
        from app.services.conversation_flow import ConversationFlowEngine, ConversationState

        engine = ConversationFlowEngine()
        user_id = 999997

        # Simular el estado cuando se recibe flow_pref_tech
        ctx = engine.get_context(user_id)
        ctx.current_state = ConversationState.LIFE_WORK_OR_BUSINESS
        engine.set_context(user_id, ctx)

        # Simular la acción que causó el bug
        action = "pref_tech"

        try:
            next_state, error_msg = engine.process_response(user_id, action, selected_options=[action])
            # No debe lanzar TypeError
            assert True
        except TypeError as e:
            if "unexpected keyword argument 'options'" in str(e):
                pytest.fail("Bug no corregido: process_response no acepta selected_options")
            raise

    def test_telegram_bot_imports_correctly(self):
        """Test que telegram_bot usa selected_options correctamente"""
        import re

        # Leer el archivo telegram_bot.py
        bot_file = Path(__file__).parent.parent / "app" / "services" / "telegram_bot.py"
        content = bot_file.read_text()

        # Verificar que no hay llamadas con options= (el bug) - excluyendo selected_options
        # Buscar "options=[action]" que NO esté precedido por "selected_"
        bug_pattern = r"(?<!selected_)options=\[action\]"
        matches = re.findall(bug_pattern, content)
        assert len(matches) == 0, f"Bug: Todavía hay {len(matches)} llamadas con options=[action]"

        # Verificar que hay llamadas con selected_options= (el fix)
        assert "selected_options=[action]" in content, "Fix no aplicado: Falta selected_options=[action]"


class TestFlowEngineStates:
    """Tests para verificar que todos los estados del flow engine funcionan"""

    def test_all_states_have_handlers(self):
        """Test que todos los estados tienen handlers"""
        from app.services.conversation_flow import ConversationFlowEngine, ConversationState

        engine = ConversationFlowEngine()

        # Estados que deben tener handlers
        states_to_test = [
            ConversationState.WELCOME,
            ConversationState.DISCOVERY_WHY,
            ConversationState.DISCOVERY_DREAM,
            ConversationState.DISCOVERY_FAMILY,
            ConversationState.DISCOVERY_USA_CONNECTIONS,
            ConversationState.LIFE_WORK_OR_BUSINESS,
        ]

        for state in states_to_test:
            user_id = 900000 + state.value
            ctx = engine.get_context(user_id)
            ctx.current_state = state
            engine.set_context(user_id, ctx)

            # Debe poder procesar una respuesta sin error
            try:
                next_state, error_msg = engine.process_response(user_id, "test_response")
                assert next_state is not None, f"Estado {state.name} retornó None"
            except Exception as e:
                pytest.fail(f"Estado {state.name} falló: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
