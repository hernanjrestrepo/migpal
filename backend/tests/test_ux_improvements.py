#!/usr/bin/env python3
"""
Tests for UX Improvements v3.0.3
================================
Tests for:
1. Startup Self-Check
2. Global Exception Handler
3. Timeout/Anti-Stall
4. Name Confirmation Simplification
5. Progress UX
6. Enhanced Logging
"""

import sys
from pathlib import Path

import pytest

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestStartupValidator:
    """Tests for startup self-check functionality"""

    def test_validate_form_states_all_valid(self):
        """Test that valid FORM_STATES pass validation"""
        from app.services.telegram_bot import (
            STATE_BIRTH_DATE,
            STATE_CURRENT_CITY,
            STATE_EMAIL,
            STATE_NAME,
            STATE_PHONE,
        )
        from app.services.ux_improvements import StartupValidator

        # Create mock module globals
        module_globals = {
            "STATE_NAME": STATE_NAME,
            "STATE_BIRTH_DATE": STATE_BIRTH_DATE,
            "STATE_CURRENT_CITY": STATE_CURRENT_CITY,
            "STATE_EMAIL": STATE_EMAIL,
            "STATE_PHONE": STATE_PHONE,
        }

        form_states = [STATE_NAME, "confirm_name", STATE_BIRTH_DATE]

        is_valid, missing = StartupValidator.validate_form_states(form_states, module_globals)
        assert is_valid is True
        assert len(missing) == 0

    def test_validate_all_states_returns_report(self):
        """Test that validate_all_states returns a proper report"""
        from app.services.telegram_bot import STATE_BIRTH_DATE, STATE_NAME, STATE_START
        from app.services.ux_improvements import StartupValidator

        module_globals = {
            "STATE_NAME": STATE_NAME,
            "STATE_BIRTH_DATE": STATE_BIRTH_DATE,
            "STATE_START": STATE_START,
        }

        is_valid, report = StartupValidator.validate_all_states(module_globals)

        assert "timestamp" in report
        assert "state_constants_count" in report
        assert "phases_validated" in report
        assert report["state_constants_count"] >= 0

    def test_run_startup_check_passes(self):
        """Test that startup check passes with valid configuration"""
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
        from app.services.ux_improvements import StartupValidator

        module_globals = globals()
        form_states = [
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

        result = StartupValidator.run_startup_check(module_globals, form_states)
        assert result is True


class TestGlobalExceptionHandler:
    """Tests for global exception handler"""

    def test_singleton_pattern(self):
        """Test that GlobalExceptionHandler is a singleton"""
        from app.services.ux_improvements import GlobalExceptionHandler

        handler1 = GlobalExceptionHandler()
        handler2 = GlobalExceptionHandler()

        assert handler1 is handler2

    def test_log_error(self):
        """Test error logging"""
        from app.services.ux_improvements import GlobalExceptionHandler

        handler = GlobalExceptionHandler()

        try:
            raise ValueError("Test error")
        except Exception as e:
            handler.log_error(12345, "test_state", e, "test_context")

        recent = handler.get_recent_errors(1)
        assert len(recent) >= 1
        assert recent[-1]["user_id"] == 12345
        assert recent[-1]["state"] == "test_state"
        assert recent[-1]["error_type"] == "ValueError"

    def test_get_fallback_message_es(self):
        """Test Spanish fallback message"""
        from app.services.ux_improvements import GlobalExceptionHandler

        handler = GlobalExceptionHandler()
        msg = handler.get_fallback_message("es")

        assert "error" in msg.lower() or "Error" in msg
        assert "/start" in msg

    def test_get_fallback_message_en(self):
        """Test English fallback message"""
        from app.services.ux_improvements import GlobalExceptionHandler

        handler = GlobalExceptionHandler()
        msg = handler.get_fallback_message("en")

        assert "error" in msg.lower()
        assert "/start" in msg


class TestStallDetector:
    """Tests for timeout/anti-stall functionality"""

    def test_singleton_pattern(self):
        """Test that StallDetector is a singleton"""
        from app.services.ux_improvements import StallDetector

        detector1 = StallDetector()
        detector2 = StallDetector()

        assert detector1 is detector2

    def test_record_activity(self):
        """Test activity recording"""
        from app.services.ux_improvements import StallDetector

        detector = StallDetector()
        detector.record_activity(99999, "test_state", "test message")

        # Should not be stalled immediately
        is_stalled, reason = detector.is_stalled(99999)
        assert is_stalled is False

        # Clean up
        detector.clear_user(99999)

    def test_repeated_messages_detection(self):
        """Test detection of repeated messages"""
        from app.services.ux_improvements import MAX_REPEATED_MESSAGES, StallDetector

        detector = StallDetector()
        user_id = 88888

        # Clear any existing data
        detector.clear_user(user_id)

        # Send same message multiple times
        for _ in range(MAX_REPEATED_MESSAGES + 1):
            detector.record_activity(user_id, "test_state", "same message")

        is_stalled, reason = detector.is_stalled(user_id)
        assert is_stalled is True
        assert reason == "repeated"

        # Clean up
        detector.clear_user(user_id)

    def test_get_stall_message(self):
        """Test stall message generation"""
        from app.services.ux_improvements import StallDetector

        detector = StallDetector()

        msg, buttons = detector.get_stall_message("es", "¿Cuál es tu nombre?")

        assert "Hola" in msg or "hola" in msg
        assert len(buttons) == 2
        assert buttons[0][1] == "stall_continue"
        assert buttons[1][1] == "stall_restart"


class TestProgressTracker:
    """Tests for progress UX functionality"""

    def test_get_current_phase(self):
        """Test phase detection from state"""
        from app.services.ux_improvements import ProgressTracker

        phase = ProgressTracker.get_current_phase("name")
        assert phase == "phase1_profile"

        phase = ProgressTracker.get_current_phase("education_level")
        assert phase == "phase2_education"

        phase = ProgressTracker.get_current_phase("unknown_state")
        assert phase is None

    def test_get_phase_progress(self):
        """Test phase progress calculation"""
        from app.services.ux_improvements import ProgressTracker

        user_data = {"profile": {"personal": {"name": "Test User", "birth_date": "01/01/1990"}}}

        progress = ProgressTracker.get_phase_progress(user_data, "phase1_profile")

        assert "completed" in progress
        assert "total" in progress
        assert "missing_fields" in progress
        assert "percentage" in progress
        assert progress["completed"] >= 2  # name and birth_date

    def test_get_overall_progress(self):
        """Test overall progress calculation"""
        from app.services.ux_improvements import ProgressTracker

        user_data = {
            "profile": {
                "personal": {"name": "Test"},
                "education": {},
                "work": {},
                "languages": {},
                "history": {},
                "financial": {},
            },
            "preferences": {},
        }

        overall = ProgressTracker.get_overall_progress(user_data)

        assert "overall_percentage" in overall
        assert "phases" in overall
        assert len(overall["phases"]) == 7  # 7 phases

    def test_format_progress_header_es(self):
        """Test Spanish progress header formatting"""
        from app.services.ux_improvements import ProgressTracker

        user_data = {
            "profile": {
                "personal": {"name": "Test User"},
                "education": {},
                "work": {},
                "languages": {},
                "history": {},
                "financial": {},
            },
            "preferences": {},
        }

        header = ProgressTracker.format_progress_header(user_data, "name", "es")

        assert "Tu Perfil" in header
        assert "%" in header
        assert "Falta" in header or "▓" in header

    def test_format_phase_summary(self):
        """Test phase summary formatting"""
        from app.services.ux_improvements import ProgressTracker

        user_data = {
            "profile": {
                "personal": {},
                "education": {},
                "work": {},
                "languages": {},
                "history": {},
                "financial": {},
            },
            "preferences": {},
        }

        summary = ProgressTracker.format_phase_summary(user_data, "es")

        assert "Progreso" in summary
        assert "%" in summary


class TestNameValidator:
    """Tests for name validation and confirmation simplification"""

    def test_is_valid_name_valid(self):
        """Test valid name validation"""
        from app.services.ux_improvements import NameValidator

        is_valid, result = NameValidator.is_valid_name("John Doe")
        assert is_valid is True
        assert result == "John Doe"

    def test_is_valid_name_titlecase(self):
        """Test titlecase conversion"""
        from app.services.ux_improvements import NameValidator

        is_valid, result = NameValidator.is_valid_name("JOHN DOE")
        assert is_valid is True
        assert result == "John Doe"

        is_valid, result = NameValidator.is_valid_name("john doe")
        assert is_valid is True
        assert result == "John Doe"

    def test_is_valid_name_too_short(self):
        """Test short name rejection"""
        from app.services.ux_improvements import NameValidator

        is_valid, result = NameValidator.is_valid_name("A")
        assert is_valid is False
        assert result == "too_short"

    def test_is_valid_name_empty(self):
        """Test empty name rejection"""
        from app.services.ux_improvements import NameValidator

        is_valid, result = NameValidator.is_valid_name("")
        assert is_valid is False
        assert result == "empty"

        is_valid, result = NameValidator.is_valid_name("   ")
        assert is_valid is False
        assert result == "empty"

    def test_is_duplicate(self):
        """Test duplicate name detection"""
        from app.services.ux_improvements import NameValidator

        assert NameValidator.is_duplicate("John Doe", "john doe") is True
        assert NameValidator.is_duplicate("John Doe", "Jane Doe") is False
        assert NameValidator.is_duplicate("John Doe", "") is False

    def test_should_skip_confirmation_well_formatted(self):
        """Test skip confirmation for well-formatted names"""
        from app.services.ux_improvements import NameValidator

        # Well-formatted name with first and last name
        assert NameValidator.should_skip_confirmation("John Doe") is True
        assert NameValidator.should_skip_confirmation("María García López") is True

        # Single name - should not skip
        assert NameValidator.should_skip_confirmation("John") is False

        # All lowercase - should not skip
        assert NameValidator.should_skip_confirmation("john doe") is False


class TestTransitionLogger:
    """Tests for enhanced logging functionality"""

    def test_singleton_pattern(self):
        """Test that TransitionLogger is a singleton"""
        from app.services.ux_improvements import TransitionLogger

        logger1 = TransitionLogger()
        logger2 = TransitionLogger()

        assert logger1 is logger2

    def test_log_transition(self):
        """Test transition logging"""
        from app.services.ux_improvements import TransitionLogger

        logger = TransitionLogger()
        logger.log_transition(77777, "state1", "state2", "test_trigger", {"field": "value"})

        transitions = logger.get_user_transitions(77777, 1)
        assert len(transitions) >= 1
        assert transitions[-1]["from_state"] == "state1"
        assert transitions[-1]["to_state"] == "state2"

    def test_log_message_received(self):
        """Test message logging (should not raise)"""
        from app.services.ux_improvements import TransitionLogger

        logger = TransitionLogger()
        # Should not raise
        logger.log_message_received(77777, "test_state", "text", "Hello world")

    def test_log_callback_received(self):
        """Test callback logging (should not raise)"""
        from app.services.ux_improvements import TransitionLogger

        logger = TransitionLogger()
        # Should not raise
        logger.log_callback_received(77777, "test_state", "button_click")


class TestIntegration:
    """Integration tests for UX improvements"""

    def test_imports_work(self):
        """Test that all imports work correctly"""
        from app.services.ux_improvements import (
            ERROR_MESSAGES,
            FIELD_LABELS,
            PHASES,
            GlobalExceptionHandler,
            NameValidator,
            ProgressTracker,
            StallDetector,
            StartupValidator,
            TransitionLogger,
        )

        assert StartupValidator is not None
        assert GlobalExceptionHandler is not None
        assert StallDetector is not None
        assert ProgressTracker is not None
        assert TransitionLogger is not None
        assert NameValidator is not None
        assert len(PHASES) == 7
        assert "es" in FIELD_LABELS
        assert "en" in FIELD_LABELS
        assert "es" in ERROR_MESSAGES
        assert "en" in ERROR_MESSAGES

    def test_bot_imports_ux_module(self):
        """Test that telegram_bot imports UX module correctly"""
        from app.services.telegram_bot import (
            get_exception_handler,
            get_progress_tracker,
            get_stall_detector,
            get_transition_logger,
            global_error_handler,
        )

        assert get_exception_handler is not None
        assert get_stall_detector is not None
        assert get_progress_tracker is not None
        assert get_transition_logger is not None
        assert global_error_handler is not None

    def test_translations_have_ux_keys(self):
        """Test that translations include UX improvement keys"""
        from app.services.translations import get_text

        # Spanish
        assert get_text("generic_error", "es") is not None
        assert get_text("stall_reminder", "es") is not None
        assert get_text("restart_phase", "es") is not None
        assert get_text("progress_title", "es") is not None

        # English
        assert get_text("generic_error", "en") is not None
        assert get_text("stall_reminder", "en") is not None
        assert get_text("restart_phase", "en") is not None
        assert get_text("progress_title", "en") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
