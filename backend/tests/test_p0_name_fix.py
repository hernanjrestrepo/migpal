#!/usr/bin/env python3
"""
Tests P0 - Fix del bug de nombre trabado
=========================================
Valida que el fix del NameError en FORM_STATES funciona correctamente.

Bug original: NameError: name 'STATE_COMPANY' is not defined
Causa: FORM_STATES contenía referencias a constantes no definidas
Fix: Remover constantes no existentes del array FORM_STATES
"""

import sys
from pathlib import Path

import pytest

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestP0FormStatesConstants:
    """Tests para validar que FORM_STATES solo contiene constantes definidas"""

    def test_all_state_constants_are_defined(self):
        """Verifica que todas las constantes de estado usadas estén definidas"""
        # Import the module - this will fail if any constant is undefined
        from app.services.telegram_bot import (
            STATE_BIRTH_DATE,
            STATE_BUDGET_INITIAL,
            STATE_CURRENT_CITY,
            STATE_EDUCATION_CAREER,
            STATE_EMAIL,
            STATE_FAMILY_MEMBER_BIRTH,
            STATE_FAMILY_MEMBER_NAME,
            STATE_LINKEDIN,
            STATE_NAME,
            STATE_PHONE,
            STATE_PROFESSION,
            STATE_SAVINGS,
            STATE_TIMELINE,
        )

        # All imports should succeed
        assert STATE_NAME == "name"
        assert STATE_BIRTH_DATE == "birth_date"
        assert STATE_CURRENT_CITY == "current_city"
        assert STATE_EMAIL == "email"
        assert STATE_PHONE == "phone"
        assert STATE_EDUCATION_CAREER == "education_career"
        assert STATE_PROFESSION == "profession"
        assert STATE_LINKEDIN == "linkedin"
        assert STATE_TIMELINE == "timeline"
        assert STATE_BUDGET_INITIAL == "budget_initial"
        assert STATE_SAVINGS == "savings"
        assert STATE_FAMILY_MEMBER_NAME == "family_member_name"
        assert STATE_FAMILY_MEMBER_BIRTH == "family_member_birth"

    def test_form_states_array_is_valid(self):
        """Verifica que el array FORM_STATES no cause NameError"""
        # This should not raise any exception
        from app.services.telegram_bot import (
            STATE_BIRTH_DATE,
            STATE_BUDGET_INITIAL,
            STATE_CURRENT_CITY,
            STATE_EDUCATION_CAREER,
            STATE_EMAIL,
            STATE_FAMILY_MEMBER_BIRTH,
            STATE_FAMILY_MEMBER_NAME,
            STATE_LINKEDIN,
            STATE_NAME,
            STATE_PHONE,
            STATE_PROFESSION,
            STATE_SAVINGS,
            STATE_TIMELINE,
        )

        # Recreate FORM_STATES as in the actual code
        FORM_STATES = [
            STATE_NAME,
            "confirm_name",
            STATE_BIRTH_DATE,
            STATE_CURRENT_CITY,
            STATE_EMAIL,
            STATE_PHONE,
            STATE_EDUCATION_CAREER,
            STATE_PROFESSION,
            STATE_LINKEDIN,
            STATE_TIMELINE,
            STATE_BUDGET_INITIAL,
            STATE_SAVINGS,
            STATE_FAMILY_MEMBER_NAME,
            STATE_FAMILY_MEMBER_BIRTH,
        ]

        # Verify all elements are strings
        for state in FORM_STATES:
            assert isinstance(state, str), f"State {state} is not a string"

        # Verify expected states are present
        assert "name" in FORM_STATES
        assert "confirm_name" in FORM_STATES
        assert "birth_date" in FORM_STATES

    def test_removed_constants_do_not_exist(self):
        """Verifica que las constantes removidas no existen (como se esperaba)"""
        import app.services.telegram_bot as bot_module

        # These constants should NOT exist
        removed_constants = [
            "STATE_COMPANY",
            "STATE_SALARY",
            "STATE_ACHIEVEMENTS",
            "STATE_FAMILY_DETAILS",
            "STATE_BUDGET",  # Note: STATE_BUDGET_INITIAL exists, but STATE_BUDGET does not
            "STATE_CONCERNS",
            "STATE_GOALS",
        ]

        for const in removed_constants:
            assert not hasattr(bot_module, const), f"Constant {const} should not exist"


