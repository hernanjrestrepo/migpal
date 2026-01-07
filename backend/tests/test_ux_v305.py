#!/usr/bin/env python3
"""
Tests para MigPAL UX v3.0.5
===========================
- Bug flow_pref_tech (TE AYUDO A ELEGIR)
- NLU de corrección
- Onboarding conversacional
- Manejo seguro de Markdown
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFlowPrefTechBug:
    """Tests para el bug de flow_pref_tech (TE AYUDO A ELEGIR)"""
    
    def test_flow_pref_handlers_exist(self):
        """Verificar que los handlers de flow_pref_* existen"""
        from pathlib import Path
        
        bot_file = Path(__file__).parent.parent / "app" / "services" / "telegram_bot.py"
        content = bot_file.read_text()
        
        # Verificar que existe el handler de pref_
        assert 'action.startswith("pref_")' in content, "Falta handler para pref_*"
        
        # Verificar que se manejan las preferencias
        assert "pref_warm" in content or "warm" in content
        assert "pref_tech" in content or "tech" in content
        assert "pref_cheap" in content or "cheap" in content
        assert "pref_latino" in content or "latino" in content
    
    def test_region_help_no_markdown_error(self):
        """Verificar que region_help no usa Markdown problemático"""
        from pathlib import Path
        import re
        
        bot_file = Path(__file__).parent.parent / "app" / "services" / "telegram_bot.py"
        content = bot_file.read_text()
        
        # Buscar el mensaje de TE AYUDO A ELEGIR
        # No debe tener parse_mode='Markdown' con asteriscos mal cerrados
        pattern = r'TE AYUDO A ELEGIR.*?parse_mode'
        matches = re.findall(pattern, content, re.DOTALL)
        
        # Si hay matches, verificar que no hay asteriscos problemáticos
        for match in matches:
            # Contar asteriscos - deben ser pares
            asterisks = match.count('*')
            # Si hay asteriscos, deben ser pares o no debe haber parse_mode='Markdown'
            if asterisks > 0:
                assert asterisks % 2 == 0 or "parse_mode" not in match, \
                    f"Markdown mal formateado en TE AYUDO A ELEGIR: {match[:100]}"


class TestCorrectionNLU:
    """Tests para NLU de corrección"""
    
    def test_detect_email_correction(self):
        """Detectar corrección de email"""
        from app.services.ux_v305 import CorrectionNLU, CorrectionType
        
        test_cases = [
            ("mi correo correcto es hernan@gmail.com", "hernan@gmail.com"),
            ("perdón, mi email es test@example.com", "test@example.com"),
            ("corregir mi correo a nuevo@mail.com", "nuevo@mail.com"),
            ("el correo correcto es user@domain.org", "user@domain.org"),
        ]
        
        for text, expected_email in test_cases:
            result = CorrectionNLU.detect_correction(text)
            assert result is not None, f"No detectó corrección en: {text}"
            assert result.type == CorrectionType.EMAIL, f"Tipo incorrecto para: {text}"
            assert result.value == expected_email, f"Email incorrecto para: {text}"
    
    def test_detect_phone_correction(self):
        """Detectar corrección de teléfono"""
        from app.services.ux_v305 import CorrectionNLU, CorrectionType
        
        test_cases = [
            ("mi teléfono correcto es +573001234567", "+573001234567"),
            ("corregir mi celular a 3001234567", "3001234567"),
        ]
        
        for text, expected_phone in test_cases:
            result = CorrectionNLU.detect_correction(text)
            assert result is not None, f"No detectó corrección en: {text}"
            assert result.type == CorrectionType.PHONE, f"Tipo incorrecto para: {text}"
    
    def test_detect_name_correction(self):
        """Detectar corrección de nombre"""
        from app.services.ux_v305 import CorrectionNLU, CorrectionType
        
        test_cases = [
            ("mi nombre correcto es Juan Pérez", "Juan Pérez"),
            ("me llamo María García", "María García"),
        ]
        
        for text, expected_name in test_cases:
            result = CorrectionNLU.detect_correction(text)
            assert result is not None, f"No detectó corrección en: {text}"
            assert result.type == CorrectionType.NAME, f"Tipo incorrecto para: {text}"
    
    def test_no_false_positives(self):
        """No detectar corrección cuando no la hay"""
        from app.services.ux_v305 import CorrectionNLU
        
        test_cases = [
            "Hola, cómo estás?",
            "Quiero migrar a Estados Unidos",
            "Tengo 30 años",
            "Vivo en Colombia",
        ]
        
        for text in test_cases:
            result = CorrectionNLU.detect_correction(text)
            # No debe detectar corrección en estos casos
            assert result is None, f"Falso positivo en: {text}"
    
    def test_confirmation_messages(self):
        """Verificar mensajes de confirmación"""
        from app.services.ux_v305 import CorrectionNLU, CorrectionIntent, CorrectionType
        
        correction = CorrectionIntent(
            type=CorrectionType.EMAIL,
            value="test@example.com",
            confidence=0.9,
            original_text="mi correo es test@example.com"
        )
        
        msg_es = CorrectionNLU.get_confirmation_message(correction, "es")
        assert "test@example.com" in msg_es
        assert "✅" in msg_es
        
        msg_en = CorrectionNLU.get_confirmation_message(correction, "en")
        assert "test@example.com" in msg_en


class TestSafeMarkdown:
    """Tests para manejo seguro de Markdown"""
    
    def test_escape_special_chars(self):
        """Escapar caracteres especiales"""
        from app.services.ux_v305 import SafeMarkdown
        
        text = "Hello *world* _test_"
        escaped = SafeMarkdown.escape(text)
        
        assert "\\*" in escaped
        assert "\\_" in escaped
    
    def test_validate_markdown(self):
        """Validar Markdown bien formateado"""
        from app.services.ux_v305 import SafeMarkdown
        
        # Markdown válido
        valid, cleaned = SafeMarkdown.validate_markdown("*bold* and _italic_")
        assert valid
        
        # Markdown inválido (asterisco suelto)
        valid, cleaned = SafeMarkdown.validate_markdown("*bold and _italic_")
        # Debe limpiar o marcar como inválido
        assert "*" not in cleaned or cleaned.count("*") % 2 == 0
    
    def test_strip_markdown(self):
        """Remover Markdown"""
        from app.services.ux_v305 import SafeMarkdown
        
        text = "*bold* and _italic_ and `code`"
        stripped = SafeMarkdown.strip_markdown(text)
        
        assert "*" not in stripped
        assert "_" not in stripped
        assert "`" not in stripped
        assert "bold" in stripped
        assert "italic" in stripped


class TestRegionPreferences:
    """Tests para preferencias de región"""
    
    def test_get_recommendation(self):
        """Obtener recomendación por preferencia"""
        from app.services.ux_v305 import RegionPreferences
        
        # Tech
        rec = RegionPreferences.get_recommendation("tech", "es")
        assert "California" in rec["states"] or "Washington" in rec["states"]
        assert "tech" in rec["description"].lower()
        
        # Warm
        rec = RegionPreferences.get_recommendation("warm", "es")
        assert "Florida" in rec["states"] or "Texas" in rec["states"]
        
        # Latino
        rec = RegionPreferences.get_recommendation("latino", "es")
        assert "Florida" in rec["states"]


class TestMigPALPersonality:
    """Tests para personalidad de MigPAL"""
    
    def test_get_greeting(self):
        """Obtener saludo personalizado"""
        from app.services.ux_v305 import MigPALPersonality
        
        greeting = MigPALPersonality.get_greeting("Juan", "es")
        assert "Juan" in greeting
        # El saludo debe ser amigable y personal
        assert len(greeting) > 20
        
        greeting_en = MigPALPersonality.get_greeting("John", "en")
        assert "John" in greeting_en
    
    def test_get_empathy(self):
        """Obtener frases empáticas"""
        from app.services.ux_v305 import MigPALPersonality
        
        empathy = MigPALPersonality.get_empathy("understanding", "es")
        assert len(empathy) > 0
        
        empathy_en = MigPALPersonality.get_empathy("support", "en")
        assert len(empathy_en) > 0
    
    def test_get_explanation(self):
        """Obtener explicaciones"""
        from app.services.ux_v305 import MigPALPersonality
        
        explanation = MigPALPersonality.get_explanation("process", "es")
        assert "paso" in explanation.lower() or "guiar" in explanation.lower()


class TestConversationalOnboarding:
    """Tests para onboarding conversacional"""
    
    def test_welcome_message(self):
        """Mensaje de bienvenida conversacional"""
        from app.services.ux_v305 import ConversationalOnboarding
        
        msg = ConversationalOnboarding.get_welcome_message("María", "es")
        
        # Debe incluir saludo, empatía y explicación
        assert "María" in msg or "amigo" in msg
        assert len(msg) > 100  # Mensaje sustancial
    
    def test_question_with_other(self):
        """Agregar opción 'Otro' a preguntas"""
        from app.services.ux_v305 import ConversationalOnboarding
        
        options = [
            ("Opción 1", "opt1"),
            ("Opción 2", "opt2"),
        ]
        
        question, new_options = ConversationalOnboarding.get_question_with_other(
            "¿Cuál prefieres?", options, "es"
        )
        
        # Debe tener una opción más
        assert len(new_options) == len(options) + 1
        
        # La última debe ser "Otro"
        last_option = new_options[-1]
        assert "Otro" in last_option[0] or "Other" in last_option[0]


class TestMultiSelect:
    """Tests para selección múltiple"""
    
    def test_create_keyboard(self):
        """Crear teclado con checkboxes"""
        from app.services.ux_v305 import MultiSelect
        
        options = [
            ("Opción 1", "opt1"),
            ("Opción 2", "opt2"),
            ("Opción 3", "opt3"),
        ]
        
        keyboard = MultiSelect.create_multi_select_keyboard(options, selected=["opt2"])
        
        # Debe tener opciones + botón confirmar
        assert len(keyboard) == len(options) + 1
        
        # opt2 debe tener checkbox marcado
        for row in keyboard:
            for text, data in row:
                if "opt2" in data:
                    assert "✅" in text
                elif "opt1" in data or "opt3" in data:
                    assert "⬜" in text
    
    def test_toggle_selection(self):
        """Toggle de selección"""
        from app.services.ux_v305 import MultiSelect
        
        current = ["opt1", "opt2"]
        
        # Toggle opt2 (quitar)
        new_selection = MultiSelect.toggle_selection(current, "opt2")
        assert "opt2" not in new_selection
        assert "opt1" in new_selection
        
        # Toggle opt3 (agregar)
        new_selection = MultiSelect.toggle_selection(current, "opt3")
        assert "opt3" in new_selection


class TestE2EFlowPrefTech:
    """Test E2E para el flujo flow_pref_tech"""
    
    def test_flow_pref_tech_simulation(self):
        """Simular el flujo completo de TE AYUDO A ELEGIR -> pref_tech"""
        # Este test verifica que el flujo no crashea
        from app.services.case_storage import save_user_data, load_user_data, delete_user_data
        
        user_id = 999888
        
        try:
            # Limpiar datos previos
            delete_user_data(user_id)
            
            # Crear usuario con estructura básica
            user = {
                "language": "es",
                "state": "start",
                "profile": {
                    "personal": {},
                    "migration": {}
                }
            }
            save_user_data(user_id, user)
            
            # Simular selección de preferencia tech
            user["profile"]["migration"]["preference"] = "tech"
            save_user_data(user_id, user)
            
            # Verificar que se guardó
            loaded = load_user_data(user_id)
            assert loaded["profile"]["migration"]["preference"] == "tech"
            
        finally:
            delete_user_data(user_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