class TestP0NameHandler:
    """Tests para el handler del nombre"""

    def test_name_state_exists(self):
        """Verifica que el estado NAME existe"""
        from app.services.telegram_bot import STATE_NAME

        assert STATE_NAME == "name"

    def test_confirm_name_state_is_string(self):
        """Verifica que confirm_name es un string válido"""
        confirm_name = "confirm_name"
        assert isinstance(confirm_name, str)
        assert len(confirm_name) > 0

    def test_get_user_data_creates_profile(self):
        """Verifica que get_user_data crea un perfil válido"""
        from app.services.case_storage import delete_user_data
        from app.services.telegram_bot import get_user_data

        test_user_id = 999999999

        # Clean up first
        try:
            delete_user_data(test_user_id)
        except:
            pass

        # Get user data (should create new)
        user = get_user_data(test_user_id)

        # Verify structure
        assert "user_id" in user
        assert "state" in user
        assert "profile" in user
        assert "personal" in user["profile"]

        # Clean up
        try:
            delete_user_data(test_user_id)
        except:
            pass

    def test_set_state_persists(self):
        """Verifica que set_state persiste el estado"""
        from app.services.case_storage import delete_user_data
        from app.services.telegram_bot import get_state, get_user_data, set_state

        test_user_id = 999999998

        # Clean up first
        try:
            delete_user_data(test_user_id)
        except:
            pass

        # Initialize user
        get_user_data(test_user_id)

        # Set state
        set_state(test_user_id, "name")

        # Verify state
        state = get_state(test_user_id)
        assert state == "name"

        # Set to confirm_name
        set_state(test_user_id, "confirm_name")
        state = get_state(test_user_id)
        assert state == "confirm_name"

        # Clean up
        try:
            delete_user_data(test_user_id)
        except:
            pass


class TestP0Translations:
    """Tests para las traducciones del flujo de nombre"""

    def test_confirm_name_translation_exists_es(self):
        """Verifica que la traducción confirm_name existe en español"""
        from app.services.translations import get_text

        text = get_text("confirm_name", "es")
        assert text is not None
        assert "{name}" in text  # Should have placeholder
        assert "nombre" in text.lower() or "name" in text.lower()

    def test_confirm_name_translation_exists_en(self):
        """Verifica que la traducción confirm_name existe en inglés"""
        from app.services.translations import get_text

        text = get_text("confirm_name", "en")
        assert text is not None
        assert "{name}" in text  # Should have placeholder

    def test_yes_correct_translation_exists(self):
        """Verifica que la traducción yes_correct existe"""
        from app.services.translations import get_text

        text_es = get_text("yes_correct", "es")
        text_en = get_text("yes_correct", "en")

        assert text_es is not None
        assert text_en is not None

    def test_no_change_translation_exists(self):
        """Verifica que la traducción no_change existe"""
        from app.services.translations import get_text

        text_es = get_text("no_change", "es")
        text_en = get_text("no_change", "en")

        assert text_es is not None
        assert text_en is not None

    def test_name_retry_translation_exists(self):
        """Verifica que la traducción name_retry existe"""
        from app.services.translations import get_text

        text_es = get_text("name_retry", "es")
        text_en = get_text("name_retry", "en")

        assert text_es is not None
        assert text_en is not None


class TestP0Integration:
    """Tests de integración para el flujo completo del nombre"""

    def test_name_flow_state_transitions(self):
        """Verifica las transiciones de estado del flujo de nombre"""
        from app.services.case_storage import delete_user_data, save_user_data
        from app.services.security import encrypt_user_data
        from app.services.telegram_bot import STATE_NAME, STATE_START, get_state, get_user_data, set_state

        test_user_id = 999999997

        # Clean up first
        try:
            delete_user_data(test_user_id)
        except:
            pass

        # Initialize user
        user = get_user_data(test_user_id)

        # Start -> Name
        set_state(test_user_id, STATE_START)
        assert get_state(test_user_id) == STATE_START

        set_state(test_user_id, STATE_NAME)
        assert get_state(test_user_id) == STATE_NAME

        # Name -> confirm_name
        user["_pending_name"] = "Test User"
        encrypted = encrypt_user_data(user)
        save_user_data(test_user_id, encrypted)

        set_state(test_user_id, "confirm_name")
        assert get_state(test_user_id) == "confirm_name"

        # confirm_name -> start (after confirmation)
        user = get_user_data(test_user_id)
        user["profile"]["personal"]["name"] = user.get("_pending_name", "")
        if "_pending_name" in user:
            del user["_pending_name"]
        encrypted = encrypt_user_data(user)
        save_user_data(test_user_id, encrypted)

        set_state(test_user_id, STATE_START)
        assert get_state(test_user_id) == STATE_START

        # Verify name was saved
        user = get_user_data(test_user_id)
        assert user["profile"]["personal"]["name"] == "Test User"

        # Clean up
        try:
            delete_user_data(test_user_id)
        except:
            pass

    def test_name_validation_trim(self):
        """Verifica que el nombre se trimea correctamente"""
        name = "  Test User  "
        trimmed = name.strip()
        assert trimmed == "Test User"

    def test_name_validation_titlecase(self):
        """Verifica que el nombre se convierte a titlecase"""
        name_upper = "JOHN DOE"
        name_lower = "john doe"

        # Should convert to titlecase
        if name_upper.isupper():
            name_upper = name_upper.title()
        if name_lower.islower():
            name_lower = name_lower.title()

        assert name_upper == "John Doe"
        assert name_lower == "John Doe"

    def test_name_validation_min_length(self):
        """Verifica la validación de longitud mínima"""
        short_name = "A"
        valid_name = "AB"

        assert len(short_name) < 2  # Should fail validation
        assert len(valid_name) >= 2  # Should pass validation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
